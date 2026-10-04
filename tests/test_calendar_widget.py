"""Calendar command safety at the Google and AWTRIX boundaries."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import calendar_widget

NOW = datetime(2026, 10, 4, 16, tzinfo=timezone.utc)
APP = {"name": "google_calendar", "origin": "pushed", "present": True,
       "enabled": True, "inLoop": True}
EVENT = {"summary": "Private Team sync", "start": {"dateTime": "2026-10-04T17:00:00Z"},
         "end": {"dateTime": "2026-10-04T18:00:00Z"}}


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.patches = [patch("calendar_widget.__file__", str(self.root / "src/calendar_widget.py")),
                        patch.dict(os.environ, {}, clear=True),
                        patch("calendar_widget.utcnow", return_value=NOW),
                        patch("calendar_widget.load_credentials"),
                        patch("calendar_widget.calendar_service"),
                        patch("calendar_widget.fetch_events", return_value=[EVENT]),
                        patch("calendar_widget.Awtrix")]
        values = []
        for patcher in self.patches:
            values.append(patcher.start())
            self.addCleanup(patcher.stop)
        self.clock, self.auth, self.service, self.fetch, self.factory = values[2:]
        self.client = self.factory.return_value
        self.client.list_apps.side_effect = [(200, []), (200, [APP])]
        self.client.push_app.return_value = 200

    def test_pushes_calendar_and_verifies_without_logging_title(self):
        with redirect_stdout(io.StringIO()) as output:
            calendar_widget.run()
        name, payload = self.client.push_app.call_args.args
        self.assertEqual(name, "google_calendar")
        self.assertEqual(payload["text"], "1:00 PM Private Team sync")
        self.assertEqual(payload["lifetimeMs"], 120000)
        self.assertNotIn("Private Team sync", output.getvalue())
        self.assertIn("Verified google_calendar", output.getvalue())
        self.client.delete_app.assert_not_called()
        self.service.return_value.close.assert_called_once()

    def test_shell_overrides_env_and_relative_paths_resolve_from_repo(self):
        (self.root / ".env").write_text("AWTRIX_HOST=http://file\n"
                                        "GOOGLE_CALENDAR_TOKEN_PATH=secrets/token.json\n"
                                        "GOOGLE_CALENDAR_TIMEZONE=America/Los_Angeles\n")
        os.environ["AWTRIX_HOST"] = "http://shell"
        with redirect_stdout(io.StringIO()):
            calendar_widget.run()
        self.factory.assert_called_once_with("http://shell")
        self.auth.assert_called_once_with(self.root / ".google-calendar/credentials.json",
                                          self.root / "secrets/token.json", authorize=False)
        self.assertEqual(self.client.push_app.call_args.args[1]["text"], "10:00 AM Private Team sync")

    def test_explicit_authorization_does_not_contact_clock_or_calendar_api(self):
        with redirect_stdout(io.StringIO()) as output:
            calendar_widget.run(authorize=True)
        self.assertTrue(self.auth.call_args.kwargs["authorize"])
        self.factory.assert_not_called()
        self.service.assert_not_called()
        self.assertNotIn("Private", output.getvalue())

    def test_auth_or_fetch_failure_never_contacts_clock(self):
        for boundary in (self.auth, self.fetch):
            with self.subTest(boundary=boundary):
                boundary.side_effect = ValueError("Calendar unavailable")
                with self.assertRaisesRegex(ValueError, "unavailable"):
                    calendar_widget.run()
                self.factory.assert_not_called()
                boundary.side_effect = None

    def test_refuses_non_pushed_name_for_both_push_and_removal(self):
        for events in ([EVENT], []):
            for origin in ("script", "native", None):
                with self.subTest(events=events, origin=origin):
                    self.fetch.return_value = events
                    self.client.list_apps.side_effect = None
                    self.client.list_apps.return_value = (200, [{"name": "google_calendar", "origin": origin}])
                    with self.assertRaisesRegex(ValueError, "refusing"):
                        calendar_widget.run()
                    self.client.push_app.assert_not_called()
                    self.client.delete_app.assert_not_called()

    def test_empty_calendar_deletes_only_its_pushed_page_and_verifies(self):
        self.fetch.return_value = []
        codex = {**APP, "name": "codex"}
        self.client.list_apps.side_effect = [(200, [APP, codex]), (200, [codex])]
        with redirect_stdout(io.StringIO()):
            calendar_widget.run()
        self.client.delete_app.assert_called_once_with("google_calendar")
        self.client.push_app.assert_not_called()

    def test_already_absent_calendar_is_noop(self):
        self.fetch.return_value = []
        self.client.list_apps.side_effect = [(200, [])]
        with redirect_stdout(io.StringIO()):
            calendar_widget.run()
        self.client.delete_app.assert_not_called()
        self.client.push_app.assert_not_called()

    def test_failed_removal_verification(self):
        self.fetch.return_value = []
        self.client.list_apps.side_effect = [(200, [APP]), (200, [APP])]
        with self.assertRaisesRegex(ValueError, "still present"):
            calendar_widget.run()

    def test_failed_push_verification(self):
        for verified in ([], [{**APP, "enabled": False}], [{**APP, "inLoop": False}],
                         [{**APP, "present": False}], [{**APP, "origin": "script"}]):
            with self.subTest(apps=verified):
                self.client.list_apps.side_effect = [(200, []), (200, verified)]
                with self.assertRaisesRegex(ValueError, "not verified"):
                    calendar_widget.run()

    def test_clock_error_does_not_expose_response_body_or_title(self):
        self.client.push_app.side_effect = ValueError("error with Private Team sync and token")
        with self.assertRaisesRegex(ValueError, "AWTRIX") as caught:
            calendar_widget.run()
        self.assertNotIn("Private", str(caught.exception))
        self.assertNotIn("token", str(caught.exception))

    def test_reselects_after_network_delay_at_event_end(self):
        self.clock.side_effect = [NOW, NOW + timedelta(hours=2)]
        self.client.list_apps.side_effect = [(200, [APP]), (200, [])]
        with redirect_stdout(io.StringIO()):
            calendar_widget.run()
        self.client.push_app.assert_not_called()
        self.client.delete_app.assert_called_once_with("google_calendar")

    def test_invalid_timezone_never_fetches_or_contacts_clock(self):
        os.environ["GOOGLE_CALENDAR_TIMEZONE"] = "Not/AZone"
        with self.assertRaisesRegex(ValueError, "TIMEZONE"):
            calendar_widget.run()
        self.auth.assert_not_called()
        self.factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
