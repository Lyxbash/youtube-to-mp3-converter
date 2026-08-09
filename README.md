# youtube-to-mp3-converter

A private, personal web app: paste a YouTube video link, click convert,
preview the audio in the browser, then download it as an MP3.

This is a single-user tool gated behind a password — it is **not** a public
service for arbitrary visitors. See [Disclaimer](#disclaimer).

## How it works, in one paragraph

Flask serves a one-page UI. When you submit a URL, the server uses
[yt-dlp](https://github.com/yt-dlp/yt-dlp) to fetch the audio and `ffmpeg` to
transcode it to MP3, then streams the file back to your browser — nothing is
stored permanently on the server. A password-gated login (see
[Access control](#access-control)) controls who can reach any of this.

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) installed and available on `PATH`
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu: `sudo apt-get install ffmpeg`
  - Windows: download a build from ffmpeg.org (e.g. gyan.dev builds) and add
    its `bin` folder to `PATH` — then **restart your terminal/IDE** so it
    picks up the change
- Or just Docker, if you don't want to install anything locally

## Run locally

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000. If `APP_PASSWORD` isn't set (see below), you'll
land straight on the converter with no login prompt — that's expected for
local dev.

## Run with Docker

```bash
docker build -t youtube-to-mp3 .
docker run -p 5000:5000 -e APP_PASSWORD=choose-a-password youtube-to-mp3
```

Open http://localhost:5000 — ffmpeg and all dependencies are baked into the
image.

## Usage

1. Paste a single YouTube video URL (e.g. `https://www.youtube.com/watch?v=...`
   or `https://youtu.be/...`).
2. Click **Convert to MP3**.
3. Once conversion finishes, preview the audio inline, then click
   **Download MP3** to save it.

## Access control

*This controls who can open the app at all — it has nothing to do with
whether YouTube itself allows the download to happen. If you're getting a
"Couldn't reach YouTube" error, that's a different problem — see
[Troubleshooting](#troubleshooting-couldnt-reach-youtube), not this section.*

The app is gated behind one shared password (there are no separate user
accounts — it's built for a single owner). Set it via an environment
variable:

```bash
APP_PASSWORD=choose-a-strong-password
```

If `APP_PASSWORD` is not set, the app runs with **no login screen at all** —
anyone with the URL can use it. That's fine for local-only use (nothing
outside your machine can reach `localhost`), but for any deployment reachable
from the internet (like Render), always set it. The app logs a warning on
startup if it's missing.

Also set `SECRET_KEY` to a long random string, so that being logged in
survives app restarts and redeploys instead of signing you out every time:

```bash
SECRET_KEY=<random-hex-string>
# generate one with:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

On Render, add both as environment variables under your service's
**Environment** tab, then redeploy. The login cookie's `Secure` flag turns on
automatically once the app detects it's running on Render (HTTPS).

## Deploying to the cloud (e.g. Render)

1. Push this repo to GitHub (already done if you're reading this from the repo).
2. On [Render](https://render.com): **New** → **Web Service** → connect this
   repo → Runtime: **Docker** → Instance Type: **Free**.
3. Add environment variables `APP_PASSWORD` and `SECRET_KEY` (see
   [Access control](#access-control)).
4. Deploy. Render gives you a public URL like
   `https://your-app.onrender.com`.
5. If conversions fail with a YouTube-related error, see the next section.

**Free-tier note:** the instance sleeps after ~15 minutes of no traffic and
takes 30-60 seconds to wake up on the next request. That's normal — the link
still always works, the first request after a while is just slower.

## Troubleshooting: "Couldn't reach YouTube"

This means YouTube itself rejected the download request — it detected the
server's IP as a datacenter/bot IP rather than a real browser. This is
unrelated to the app's login password; it happens regardless of who's signed
in, and on a cloud host (e.g. Render) it will happen on essentially every
request unless cookies are configured. Authenticating as your own YouTube
account via exported browser cookies is the fix:

1. While logged into youtube.com in your normal browser, export cookies to a
   Netscape-format `cookies.txt` file. Easiest way: a browser extension like
   "Get cookies.txt LOCALLY" (Chrome/Firefox).
2. **Never commit this file to git** — it's equivalent to a login token for
   your Google account.
3. Get the contents into Render one of two ways (pick one, don't mix them up
   — this is the single most common mistake):
   - **`YTDLP_COOKIES_CONTENT` (recommended — simplest, no known issues):**
     the *entire text contents* of `cookies.txt`, pasted directly as the
     value of this environment variable.
   - **`YTDLP_COOKIES_FILE` (alternative):** a *file path* — e.g.
     `/etc/secrets/cookies.txt` — pointing at a Render **Secret File** you
     uploaded separately under **Environment** → **Secret Files** containing
     the cookie text. This variable's value must be the path, never the
     cookie text itself. If Render's Secret Files UI errors out on upload,
     just use `YTDLP_COOKIES_CONTENT` instead — it does the same job without
     that extra step.
4. Redeploy. The app automatically picks up whichever one you set — no code
   changes needed.

These cookies expire eventually (e.g. if you sign out everywhere or change
your Google password) and will need re-exporting when that happens.

## Limitations

- One video at a time — playlist URLs are accepted but only the single video
  is converted.
- Single shared password, not multi-user accounts.
- No job queue — a conversion blocks that request until it finishes, which
  is fine for one person using it occasionally.

## Disclaimer

This tool is intended for **personal, single-user, non-commercial use only**
— for content you have the rights to or that's otherwise permitted for
personal offline use. It is deliberately not built or intended to serve the
general public: publicly-accessible YouTube-to-MP3 conversion services have
repeatedly been found liable for copyright infringement in court (e.g. *UMG
Recordings v. FLVTO/2conv*, *RIAA v. youtube-mp3.org*), which is why this app
is password-gated to a single owner rather than open to anyone. You are
solely responsible for ensuring your use complies with YouTube's Terms of
Service and applicable copyright law in your jurisdiction.
