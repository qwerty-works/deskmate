"""Focused checks for source selection and failures before touching the clock."""

from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from awtrix import Awtrix
from codex import account_limits, freshness, normalize_limits, read_local, read_usage
import main

NOW = 1791120000


def snapshot(age=10, used=34, reset=NOW + 500):
    return {"timestamp": datetime.fromtimestamp(NOW - age, timezone.utc).isoformat(),
            "primary": {"used_percent": used, "window_minutes": 300, "resets_at": reset},
            "secondary": {"used_percent": 53, "window_minutes": 10080, "resets_at": NOW + 8000}, "available_resets": 3}


def api_result(count=3):
    return {"rateLimits": {"limitId": "codex", "primary": {
        "usedPercent": 34, "windowDurationMins": 300, "resetsAt": NOW + 500},
        "secondary": {"usedPercent": 53, "windowDurationMins": 10080, "resetsAt": NOW + 8000}},
        "rateLimitResetCredits": {"availableCount": count, "credits": []}}


def fake_server(result):
    return """import sys,json
for line in sys.stdin:
    message=json.loads(line)
    if message.get('id') == 1:
        print(json.dumps({'id':1,'result':{}}),flush=True)
    elif message.get('id') == 2:
        print(json.dumps({'method':'account/rateLimits/updated','params':{}}),flush=True)
        print(json.dumps({'id':2,'result':RESULT}),flush=True)
""".replace("RESULT", repr(result))


