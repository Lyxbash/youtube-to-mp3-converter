import os
import secrets

from flask import Flask


def create_app() -> Flask:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
    )

    if not os.environ.get("APP_PASSWORD"):
        app.logger.warning(
            "APP_PASSWORD is not set - this app is running with NO authentication. "
            "Anyone with the URL can use it."
        )

    from app.routes import bp

    app.register_blueprint(bp)

    return app
