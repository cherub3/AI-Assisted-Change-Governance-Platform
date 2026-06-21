"""Database initialization entry point.

Run with:
    python -m app.database
"""

from app import create_app
from app.extensions import db


def init_db() -> None:
    """Create all tables and load seed data. Idempotent — safe to run multiple times."""
    db.create_all()

    from seeds.seed_data import load_seed_data

    load_seed_data()
    print("Database initialized. 7 tables created. Seed data loaded.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_db()
