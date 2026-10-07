# Google Calendar on your desk display

The Pi reads your primary Google Calendar independently of your Mac. AWTRIX
rotates a separate `google_calendar` page alongside Codex and your other apps:

Each push shows one scrolling agenda line: the `calendardots` icon on the left,
then up to three events joined with `" | "`.

| Calendar state | Scrolling display |
| --- | --- |
| One timed event today | `1:00 PM Team sync` |
| Several events today | `1:00 PM One on one \| 3:00 PM Retro` |
| Next timed event tomorrow | `Tomorrow 9:00 AM Team sync` |
| Timed event underway | Great Wave animation, exclusive |
| No eligible events within the next 24 hours | Calendar page removed |

The underway marker appears once, even when meetings overlap, and carries no
title. All-day, cancelled, and self-declined events are skipped. Recurring
events are expanded into individual occurrences. Ongoing events come first,
then the earliest upcoming events. Start time is inclusive and end time is
exclusive. Blank titles become `Untitled event`. The calendar is read-only; the
integration never creates or changes events. If the spring DST change brings an
event two local dates ahead into the 24-hour window, its month and day are shown
instead of the word `Tomorrow`.

## The calendar icon

The payload sets `icon: "calendardots"`, which AWTRIX resolves **by name** from
the clock's `/ICONS` directory (`/ICONS/calendardots.gif`). No GIF is vendored
in this repository, so installing the icon on a device is a prerequisite you
manage on that device. If `/ICONS` is ever cleared, AWTRIX silently falls back
to the icon-less layout and the agenda still scrolls. That silent fallback is a
deliberate, accepted tradeoff of referencing the icon by name instead of
inlining an asset; it is documented behavior, not an error.

## The meeting wave

While a timed event is underway, the display shows the **Great Wave** animation
from `packs/transitions` and nothing else. The text page is not pushed for the
duration of the meeting; it returns on the first run after the event ends.

This replaces the agenda's `meeting in progress` line, which was the earlier
behavior for an underway meeting. `event_payload` still builds that marker and
still has its own unit tests, but the widget no longer pushes a page while a
meeting is running, so the marker is not reachable through the display.

A few details worth knowing:

- The app is named `deskmate-wave`, because AWTRIX app names accept only letters,
  digits, `_`, and `-`. The `Great Wave` display name still comes from the
  script's `@name` header.
- The script stays installed on the clock and is merely switched out of the
  rotation between meetings, so the next meeting does not reinstall it.
- The wave is **poll-driven**. The once-a-minute calendar run decides whether it
  holds the display, so it can outlive a meeting by up to one minute.
- A meeting outranks overnight idle mode. If a meeting overlaps the fireplace
  window, the wave takes the display and the dimmed fireplace resumes afterward.
- `MEETING_BRIGHTNESS` sets the display brightness during a meeting
  (default `120`); the previous brightness and app order are restored on exit.

If the calendar cron stops while a meeting is underway, the wave can stay on the
display. Clear it manually:

```sh
.venv/bin/python src/meeting_mode.py exit
```

## Privacy and network security

The read-only scope still exposes calendar event metadata to this application:
each push sends up to three event titles and times, so several titles at once
now reach the physical display, not just one. Anyone who can see the display can
see that text. This is intentional for a private desk display; use a generic
title policy such as `Busy` if the display is later moved to a shared or public
space. Event titles are still never written to the application log.

The OAuth token and client files are secrets. Keep `.google-calendar/` outside
source control and transfer tokens only over a protected channel. The documented
setup uses a `700` directory and `600` files, and the repository ignores the
standard directory. Custom paths must be protected and kept out of Git as well.

The AWTRIX host is a privileged local API because this project can push pages and
change the clock's app state. A trusted apartment LAN is an appropriate boundary
for personal use, but the clock should not be port-forwarded or exposed directly
to the internet. On shared networks, enable AWTRIX authentication and HTTPS if
available, and configure `AWTRIX_HOST` accordingly.

## 1. Create the Google OAuth client

