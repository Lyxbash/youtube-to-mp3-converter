import io

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException

from app.converter import convert_to_mp3
from app.errors import (
    ConversionAppError,
    ConversionError,
    DownloadFailedError,
    InvalidUrlError,
    VideoUnavailableError,
)
from app.validators import extract_video_id

bp = Blueprint("main", __name__)

_ERROR_STATUS = {
    InvalidUrlError: 400,
    VideoUnavailableError: 422,
    DownloadFailedError: 502,
    ConversionError: 500,
}


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/healthz")
def healthz():
    return jsonify(status="ok")


@bp.post("/api/convert")
def convert():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "")

    try:
        extract_video_id(url)
        result = convert_to_mp3(url)
    except ConversionAppError as exc:
        status = _ERROR_STATUS.get(type(exc), 500)
        if status == 500:
            current_app.logger.exception("Conversion failed")
        return jsonify(error=str(exc)), status

    return send_file(
        io.BytesIO(result.data),
        mimetype=result.mimetype,
        as_attachment=True,
        download_name=result.filename,
    )


@bp.app_errorhandler(Exception)
def handle_unexpected_error(exc):
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.description), exc.code
    current_app.logger.exception("Unhandled error")
    return jsonify(error="Something went wrong during conversion. Please try again."), 500
