# youtube-to-mp3-converter

A small local web app: paste a YouTube video link, click convert, and download the audio as an MP3.

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/download.html) installed and available on `PATH`
  - macOS: `brew install ffmpeg`
  - Debian/Ubuntu: `sudo apt-get install ffmpeg`
  - Windows: download a build from ffmpeg.org and add it to `PATH`
- Or just Docker, if you don't want to install anything locally.

## Run locally

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:5000, paste a YouTube video URL, and click **Convert to MP3**.

## Run with Docker

```bash
docker build -t youtube-to-mp3 .
docker run -p 5000:5000 youtube-to-mp3
```

Open http://localhost:5000 — ffmpeg and all dependencies are baked into the image.

## Usage

1. Paste a single YouTube video URL (e.g. `https://www.youtube.com/watch?v=...` or `https://youtu.be/...`).
2. Click **Convert to MP3**.
3. Once conversion finishes, preview the audio inline, then click **Download MP3** to save it.

## Limitations

- One video at a time — playlist URLs are accepted but only the single video is converted.
- Single-password login, no multi-user accounts or job queue — this is a personal-use tool.

## Access control

The app is gated behind a single shared password (there are no separate user
accounts — this is meant for one person). Set it via an environment variable:

```bash
APP_PASSWORD=choose-a-strong-password
```

If `APP_PASSWORD` is not set, the app runs with **no authentication** — fine
for local-only use, but it logs a warning on startup and you should always
set it for any publicly reachable deployment (e.g. Render).

Also set `SECRET_KEY` to a long random string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)
so login sessions survive app restarts/redeploys instead of logging you out
each time:

```bash
SECRET_KEY=<random-hex-string>
```

On Render, add both as environment variables under your service's
**Environment** tab. Cookie security (`Secure` flag) is enabled automatically
whenever the app detects it's running on Render.

## Deploying to the cloud (e.g. Render)

YouTube blocks download requests from most cloud/datacenter IP ranges with a
"Sign in to confirm you're not a bot" error. If you see that error (as
`Couldn't reach YouTube...` in the UI, with the real reason in your host's
logs), you need to authenticate yt-dlp with cookies from your own logged-in
YouTube session:

1. While logged into youtube.com in your browser, export your cookies to a
   Netscape-format `cookies.txt` file. The easiest way is a browser
   extension such as "Get cookies.txt LOCALLY" (Chrome/Firefox).
2. **Do not commit this file to git** — it's equivalent to a session login
   token for your Google account.
3. On Render: go to your service → **Environment** → **Secret Files** → add
   a file with path `/etc/secrets/cookies.txt` and paste the exported
   contents.
4. Add an environment variable `YTDLP_COOKIES_FILE=/etc/secrets/cookies.txt`.
5. Redeploy. The app automatically uses the cookie file if that environment
   variable is set and points at a file that exists — no code changes needed.

Note: these cookies will eventually expire or get invalidated (e.g. if you
sign out everywhere or change your password), and you'll need to re-export
and re-upload them when that happens.

## Disclaimer

This tool is intended for personal, non-commercial use only. You are solely
responsible for ensuring your use complies with YouTube's Terms of Service
and applicable copyright law in your jurisdiction.
