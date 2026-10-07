"""Scheduled AWTRIX idle mode for the Pixel Fireplace Berry app."""

import argparse
from datetime import datetime, time
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from awtrix import Awtrix
from awtrix_takeover import claim, guarded, release

APP_NAME = "Pixel-Fireplace"
IDLE_APP_NAMES = {APP_NAME, "pixel-fireplace"}
DEFAULT_STATE = ".idle-mode-state.json"
DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_BRIGHTNESS = 10
DEFAULT_MEETING_STATE = ".meeting-mode-state.json"


def in_idle_window(now):
    local = now
    current = local.timetz().replace(tzinfo=None)
    return current >= time(20, 0) or current < time(6, 0)


def config():
    try:
        zone = ZoneInfo(os.environ.get("IDLE_TIMEZONE", DEFAULT_TIMEZONE))
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("IDLE_TIMEZONE must be an IANA timezone such as America/New_York") from exc
    try:
        brightness = int(os.environ.get("IDLE_BRIGHTNESS", str(DEFAULT_BRIGHTNESS)))
    except ValueError as exc:
        raise ValueError("IDLE_BRIGHTNESS must be an integer from 0 to 255") from exc
    if not 0 <= brightness <= 255:
        raise ValueError("IDLE_BRIGHTNESS must be an integer from 0 to 255")
    state = Path(os.environ.get("IDLE_STATE_PATH", DEFAULT_STATE)).expanduser()
    if not state.is_absolute():
        state = Path(__file__).resolve().parents[1] / state
    return zone, brightness, state


def meeting_state_path():
    path = Path(os.environ.get("MEETING_STATE_PATH", DEFAULT_MEETING_STATE)).expanduser()
    return path if path.is_absolute() else Path(__file__).resolve().parents[1] / path


def verify_app(apps):
    return any(app.get("name") == APP_NAME and app.get("origin") == "script"
               and all(app.get(key) is True for key in ("present", "enabled", "inLoop"))
               for app in apps)


def enter(client, state_path, brightness):
    # Idle mode drives the user's own script; it never substitutes a bundled animation.
    _, apps = client.list_apps()
    if not any(app.get("name") == APP_NAME and app.get("origin") == "script" for app in apps):
        raise ValueError("Original Pixel-Fireplace script is not installed on AWTRIX")
    state = claim(client, state_path, APP_NAME, IDLE_APP_NAMES, brightness,
                  meeting_state_path(), call=guarded)
    if state is None:
        return False
    _, apps = client.list_apps()
    if not verify_app(apps):
        raise ValueError("Pixel Fireplace was not verified present, enabled and inLoop")
    return True


def exit_mode(client, state_path):
    release(client, state_path, APP_NAME, IDLE_APP_NAMES, call=guarded)


def run(command):
    zone, brightness, state_path = config()
    client = Awtrix(os.environ.get("AWTRIX_HOST", "http://192.168.4.94"))
    now = datetime.now(zone)
    if command == "sync":
        command = "enter" if in_idle_window(now) else "exit"
    if command == "enter":
        if not enter(client, state_path, brightness):
            print("Pixel Fireplace idle mode deferred: a meeting animation is active", flush=True)
            return
        print("Verified Pixel Fireplace idle mode", flush=True)
    else:
        exit_mode(client, state_path)
        print("Verified normal AWTRIX mode restored", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("enter", "exit", "sync"))
    args = parser.parse_args()
    try:
        run(args.command)
    except (OSError, ValueError) as exc:
        print("deskmate idle mode: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
