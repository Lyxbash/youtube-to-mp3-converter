import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from yt_dlp.utils import sanitize_filename

from app.errors import ConversionError, DownloadFailedError, VideoUnavailableError

logger = logging.getLogger(__name__)


class _YtdlpLogger:
    """Route yt-dlp's own messages into our logger so they show in host logs.

    yt-dlp normally prints to stderr; funnelling through logging keeps its
    warnings (e.g. PO-token generation failures) and, when verbose is on, its
    debug output visible and consistently formatted in Render's log stream.
    """

    def debug(self, msg):
        logger.info("yt-dlp: %s", msg)

    def info(self, msg):
        logger.info("yt-dlp: %s", msg)

    def warning(self, msg):
        logger.warning("yt-dlp: %s", msg)

    def error(self, msg):
        logger.error("yt-dlp: %s", msg)

_UNAVAILABLE_MARKERS = (
    "private video",
    "sign in to confirm your age",
    "age-restricted",
    "video unavailable",
    "this video is not available",
    "removed by the uploader",
    "not made this video available in your country",
    "copyright claim",
)


@dataclass
class ConversionResult:
    filename: str
    data: bytes
    mimetype: str = "audio/mpeg"


_cookies_file_cache = None


def _resolve_cookies_file() -> str | None:
    """Find a cookies.txt to authenticate yt-dlp with, if one is configured.

    Supports either a path to an already-present file (YTDLP_COOKIES_FILE,
    e.g. a Render Secret File) or the file's raw contents pasted directly
    into an environment variable (YTDLP_COOKIES_CONTENT), which is written
    to a temp file once and reused for the life of the process.
    """
    global _cookies_file_cache
    if _cookies_file_cache and os.path.isfile(_cookies_file_cache):
        return _cookies_file_cache

    explicit_path = os.environ.get("YTDLP_COOKIES_FILE")
    content = os.environ.get("YTDLP_COOKIES_CONTENT")
    logger.info(
        "Cookie env check: YTDLP_COOKIES_FILE=%s (exists=%s) YTDLP_COOKIES_CONTENT "
        "is-set=%s length=%d",
        explicit_path or "<unset>",
        bool(explicit_path and os.path.isfile(explicit_path)),
        content is not None,
        len(content) if content else 0,
    )

    if explicit_path and os.path.isfile(explicit_path):
        _cookies_file_cache = explicit_path
        return _cookies_file_cache

    if content:
        fd, path = tempfile.mkstemp(prefix="ytdlp_cookies_", suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        _cookies_file_cache = path
        return _cookies_file_cache

    return None


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
            # Surface yt-dlp warnings (e.g. failed PO-token generation) via our
            # logger so download failures are diagnosable from host logs.
            "no_warnings": False,
            "restrictfilenames": True,
            "logger": _YtdlpLogger(),
        }

        # Set YTDLP_VERBOSE=1 to get yt-dlp's full debug trace (including PO
        # token provider activity) in the logs when diagnosing a failure.
        if os.environ.get("YTDLP_VERBOSE"):
            ydl_opts["verbose"] = True
            ydl_opts["quiet"] = False

        # yt-dlp needs a JavaScript runtime to solve YouTube's "n" signature
        # challenge; without it, format URLs can't be deciphered and only
        # storyboard images remain. Node >= 22 is supported for this (and also
        # backs the POT provider). We standardise on Node rather than Deno:
        # when Deno is also present, the bgutil plugin probes a Deno code path
        # that hangs and times out during extraction.
        if shutil.which("node"):
            ydl_opts["js_runtimes"] = {"node": {}}
            logger.info("Using node as yt-dlp JS runtime")
        else:
            logger.info("node not found; yt-dlp has no JS runtime available")

        # YouTube now demands a proof-of-origin (PO) token from datacenter
        # IPs even with valid cookies. The bgutil POT-provider plugin mints
        # those tokens by shelling out to its bundled Node server, whose
        # location is passed here. Only enabled when that server is actually
        # present (it's built into the Docker image, absent for local runs
        # from a home IP that don't need a PO token in the first place).
        bgutil_home = os.environ.get("BGUTIL_SERVER_HOME")
        if bgutil_home and os.path.isdir(bgutil_home):
            # The bgutil script provider needs this exact built file; if the
            # Docker build didn't produce it, the provider registers as
            # "unavailable" and yt-dlp silently proceeds with no PO token.
            script_path = os.path.join(bgutil_home, "build", "generate_once.js")
            script_ok = os.path.isfile(script_path)
            logger.info(
                "PO token provider enabled (bgutil server at %s); "
                "generate_once.js present=%s",
                bgutil_home,
                script_ok,
            )
            if not script_ok:
                logger.warning(
                    "bgutil script %s is MISSING - PO tokens will not be "
                    "generated. The Node build in the Docker image likely "
                    "failed or output elsewhere.",
                    script_path,
                )
            ydl_opts["extractor_args"] = {
                "youtubepot-bgutilscript": {"server_home": [bgutil_home]}
            }
        else:
            logger.info("PO token provider not configured (BGUTIL_SERVER_HOME unset)")

        cookies_file = _resolve_cookies_file()
        if cookies_file:
            with open(cookies_file) as f:
                cookie_count = sum(
                    1 for line in f if line.strip() and not line.startswith("#")
                )
            logger.info(
                "Using cookies file %s with %d cookie entries", cookies_file, cookie_count
            )
            if cookie_count == 0:
                logger.warning(
                    "Cookies file resolved but contains 0 usable entries - "
                    "check YTDLP_COOKIES_CONTENT/YTDLP_COOKIES_FILE for formatting issues"
                )
            ydl_opts["cookiefile"] = cookies_file
        else:
            logger.warning(
                "No YouTube cookies configured "
                "(neither YTDLP_COOKIES_FILE nor YTDLP_COOKIES_CONTENT is set)"
            )

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