class CodexTests(unittest.TestCase):
    def test_live_protocol_with_real_child_process(self):
        result = api_result()
        self.assertEqual(account_limits([sys.executable, "-u", "-c", fake_server(result)]), result)

    def test_protocol_errors_eof_and_timeout(self):
        scripts = ["import sys;sys.exit(1)",
                   "import time;time.sleep(10)",
                   "import sys;sys.stdin.readline();print('not JSON',flush=True)",
                   "import sys,json;sys.stdin.readline();print(json.dumps({'id':1,'error':'unauthenticated'}),flush=True)"]
        for script in scripts:
            with self.subTest(script=script), self.assertRaises(ValueError):
                account_limits([sys.executable, "-u", "-c", script], timeout=0.2)

    def test_normalize_and_authoritative_reset_count(self):
        data = normalize_limits(api_result())
        self.assertEqual(data["primary"], snapshot()["primary"])
        self.assertEqual(data["secondary"], snapshot()["secondary"])
        # Count is authoritative, even when the credit detail list is empty.
        self.assertEqual(data["available_resets"], 3)

    def test_specific_codex_bucket_wins(self):
        result = api_result()
        bucket = result["rateLimits"].copy()
        result["rateLimits"] = {"limitId": "other"}
        result["rateLimitsByLimitId"] = {"codex": bucket}
        self.assertEqual(normalize_limits(result)["primary"]["used_percent"], 34)
        result["rateLimitsByLimitId"] = {"other": bucket}
        with self.assertRaises(ValueError):
            normalize_limits(result)

    def test_zero_and_unknown_resets_are_distinct(self):
        for count in (0, None):
            self.assertEqual(normalize_limits(api_result(count))["available_resets"], count)
        data = api_result()
        data["rateLimitResetCredits"] = None
        self.assertIsNone(normalize_limits(data)["available_resets"])
        for count in (-1, True, "3", 3.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                normalize_limits(api_result(count))

    def test_invalid_percentages(self):
        for value in (-1, 101, True, "34", float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                freshness(snapshot(used=value), 3600, NOW)

    def test_lifetime_is_remaining_age_allowance(self):
        self.assertEqual(freshness(snapshot(age=20, reset=NOW + 9000), 100, NOW), (20, 80000))

    def test_lifetime_is_capped_by_each_reset(self):
        self.assertEqual(freshness(snapshot(), 3600, NOW), (10, 500000))
        data = snapshot()
        data["secondary"]["resets_at"] = NOW + 20
        self.assertEqual(freshness(data, 3600, NOW), (10, 20000))

    def test_stale_expired_future_and_invalid_max_age(self):
        cases = [(snapshot(age=3600), 3600), (snapshot(reset=NOW), 3600),
                 (snapshot(age=-1), 3600), (snapshot(), 0), (snapshot(), float("nan"))]
        for data, age in cases:
            with self.subTest(data=data, age=age), self.assertRaises(ValueError):
                freshness(data, age, NOW)
        data = snapshot()
        data["secondary"]["window_minutes"] = 7200
        with self.assertRaisesRegex(ValueError, "seven days"):
            freshness(data, 3600, NOW)

    def test_missing_cli(self):
        with patch("codex.shutil.which", return_value=None), \
                patch("codex.Path.is_file", return_value=False), self.assertRaisesRegex(ValueError, "CLI not found"):
            read_local()

    def test_standard_library_reader_runs_from_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "codex"
            binary.write_text("#!" + sys.executable + "\n" + fake_server(api_result()))
            binary.chmod(0o755)
            real_run = subprocess.run

            def run_remote(command, **kwargs):
                self.assertEqual(command[-1], "python3 - --read-local --home '/a path/codex'")
                self.assertIn("BatchMode=yes", command)
                return real_run([sys.executable, "-", "--read-local", "--home", "/a path/codex"], **kwargs)

            with patch.dict(os.environ, {"PATH": directory}), patch("codex.subprocess.run", side_effect=run_remote):
                data = read_usage("user@mac", "/a path/codex")
                self.assertEqual(data["primary"], snapshot()["primary"])
                self.assertEqual(data["available_resets"], 3)

    def test_ssh_failures(self):
        failures = [subprocess.TimeoutExpired("ssh", 30),
                    Mock(returncode=255, stderr="Permission denied", stdout=""),
                    Mock(returncode=0, stderr="", stdout="not JSON")]
        for failure in failures:
            kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
            with self.subTest(failure=failure), patch("codex.subprocess.run", **kwargs), self.assertRaises(ValueError):
                read_usage("user@mac")


class AwtrixTests(unittest.TestCase):
    def response(self, client, body, status=200):
        response = io.BytesIO(json.dumps(body).encode())
        response.status = status
        client.http.open = Mock(return_value=response)

    def test_push_protocol_and_acknowledgement(self):
        client = Awtrix("http://clock/")
        self.response(client, {"ok": True})
        self.assertEqual(client.push_app("codex", {"text": "CODEX 34%"}), 200)
        request = client.http.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://clock/api/v1/apps/pushed/codex")
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), {"text": "CODEX 34%"})
        self.response(client, {"ok": False})
        with self.assertRaisesRegex(ValueError, "acknowledge"):
            client.push_app("codex", {"text": "CODEX 34%"})

    def test_http_and_connection_failures(self):
        client = Awtrix("http://clock")
        failures = [HTTPError("http://clock", 422, "Invalid", {}, io.BytesIO(b'bad payload')),
                    URLError("unreachable"), TimeoutError("timed out")]
        for failure in failures:
            with self.subTest(failure=failure):
                client.http.open = Mock(side_effect=failure)
                with self.assertRaises(ValueError):
                    client.push_app("codex", {"text": "x"})

    def test_invalid_response_shapes(self):
        client = Awtrix("http://clock")
        self.response(client, {"ok": True})
        with self.assertRaisesRegex(ValueError, "app list"):
            client.list_apps()
        response = io.BytesIO(b"<html>setup</html>")
        response.status = 200
        client.http.open = Mock(return_value=response)
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            client.list_apps()


