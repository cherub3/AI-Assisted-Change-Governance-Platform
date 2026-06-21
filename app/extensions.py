"""Shared Flask extension instances.

Kept in their own module (separate from app/__init__.py) so that models and
services can import `db` without triggering circular imports through the
app factory.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
