import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from yt_dlp.utils import sanitize_filename

from app.errors import ConversionError, DownloadFailedError, VideoUnavailableError

_UNAVAILABLE_MARKERS = (
    "private video",
    "sign in to confirm your age",
    "age-restricted",
    "unavailable",
    "removed",
    "not available",
    "blocked it",
    "copyright",
)


@dataclass
class ConversionResult:
    filename: str
    data: bytes
    mimetype: str = "audio/mpeg"


def convert_to_mp3(url: str) -> ConversionResult:
    """Download a single YouTube video's audio and transcode it to MP3.

    Returns the MP3 bytes and a filesystem-safe filename derived from the video title.
    Always cleans up the temp working directory, on both success and failure.
    """
    if not shutil.which("ffmpeg"):
        raise ConversionError("ffmpeg is not installed or not on PATH.")

    tmp_dir = tempfile.mkdtemp(prefix="ytmp3_")
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(tmp_dir) / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
            # Prefer YouTube's mobile-app API over the website — it's less
            # aggressively bot-checked, so this often avoids needing cookies
            # at all on cloud hosts. Falls back to the web client if it fails.
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        }

        cookies_file = os.environ.get("YTDLP_COOKIES_FILE")
        if cookies_file and os.path.isfile(cookies_file):
            ydl_opts["cookiefile"] = cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as exc:
            message = str(exc).lower()
            if any(marker in message for marker in _UNAVAILABLE_MARKERS):
                raise VideoUnavailableError(
                    "This video can't be downloaded (it may be private, "
                    "age-restricted, or unavailable in this region)."
                ) from exc
            raise DownloadFailedError(
                "Couldn't reach YouTube. Check your connection and try again."
            ) from exc

        mp3_path = Path(tmp_dir) / f"{info['id']}.mp3"
        if not mp3_path.exists():
            raise ConversionError("Audio conversion did not produce an MP3 file.")

        title = info.get("title") or info["id"]
        filename = f"{sanitize_filename(title, restricted=True)[:150]}.mp3"

        return ConversionResult(filename=filename, data=mp3_path.read_bytes())
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
