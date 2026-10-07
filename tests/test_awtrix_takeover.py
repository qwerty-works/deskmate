import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from awtrix_takeover import claim, release, save, snapshot

FIREPLACE = {"name": "Pixel-Fireplace", "origin": "script", "enabled": True,
             "inLoop": True, "present": True}
WAVE = {"name": "deskmate-wave", "origin": "script", "enabled": True,
        "inLoop": True, "present": True}
CODEX = {"name": "codex", "origin": "pushed", "present": True,
         "enabled": True, "inLoop": True}


class TakeoverTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.client = Mock()

    def test_snapshot_excludes_owned_names_and_records_display_state(self):
        apps = [FIREPLACE, CODEX, {"name": "Battery", "present": True, "enabled": False, "inLoop": False}]
        state = snapshot(apps, {"brightness": 120, "autoBrightness": True}, {"Pixel-Fireplace", "pixel-fireplace"})
        self.assertEqual(state, {"active": True, "brightness": 120, "autoBrightness": True,
                                 "order": ["codex"], "disabled": ["Battery"], "activeApp": "Pixel-Fireplace"})

    def test_claim_reuses_the_first_snapshot_across_repeated_runs(self):
        self.client.list_apps.side_effect = [(200, [FIREPLACE, CODEX]), (200, [WAVE])]
        self.client.get_settings.return_value = (200, {"brightness": 120, "autoBrightness": True})
        first = claim(self.client, self.path, "deskmate-wave", {"deskmate-wave"}, 120, None)
        self.client.get_settings.return_value = (200, {"brightness": 120, "autoBrightness": False})
        second = claim(self.client, self.path, "deskmate-wave", {"deskmate-wave"}, 120, None)
        self.assertEqual(first, second)
        # The wave owns only itself, so the fireplace stays in the restored loop.
        self.assertEqual(json.loads(self.path.read_text())["order"], ["Pixel-Fireplace", "codex"])
        self.assertEqual(json.loads(self.path.read_text())["autoBrightness"], True)

    def test_claim_defers_when_another_controller_is_active(self):
        other = Path(self.directory.name) / "idle.json"
        save(other, {"active": True, "brightness": 10, "autoBrightness": False,
                     "order": [], "disabled": [], "activeApp": "Pixel-Fireplace"})
        self.assertIsNone(claim(self.client, self.path, "deskmate-wave", {"deskmate-wave"}, 120, other))
        self.assertFalse(self.path.exists())
        self.client.set_app_order.assert_not_called()

    def test_claim_refuses_a_non_script_owner(self):
        self.client.list_apps.return_value = (200, [{"name": "deskmate-wave", "origin": "pushed", "present": True}])
        with self.assertRaises(ValueError):
            claim(self.client, self.path, "deskmate-wave", {"deskmate-wave"}, 120, None)
        self.assertFalse(self.path.exists())

    def test_release_restores_order_brightness_and_disables_the_owner(self):
        self.client.list_apps.return_value = (200, [WAVE, CODEX])
        save(self.path, {"active": True, "brightness": 10, "autoBrightness": False,
                         "order": ["Pixel-Fireplace"], "disabled": ["Battery"],
                         "activeApp": "Pixel-Fireplace"})
        release(self.client, self.path, "deskmate-wave", {"deskmate-wave"})
        self.client.set_app_order.assert_called_once_with(["Pixel-Fireplace"], ["Battery", "deskmate-wave"])
        self.client.patch_settings.assert_called_once_with({"autoBrightness": False, "brightness": 10})
        self.client.activate_app.assert_called_once_with("Pixel-Fireplace", fast=True)
        self.assertFalse(self.path.exists())

    def test_release_keeps_the_owner_script_installed(self):
        self.client.list_apps.return_value = (200, [WAVE, CODEX])
        save(self.path, {"active": True, "brightness": 120, "autoBrightness": False,
                         "order": ["google_calendar"], "disabled": [], "activeApp": "codex"})
        release(self.client, self.path, "deskmate-wave", {"deskmate-wave"})
        self.client.delete_app.assert_not_called()

    def test_release_is_idempotent_without_a_state_file(self):
        self.client.list_apps.return_value = (200, [CODEX])
        release(self.client, self.path, "deskmate-wave", {"deskmate-wave"})
        self.assertFalse(self.path.exists())
        self.assertEqual(self.client.patch_settings.call_count, 0)

    def test_unreadable_state_fails_loudly(self):
        self.path.write_text("{not json")
        with self.assertRaises(ValueError):
            release(self.client, self.path, "deskmate-wave", {"deskmate-wave"})