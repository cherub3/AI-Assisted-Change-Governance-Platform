"""RiskScore model and risk tier enum."""

import enum

from app.extensions import db
from app.models.base import BaseModel


class RiskTier(str, enum.Enum):
    MANAGER = "manager"
    MANAGER_PMO = "manager_pmo"


def _values(enum_cls):
    return [e.value for e in enum_cls]


class RiskScore(BaseModel):
    """A single risk calculation against a change request.

    One-to-many with ChangeRequest by design: recalculation (Phase 3,
    RiskEngine) inserts a new row with an incremented `version` rather than
    overwriting the previous score. History is never destroyed.
    """

    __tablename__ = "risk_scores"
    __table_args__ = (db.Index("ix_risk_scores_change_request_id", "change_request_id"),)

    change_request_id = db.Column(db.Integer, db.ForeignKey("change_requests.id"), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    score_value = db.Column(db.Integer, nullable=False)
    tier = db.Column(
        db.Enum(RiskTier, values_callable=_values, native_enum=False, length=20),
        nullable=False,
    )
    # SQLAlchemy's generic JSON type stores as TEXT on SQLite and handles
    # serialization transparently — no manual fallback needed.
    rules_fired_json = db.Column(db.JSON, nullable=True)
    calculated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    change_request = db.relationship("ChangeRequest", back_populates="risk_scores")

    def __repr__(self) -> str:
        return f"<RiskScore id={self.id} change_request_id={self.change_request_id} version={self.version} tier={self.tier.value}>"
