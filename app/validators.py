import re
from urllib.parse import parse_qs, urlparse

from app.errors import InvalidUrlError

_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url: str) -> str:
    """Validate that `url` is a plausible single-video YouTube URL and return its video ID.

    Raises InvalidUrlError if the URL isn't recognizable as a YouTube video link.
    """
    if not url or not isinstance(url, str):
        raise InvalidUrlError("Please enter a YouTube video URL.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise InvalidUrlError("Please enter a valid YouTube video URL.")

    host = parsed.netloc.lower()
    if host not in _ALLOWED_HOSTS:
        raise InvalidUrlError("Please enter a valid YouTube video URL.")

    video_id = None
    if host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/shorts/", 1)[1].split("/")[0]

    if not video_id or not _VIDEO_ID_RE.match(video_id):
        raise InvalidUrlError("Please enter a valid YouTube video URL.")

    return video_id
