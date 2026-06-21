"""Flask application factory."""

import os
import sqlite3

from flask import Flask
from sqlalchemy import event

from app.config import Config
from app.extensions import db

# Project root (change-governance/), one level up from this app/ package.
# Passed below as Flask's instance_path so a relative "sqlite:///..." URI
# resolves directly there instead of Flask's default nested instance/
# subfolder.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_class: type = Config) -> Flask:
    """Build and configure the Flask application.

    Models are imported here (inside the factory, after the app exists)
    rather than at module level, to avoid circular imports between
    app/__init__.py and app/models/*.
    """
    app = Flask(__name__, instance_path=_PROJECT_ROOT)
    app.config.from_object(config_class)

    db.init_app(app)

    with app.app_context():
        from app import models  # noqa: F401  registers all tables with db.metadata
        from app import events  # noqa: F401  registers audit-immutability event listeners

        # SQLite parses and stores FOREIGN KEY constraints but does NOT
        # enforce them unless this pragma is set on every connection — it is
        # off by default. Without this, every FK column in app/models/*
        # (submitter_id, approver_id, change_request_id, ...) is decorative:
        # inserting an ApprovalTask with a non-existent approver_id would
        # silently succeed. Scoped to db.engine (this app's engine only) via
        # the SQLAlchemy "connect" event, the standard pysqlite recipe.
        @event.listens_for(db.engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return app