class CommandTests(unittest.TestCase):
    def test_unknown_values_are_not_zero(self):
        data = snapshot()
        data["secondary"] = None
        data["available_resets"] = None
        pages = main.payloads(data, 1000)
        self.assertEqual(pages["codex_week"]["text"], "7D N/A")
        self.assertNotIn("progress", pages["codex_week"])
        self.assertEqual(pages["codex_resets"]["text"], "RST N/A")
        self.assertNotIn("progress", pages["codex_resets"])

    def test_bar_endpoints_and_zero_resets(self):
        data = snapshot(used=0)
        data["secondary"]["used_percent"] = 100
        data["available_resets"] = 0
        pages = main.payloads(data, 1000)
        self.assertEqual(pages["codex"]["progress"], 0)
        self.assertEqual(pages["codex_week"]["progress"], 100)
        self.assertEqual(pages["codex_resets"]["text"], "RST 0")
        self.assertTrue(all(page["lifetimeMs"] == 1000 for page in pages.values()))


    def test_success_and_shell_configuration_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("AWTRIX_HOST=http://from-file\nCODEX_MAX_AGE_SECONDS=100\n")
            with patch("main.__file__", str(root / "src/main.py")), \
                    patch.dict(os.environ, {"AWTRIX_HOST": "http://from-shell"}, clear=True), \
                    patch("main.read_usage", return_value=snapshot(used=34.5)) as reader, \
                    patch("codex.time.time", return_value=NOW), patch("main.Awtrix") as factory, \
                    redirect_stdout(io.StringIO()) as output:
                client = factory.return_value
                client.host = "http://from-shell"
                app = {"name": "codex", "origin": "pushed", "present": True,
                       "enabled": True, "inLoop": True}
                apps = [dict(app, name=name) for name in ("codex", "codex_week", "codex_resets")]
                client.list_apps.side_effect = [(200, []), (200, apps)]
                client.push_app.return_value = 200
                main.run()
                factory.assert_called_once_with("http://from-shell")
                reader.assert_called_once_with(None, None)
                self.assertEqual(client.push_app.call_count, 3)
                calls = client.push_app.call_args_list
                self.assertEqual(calls[0].args, ("codex", {
                    "text": "5H 35%", "progress": 35, "progressColor": "#00AAFF",
                    "progressTrackColor": "#202020", "lifetimeMs": 90000, "lifetimeExpiry": "remove"}))
                self.assertEqual(calls[1].args[1]["text"], "7D 53%")
                self.assertEqual(calls[1].args[1]["progress"], 53)
                self.assertEqual(calls[2].args[1]["text"], "RST 3")
                self.assertNotIn("progress", calls[2].args[1])
                self.assertIn("Verified codex", output.getvalue())

    def test_stale_source_never_contacts_awtrix(self):
        with patch("main.load_dotenv"), patch.dict(os.environ, {}, clear=True), \
                patch("main.read_usage", return_value=snapshot(age=4000)), \
                patch("codex.time.time", return_value=NOW), patch("main.Awtrix") as client:
            with self.assertRaisesRegex(ValueError, "stale"):
                main.run()
            client.assert_not_called()

    def test_missing_or_disabled_app_fails_verification(self):
        for after in ([], [{"name": "codex", "origin": "pushed", "present": True,
                          "enabled": False, "inLoop": False}]):
            with patch("main.load_dotenv"), patch.dict(os.environ, {}, clear=True), \
                    patch("main.read_usage", return_value=snapshot()), \
                    patch("codex.time.time", return_value=NOW), patch("main.Awtrix") as factory, \
                    redirect_stdout(io.StringIO()):
                client = factory.return_value
                client.list_apps.side_effect = [(200, []), (200, after)]
                client.push_app.return_value = 200
                with self.assertRaisesRegex(ValueError, "not verified"):
                    main.run()

    def test_existing_script_is_not_overwritten(self):
        with patch("main.load_dotenv"), patch.dict(os.environ, {}, clear=True), \
                patch("main.read_usage", return_value=snapshot()), \
                patch("codex.time.time", return_value=NOW), patch("main.Awtrix") as factory:
            client = factory.return_value
            client.list_apps.return_value = (200, [{"name": "codex_week", "origin": "script"}])
            with self.assertRaisesRegex(ValueError, "refusing"):
                main.run()
            client.push_app.assert_not_called()


if __name__ == "__main__":
    unittest.main()