Use Python **3.10+** on the Mac and Pi; **3.11+** is recommended. In the
[Google Cloud Console](https://console.cloud.google.com/):

1. Create or choose a project and enable **Google Calendar API** under
   **APIs & Services → Library**.
2. Configure **Google Auth platform → Branding** with an app name and contact
   email. Under **Audience**, use **External** for a personal Google account.
   Workspace accounts may use **Internal** if permitted by their organization.
3. While the app is in **Testing**, add your Google account as a test user.
   Add `https://www.googleapis.com/auth/calendar.events.readonly` under
   **Data Access**. This permits reading events; it does not grant write access.
4. Under **Clients**, create an OAuth client with application type **Desktop app**
   and download its JSON file. Use a Desktop client, not a Web client or service account.

On the Mac, from this checkout:

```sh
mkdir -m 700 -p .google-calendar
```

Save the downloaded JSON as `.google-calendar/credentials.json`, then:

```sh
chmod 600 .google-calendar/credentials.json
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/calendar_widget.py --authorize
```

If the virtual environment does not exist, first create it with
`python3 -m venv .venv`. Finish the browser sign-in within three minutes using
the account whose primary calendar you want displayed. The command requests
offline access and writes `.google-calendar/token.json` with mode `600`.
Authorization alone does not fetch events or change the clock.

Google's [Python quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
describes the Cloud project and Desktop-client setup.

## 2. Keep unattended authorization working

For External apps in **Testing**, Calendar refresh tokens expire after **seven
days**. For continued unattended operation, open **Google Auth platform → Audience**,
choose **Publish app** to move to **In production**, then rerun `--authorize` to
obtain a new token before transferring it to the Pi. Production status does not
prevent revocation or account-policy expiration.

A personal-use app may qualify for Google's verification exception and still
show an unverified-app warning. Do not assume this setup authorizes distribution
to other users; Workspace administrators can also restrict consent. See Google's
[token expiration rules](https://developers.google.com/identity/protocols/oauth2#expiration)
and [verification exceptions](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).

When a token is revoked or expires, the regular command exits nonzero and asks
you to rerun `--authorize` on your Mac. It never launches a browser from cron.

## 3. Transfer the token to the Pi

Replace `your-user@your-pi.local` and `/home/your-user/deskmate` below with the Pi's
SSH destination and existing checkout. Update the checkout through your normal
Git workflow, then install the requirements in its virtual environment.

Only the token needs transferring: it contains the OAuth client information
required for refresh, so the Pi does not need the downloaded client JSON.
Use SSH/SCP rather than putting the token in Git or copying it into chat:

```sh
ssh your-user@your-pi.local 'mkdir -m 700 -p /home/your-user/deskmate/.google-calendar && chmod 700 /home/your-user/deskmate/.google-calendar'
scp .google-calendar/token.json your-user@your-pi.local:/home/your-user/deskmate/.google-calendar/token.new.json
ssh your-user@your-pi.local 'chmod 600 /home/your-user/deskmate/.google-calendar/token.new.json && mv /home/your-user/deskmate/.google-calendar/token.new.json /home/your-user/deskmate/.google-calendar/token.json'
```

The default `.google-calendar/` directory, calendar log, and lock file are ignored
by Git. If you choose custom credential paths, keep those files outside Git too.
Refresh saves use an owner-only temporary file and atomic replacement.

## 4. Configure and run on the Pi

Add these settings to the Pi's existing `.env` without overwriting its Codex settings:

```dotenv
AWTRIX_HOST=http://your-awtrix-host
GOOGLE_CALENDAR_CREDENTIALS_PATH=.google-calendar/credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=.google-calendar/token.json
GOOGLE_CALENDAR_TIMEZONE=America/New_York
```

Relative paths are resolved from the checkout, regardless of the working directory.
An existing shell variable takes precedence over `.env`. The display timezone
must be an IANA name; event comparisons use UTC to handle DST correctly. Replace
`your-awtrix-host` with the hostname or address of your clock on the Pi's network.

```sh
cd /home/your-user/deskmate
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/calendar_widget.py
```

Successful output confirms the calendar page is present, pushed, enabled, and in
the rotation. If clear, the command removes only its own pushed page and verifies
removal. A script or other non-pushed app called `google_calendar` blocks updates
and deletion. Enable a disabled page through AWTRIX's own controls.

Install this additional line with `crontab -e` as the Pi user:

```cron
* * * * * /usr/bin/flock -n /home/your-user/deskmate/.calendar.lock /home/your-user/deskmate/.venv/bin/python /home/your-user/deskmate/src/calendar_widget.py >> /home/your-user/deskmate/calendar.log 2>&1 # deskmate-calendar
```

Keep the existing hourly Codex entry. Calendar has its own overlap lock and log,
and resumes after reboot. Google HTTP requests have a ten-second timeout;
pagination also has a 45-second deadline checked after each request. Failed runs
exit nonzero, and the next cron invocation retries. Logs omit tokens and event titles.

Each successful push expires after the earlier of two minutes or the soonest
start/end boundary among the events on screen. Network or authorization failures
never look like an empty calendar: the previous page expires naturally. A boundary
can leave a brief gap until the next minute's refresh. AWTRIX's `repeat: 1` and
explicit wrap scrolling let the entire message pass once per rotation without
changing global settings.

To stop updates, remove only the `# deskmate-calendar` cron line; the page expires.
Check `crontab -l` and `tail -n 20 calendar.log` to diagnose scheduling issues.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The tests cover multi-event selection and ordering, the rendered agenda and
icon, DST and boundaries, recurring-event pagination, real Google client request
construction with a substituted HTTP transport, private token storage,
refresh/revocation, `.env` precedence, and safe AWTRIX push/removal. They do not
prove account consent, Pi access, or physical readability.

After real authorization, run once on the Pi and confirm on the **physical TC001**:
the whole agenda scrolls; the `calendardots` icon renders at 8×8 beside it; a
meeting underway replaces the page with the wave and returns the page afterward;
`" | "` separates several events cleanly; an empty 24-hour window hides the page;
and Codex and the other apps continue rotating normally.
For HTTP 403, check API enablement, the chosen account's permissions, and quota.
For connection errors, check the Pi's internet access and `AWTRIX_HOST`.
