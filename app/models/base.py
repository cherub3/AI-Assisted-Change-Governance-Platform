"""Abstract base model shared by all mutable domain models."""

from app.extensions import db


class BaseModel(db.Model):
    """Common columns for every domain model.

    NOTE: AuditLog and AIExtractionLog deliberately do NOT inherit from this
    class. They are immutable, append-only records and therefore have no
    updated_at — a row that can never be updated should not carry a column
    that implies it can.
    """

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False
    )
