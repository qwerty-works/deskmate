"""Query official Codex account limits; also runs standalone over SSH."""

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import shutil
import subprocess
import sys
import time


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Codex snapshot timestamp has no timezone")
    return parsed.timestamp()


def window(value):
    if not isinstance(value, dict):
        raise ValueError("Missing Codex usage window")
    result = {}
    for key in ("used_percent", "window_minutes", "resets_at"):
        number = value.get(key)
        if (isinstance(number, bool) or not isinstance(number, (int, float))
                or not math.isfinite(number)):
            raise ValueError("Invalid Codex " + key)
        result[key] = number
    if not 0 <= result["used_percent"] <= 100:
        raise ValueError("Codex percentage must be between 0 and 100")
    if result["window_minutes"] <= 0 or result["resets_at"] <= 0:
        raise ValueError("Invalid Codex window or reset time")
    return result


def account_limits(command, env=None, timeout=20):
    """One bounded JSONL RPC connection, with no model turn or reset consumption."""
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=env)
    pending = b""
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)

            def send(message):
                process.stdin.write((json.dumps(message) + "\n").encode())
                process.stdin.flush()

            def receive(request_id):
                nonlocal pending
                while True:
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        message = json.loads(line)
                        if not isinstance(message, dict):
                            raise ValueError("Codex returned an invalid RPC message")
                        if message.get("id") == request_id:
                            if "error" in message:
                                raise ValueError("Codex API error: " + str(message["error"]))
                            if not isinstance(message.get("result"), dict):
                                raise ValueError("Codex returned an invalid RPC result")
                            return message["result"]
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise ValueError("Codex account query timed out")
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError("Codex app-server closed before answering; check codex login status")
                    pending += chunk

            send({"method": "initialize", "id": 1, "params": {
                "clientInfo": {"name": "deskmate", "version": "0.2"},
                "capabilities": {"experimentalApi": True}}})
            receive(1)
            send({"method": "initialized", "params": {}})
            send({"method": "account/rateLimits/read", "id": 2})
            return receive(2)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()


def normalize_limits(result):
    buckets = result.get("rateLimitsByLimitId")
    limits = buckets.get("codex") if isinstance(buckets, dict) else result.get("rateLimits")
    if not isinstance(limits, dict) or limits.get("limitId") != "codex":
        raise ValueError("Codex API returned no codex account limits")

    def convert(value):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("Codex API returned an invalid usage window")
        return window({"used_percent": value.get("usedPercent"),
                       "window_minutes": value.get("windowDurationMins"),
                       "resets_at": value.get("resetsAt")})

    credits = result.get("rateLimitResetCredits")
    count = credits.get("availableCount") if isinstance(credits, dict) else None
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("Invalid available reset count")
    snapshot = {"timestamp": datetime.now(timezone.utc).isoformat(),
                "primary": convert(limits.get("primary")),
                "secondary": convert(limits.get("secondary")), "available_resets": count}
    return snapshot


def read_local(home=None):
    binary = shutil.which("codex")
    if not binary:
        candidate = Path.home() / ".local/bin/codex"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            binary = str(candidate)
    if not binary:
        raise ValueError("Codex CLI not found; install it on the machine being queried")
    env = os.environ.copy()
    if home:
        env["CODEX_HOME"] = str(Path(home).expanduser())
    return normalize_limits(account_limits([binary, "app-server", "--stdio"], env))


def read_usage(ssh_host=None, home=None):
    if not ssh_host:
        return read_local(home)
    if ssh_host.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_.@:-]+", ssh_host):
        raise ValueError("CODEX_SSH_HOST must be a hostname or user@hostname")
    remote = ["python3", "-", "--read-local"]
    if home:
        remote.extend(["--home", home])
    command = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
               ssh_host, shlex.join(remote)]
    try:
        result = subprocess.run(command, input=Path(__file__).read_text(),
                                text=True, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Codex SSH read timed out after 30 seconds") from exc
    if result.returncode:
        raise ValueError("Codex SSH read failed: " + result.stderr.strip()[:300])
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("Codex SSH reader returned invalid JSON") from exc


def freshness(snapshot, max_age, now=None):
    """Validate local/remote data and return age and safe display lifetime."""
    now = time.time() if now is None else now
    if not math.isfinite(max_age) or max_age <= 0:
        raise ValueError("CODEX_MAX_AGE_SECONDS must be a positive finite number")
    if not isinstance(snapshot, dict):
        raise ValueError("Invalid Codex snapshot")
    primary = window(snapshot.get("primary"))
    if primary["window_minutes"] != 300:
        raise ValueError("Codex primary window is not five hours")
    secondary = snapshot.get("secondary")
    if secondary is not None:
        secondary = window(secondary)
        if secondary["window_minutes"] != 10080:
            raise ValueError("Codex secondary window is not seven days")
    count = snapshot.get("available_resets")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("Invalid available reset count")
    try:
        age = now - timestamp(snapshot["timestamp"])
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Invalid Codex snapshot timestamp") from exc
    if age < 0:
        raise ValueError("Codex snapshot is in the future; check the Mac and Pi clocks")
    if age >= max_age:
        raise ValueError("Codex snapshot is stale (%.0fs old; maximum %.0fs)" % (age, max_age))
    remaining = min(max_age - age, primary["resets_at"] - now)
    if secondary is not None:
        remaining = min(remaining, secondary["resets_at"] - now)
    if remaining <= 0:
        raise ValueError("Codex usage window has expired; rerun to query fresh account limits")
    lifetime_ms = int(remaining * 1000)
    if lifetime_ms < 1:
        raise ValueError("Codex snapshot expires too soon to display")
    return age, lifetime_ms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-local", action="store_true", required=True)
    parser.add_argument("--home", help="Codex home on this machine")
    args = parser.parse_args()
    try:
        print(json.dumps(read_local(args.home), allow_nan=False))
    except (OSError, ValueError) as exc:
        print("Codex: " + str(exc), file=sys.stderr)
        sys.exit(1)
