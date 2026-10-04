"""One shot: live Codex limits -> three AWTRIX pushed apps -> verification."""

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from awtrix import Awtrix
from codex import freshness, read_usage


def payloads(snapshot, lifetime_ms):
    base = {"lifetimeMs": lifetime_ms, "lifetimeExpiry": "remove"}

    def usage_page(label, value):
        if value is None:
            return dict(base, text=label + " N/A")
        used = int(math.floor(value["used_percent"] + 0.5))
        return dict(base, text="%s %d%%" % (label, used), progress=used,
                    progressColor="#00AAFF", progressTrackColor="#202020")

    resets = snapshot.get("available_resets")
    return {"codex": usage_page("5H", snapshot["primary"]),
            "codex_week": usage_page("7D", snapshot.get("secondary")),
            "codex_resets": dict(base, text="RST " + ("N/A" if resets is None else str(resets)))}


def run():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    max_age = float(os.environ.get("CODEX_MAX_AGE_SECONDS", "3600"))
    if not math.isfinite(max_age) or max_age <= 0:
        raise ValueError("CODEX_MAX_AGE_SECONDS must be a positive finite number")
    ssh_host = os.environ.get("CODEX_SSH_HOST") or None
    # In SSH mode, Codex and CODEX_HOME belong to the Mac, never the Pi.
    snapshot = read_usage(ssh_host, os.environ.get("CODEX_HOME") or None)
    freshness(snapshot, max_age)
    client = Awtrix(os.environ.get("AWTRIX_HOST", "http://192.168.4.94"))
    _, before = client.list_apps()
    names = ("codex", "codex_week", "codex_resets")
    if any(app.get("name") in names and app.get("origin") not in (None, "pushed")
           for app in before):
        raise ValueError("AWTRIX has a non-pushed app with a Codex widget name; refusing to replace it")
    # Recheck after preflight and before each push to account for network delays.
    age, lifetime_ms = freshness(snapshot, max_age)
    for name, payload in payloads(snapshot, lifetime_ms).items():
        _, payload["lifetimeMs"] = freshness(snapshot, max_age)
        push_status = client.push_app(name, payload)
        print("Sent %s %s -> %s | PUT HTTP %d" %
              (name, json.dumps(payload), client.host, push_status), flush=True)
    get_status, apps = client.list_apps()
    for name in names:
        verified = any(app.get("name") == name and app.get("origin") == "pushed"
                       and all(app.get(key) is True for key in ("present", "enabled", "inLoop"))
                       for app in apps)
        if not verified:
            raise ValueError("Push acknowledged, but %s was not verified present, pushed, enabled and inLoop" % name)
    reset = datetime.fromtimestamp(snapshot["primary"]["resets_at"], timezone.utc).isoformat()
    source = "SSH " + ssh_host if ssh_host else "local"
    print("Verified codex, codex_week, codex_resets: present, pushed, enabled, inLoop"
          " | GET HTTP %d | %s account query %.0fs old | five-hour reset %s" %
          (get_status, source, age, reset))


if __name__ == "__main__":
    try:
        run()
    except (OSError, ValueError) as exc:
        print("deskmate: " + str(exc), file=sys.stderr)
        sys.exit(1)
