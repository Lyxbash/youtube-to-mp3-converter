import os

from flask import Flask


def create_app() -> Flask:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    from app.routes import bp

    app.register_blueprint(bp)

    return app
