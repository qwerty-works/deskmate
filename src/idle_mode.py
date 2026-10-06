"""Scheduled AWTRIX idle mode for the Pixel Fireplace Berry app."""

import argparse
from datetime import datetime, time
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from awtrix import Awtrix

APP_NAME = "Pixel-Fireplace"
IDLE_APP_NAMES = {APP_NAME, "pixel-fireplace"}
DEFAULT_STATE = ".idle-mode-state.json"
DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_BRIGHTNESS = 10
SOURCE = Path(__file__).resolve().parents[1] / "packs" / "halloween" / "pixel-fireplace.be"


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


def load_state(path):
    try:
        return json.loads(path.read_text()) if path.exists() else None
    except (OSError, ValueError) as exc:
        raise ValueError("Idle state file is unreadable; remove it after checking the device state") from exc


def save_state(path, state):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(json.dumps(state) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def verify_app(apps):
    return any(app.get("name") == APP_NAME and app.get("origin") == "script"
               and all(app.get(key) is True for key in ("present", "enabled", "inLoop"))
               for app in apps)


def enter(client, state_path, brightness):
    _, apps = client.list_apps()
    existing = next((app for app in apps if app.get("name") == APP_NAME), None)
    if existing and existing.get("origin") != "script":
        raise ValueError("AWTRIX has a non-script pixel-fireplace app; refusing to replace it")
    _, settings = client.get_settings()
    state = load_state(state_path)
    if not state or not state.get("active"):
        save_state(state_path, {"active": True, "brightness": settings.get("brightness", 120),
                                "autoBrightness": settings.get("autoBrightness", False),
                                "order": [app["name"] for app in apps if app.get("inLoop") and app["name"] not in IDLE_APP_NAMES],
                                "disabled": [app["name"] for app in apps if not app.get("enabled") and app["name"] not in IDLE_APP_NAMES],
                                "activeApp": next((app["name"] for app in apps if app.get("present")), None)})
    # Preserve the original AWTRIX-installed fireplace when present. This lets
    # existing devices keep their procedural fire animation and avoids replacing
    # it with the bundled sample script.
    if not existing:
        client.install_script(APP_NAME, SOURCE.read_text())
    _, apps = client.list_apps()
    client.set_app_order([APP_NAME], [app["name"] for app in apps if app.get("name") != APP_NAME])
    client.patch_settings({"autoBrightness": False, "brightness": brightness})
    client.activate_app(APP_NAME)
    _, apps = client.list_apps()
    if not verify_app(apps):
        raise ValueError("Pixel Fireplace was not verified present, enabled and inLoop")


def exit_mode(client, state_path):
    state = load_state(state_path)
    _, apps = client.list_apps()
    if any(app.get("name") == APP_NAME and app.get("origin") != "script" for app in apps):
        raise ValueError("AWTRIX has a non-script pixel-fireplace app; refusing to remove it")
    order = [name for name in (state.get("order", []) if state else [app["name"] for app in apps if app.get("inLoop")]) if name not in IDLE_APP_NAMES]
    disabled = [name for name in (state.get("disabled", []) if state else [app["name"] for app in apps if not app.get("enabled")]) if name not in IDLE_APP_NAMES]
    client.set_app_order(order, disabled)
    if state and state.get("active"):
        client.patch_settings({"autoBrightness": bool(state.get("autoBrightness", False)),
                               "brightness": int(state.get("brightness", 120))})
        active_app = state.get("activeApp")
        if active_app and active_app in order:
            client.activate_app(active_app, fast=True)
    client.delete_app(APP_NAME)
    state_path.unlink(missing_ok=True)


def run(command):
    zone, brightness, state_path = config()
    client = Awtrix(os.environ.get("AWTRIX_HOST", "http://192.168.4.94"))
    now = datetime.now(zone)
    if command == "sync":
        command = "enter" if in_idle_window(now) else "exit"
    if command == "enter":
        enter(client, state_path, brightness)
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
