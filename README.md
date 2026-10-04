# Desk Mate

One command queries real Codex account usage and sends three pushed apps to the
TC001. AWTRIX owns rendering, scrolling, and app rotation:

| App | Example text | Bar |
| --- | --- | --- |
| `codex` | `5H 51%` | Five-hour percentage used |
| `codex_week` | `7D 55%` | Seven-day percentage used |
| `codex_resets` | `RST 3` | Count only: Codex provides no maximum |

## Setup and run (macOS or Raspberry Pi)

Requires Python **3.9+**. From the project directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

The only package dependency is `python-dotenv`; HTTP, parsing, and SSH orchestration
use the Python standard library. On Raspberry Pi OS, install `python3-venv` with
`sudo apt install python3-venv` if virtual-environment creation requires it.

The machine being queried needs a current Codex CLI with `app-server --stdio`
support, an existing ChatGPT-backed Codex login, and internet access. Check
`codex login status`. API-key-only authentication does not provide these account
limits. In Pi-over-SSH mode, these requirements apply to the Mac, not the Pi.

## Configuration

Edit `.env`. Existing shell environment variables take precedence. The file is
loaded relative to the project, even when you run the script from another directory.

| Variable | Default | Purpose |
| --- | --- | --- |
| `AWTRIX_HOST` | `http://192.168.4.94` | AWTRIX NG base URL |
| `CODEX_MAX_AGE_SECONDS` | `3600` | Maximum age of returned metrics and display lifetime, in seconds |
| `CODEX_SSH_HOST` | empty | Query locally, or use `user@mac` / an SSH config alias |
| `CODEX_HOME` | `~/.codex` | Codex data directory; in SSH mode this is on the Mac |

Leave `CODEX_HOME` blank for the normal location. The reader also honors the remote
Mac's existing `CODEX_HOME` environment variable when no explicit path is supplied.
Use an absolute path if your Mac stores Codex data elsewhere.

### Running on the Pi using your Mac's data

The Pi needs LAN access to AWTRIX and SSH key access to the Mac. Enable **Remote
Login** on macOS, establish SSH key authentication, and verify the Mac's host key
interactively before running the widget. On the Pi:

```sh
ssh your-user@your-mac.local 'python3 --version'
ssh -o BatchMode=yes your-user@your-mac.local 'python3 --version'
```

Set `CODEX_SSH_HOST=your-user@your-mac.local` in the Pi's `.env`, then run
`python src/main.py` there. The Mac needs Python 3.9+ and an authenticated Codex CLI;
it does not need Desk Mate or `python-dotenv` installed for SSH reads. The Pi sends
the same reader code through SSH stdin to `python3 -`; only selected usage JSON
comes back. SSH connects within five seconds and the entire read has a 30-second
timeout. It never asks for passwords or copies credentials/transcripts. The Mac
must be awake and reachable. The reader searches `PATH`, then `~/.local/bin/codex`;
make Codex available there in the Mac's noninteractive SSH environment.
No Pi deployment has been verified yet.

## Where usage comes from

Each run starts a short-lived `codex app-server --stdio` subprocess, initializes
its documented JSONL protocol, and calls `account/rateLimits/read`. The server
uses the existing Codex login on that machine; Desk Mate never reads or copies
the credential files. No model turn is started, and no reset is consumed.

The official [Codex app-server API](https://learn.chatgpt.com/docs/app-server)
provides percentage **used**, window length, reset timestamps, and
`rateLimitResetCredits.availableCount`. The count is authoritative; the credit
detail list may be incomplete. A missing reset count is displayed as `RST N/A`,
never zero. A missing weekly window is displayed as `7D N/A`, with no bar.

Your account reports a **seven-day** secondary window, not five days. The reader
checks the window lengths rather than relabeling a different window as weekly.
`5H 51%` means 51% of the five-hour allowance used, not 51% remaining. Text and
bars use the same rounded value (halves rounded up). Resets are an available count;
there is no total from which to compute a meaningful percentage.

V1 used local session snapshots, which omitted reset credits. This version uses
the official live query for all three metrics, with no session-file fallback.
The subprocess has a 20-second total query timeout and is stopped afterward.
The CLI/app-server interface is experimental and requires a compatible Codex
version. Authentication, connection, malformed data, and timeout failures exit
nonzero before any push. Future-dated, expired, or stale metrics are also rejected.

## AWTRIX behavior and verification

The client follows the official AWTRIX NG
[HTTP API](https://ang.blueforcer.de/reference/http/) and
[payload reference](https://ang.blueforcer.de/reference/payload/).
Each page uses `PUT /api/v1/apps/pushed/{name}`. For example:

```json
{"text":"5H 51%","progress":51,"progressColor":"#00AAFF","progressTrackColor":"#202020","lifetimeMs":3600000,"lifetimeExpiry":"remove"}
```

AWTRIX draws its native progress bar along the bottom row: blue filled portion,
dark empty track. Separate pushed apps let AWTRIX rotate each value with its own
bar, without custom rendering. The existing `codex` app becomes the five-hour
page; `codex_week` and `codex_resets` are added. Other apps and rotation settings
are preserved.

Lifetimes are computed before each push: the smaller of the remaining age
allowance and time until either known usage window resets. Rerunning updates the
same three apps. A preflight refuses to replace scripts with any of those names.
Each push requires a successful HTTP status and `{"ok":true}`; afterward
`GET /api/v1/apps` must confirm all three are present, pushed, enabled, and in the
loop. Pushes are sequential: an error can leave earlier pages updated. The console
prints each acknowledged push and exits nonzero on failure. Disabled pages must
be enabled using AWTRIX's own controls.

Values update only when rerun. Pages disappear when their lifetimes run out or
AWTRIX reboots; rerun to recreate them. There is no scheduler, persistent daemon,
database, Docker, UI, Berry application, or firmware modification.

On the **physical TC001**, confirm both percentage texts are readable, blue bars
match their values without covering the text, and `RST 3` rotates normally
alongside your existing apps. Text scrolls using AWTRIX defaults if needed.
HTTP acceptance and app-list verification do not prove physical appearance.

## Tests and manual updates

```sh
source .venv/bin/activate
python -m unittest discover -s tests -v
```

After changing code, rerun the tests and `python src/main.py`. For another checkout
on the Pi, commit/push the intended changes from your development machine, then:

```sh
cd /path/to/deskmate
git pull --ff-only
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
```

Keep each machine's `.env` local. There is no background service to restart.
