"""Small AWTRIX NG HTTP client for pushed apps."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener


class Awtrix:
    def __init__(self, host, timeout=5):
        host = host.rstrip("/")
        url = urlsplit(host)
        if url.scheme not in ("http", "https") or not url.netloc or url.query or url.fragment:
            raise ValueError("AWTRIX_HOST must be an http:// or https:// base URL")
        self.host = host
        self.timeout = timeout
        # Connect directly to the clock, independent of shell HTTP proxy settings.
        self.http = build_opener(ProxyHandler({}))

    def _request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode()
        request = Request(self.host + path, data=data, method=method,
                          headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self.http.open(request, timeout=self.timeout) as response:
                status = response.status
                body = json.load(response)
        except HTTPError as exc:
            detail = exc.read(500).decode(errors="replace")
            raise ValueError("AWTRIX HTTP %s: %s" % (exc.code, detail)) from exc
        except (URLError, OSError) as exc:
            raise ValueError("AWTRIX connection failed: " + str(exc)) from exc
        except ValueError as exc:
            raise ValueError("AWTRIX returned invalid JSON") from exc
        if not 200 <= status < 300:
            raise ValueError("AWTRIX HTTP " + str(status))
        return status, body

    def push_app(self, name, payload):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
            raise ValueError("Invalid AWTRIX app name")
        status, body = self._request("PUT", "/api/v1/apps/pushed/" + name, payload)
        if not isinstance(body, dict) or body.get("ok") is not True:
            raise ValueError("AWTRIX did not acknowledge the push: " + repr(body))
        return status

    def list_apps(self):
        status, body = self._request("GET", "/api/v1/apps")
        if not isinstance(body, list) or not all(isinstance(app, dict) for app in body):
            raise ValueError("AWTRIX returned an invalid app list")
        return status, body
