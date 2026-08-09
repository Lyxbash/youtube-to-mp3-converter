import functools
import hmac
import os

from flask import jsonify, redirect, request, session, url_for


def app_password() -> str | None:
    return os.environ.get("APP_PASSWORD") or None


def check_password(candidate: str) -> bool:
    expected = app_password()
    if not expected:
        return True
    return hmac.compare_digest(candidate, expected)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not app_password() or session.get("authenticated"):
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify(error="Unauthorized"), 401
        return redirect(url_for("main.login", next=request.path))

    return wrapped
