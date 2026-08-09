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
3. The MP3 downloads automatically once conversion finishes.

## Limitations

- One video at a time — playlist URLs are accepted but only the single video is converted.
- No authentication, no multi-user job queue — this is a personal-use tool.

## Disclaimer

This tool is intended for personal, non-commercial use only. You are solely
responsible for ensuring your use complies with YouTube's Terms of Service
and applicable copyright law in your jurisdiction.
