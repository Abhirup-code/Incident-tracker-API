import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_overrides=None):
    app = Flask(__name__)

    default_db_url = "sqlite:///incidents.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", default_db_url
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    from app.routes import bp as incidents_bp

    app.register_blueprint(incidents_bp)

    with app.app_context():
        db.create_all()

    return app
