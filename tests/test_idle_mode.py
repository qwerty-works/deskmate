import json
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from idle_mode import config, enter, exit_mode, in_idle_window


class IdleModeTests(unittest.TestCase):
    def test_window_crosses_midnight_and_boundaries(self):
        zone = ZoneInfo("America/New_York")
        self.assertFalse(in_idle_window(datetime(2026, 10, 5, 19, 59, tzinfo=zone)))
        self.assertTrue(in_idle_window(datetime(2026, 10, 5, 20, 0, tzinfo=zone)))
        self.assertTrue(in_idle_window(datetime(2026, 10, 6, 5, 59, tzinfo=zone)))
        self.assertFalse(in_idle_window(datetime(2026, 10, 6, 6, 0, tzinfo=zone)))

    def test_config_rejects_invalid_brightness(self):
        import os
        old = os.environ.get("IDLE_BRIGHTNESS")
        os.environ["IDLE_BRIGHTNESS"] = "256"
        try:
            with self.assertRaises(ValueError): config()
        finally:
            if old is None: os.environ.pop("IDLE_BRIGHTNESS", None)
            else: os.environ["IDLE_BRIGHTNESS"] = old

    def test_enter_saves_brightness_and_is_repeatable(self):
        client = Mock()
        original = {"name": "Pixel-Fireplace", "origin": "script", "enabled": True,
                    "inLoop": True, "present": True}
        client.list_apps.side_effect = [(200, [original]), (200, [original]), (200, [original])]
        client.get_settings.return_value = (200, {"brightness": 120, "autoBrightness": True})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            enter(client, path, 10)
            state = json.loads(path.read_text())
            self.assertEqual(state, {"active": True, "brightness": 120, "autoBrightness": True,
                                     "order": [], "disabled": [], "activeApp": "Pixel-Fireplace"})

    def test_exit_restores_and_disables_original_without_removing_it(self):
        client = Mock()
        client.list_apps.return_value = (200, [{"name": "Pixel-Fireplace", "origin": "script",
                                                "enabled": True, "inLoop": True, "present": True}])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            path.write_text(json.dumps({"active": True, "brightness": 120, "autoBrightness": True,
                                        "order": ["codex"], "disabled": [], "activeApp": "codex"}))
            exit_mode(client, path)
            client.set_app_order.assert_called_once_with(["codex"], ["Pixel-Fireplace"])
            client.patch_settings.assert_called_once_with({"autoBrightness": True, "brightness": 120})
            client.activate_app.assert_called_once_with("codex", fast=True)
            client.delete_app.assert_not_called()
            self.assertFalse(path.exists())
