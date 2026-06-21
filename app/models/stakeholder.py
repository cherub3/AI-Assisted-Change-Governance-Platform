"""Stakeholder model.

Populated by ExtractionService (AI-suggested) and then reviewed/confirmed by
a human before the change request can proceed to risk scoring.
"""

from app.extensions import db
from app.models.base import BaseModel


class Stakeholder(BaseModel):
    __tablename__ = "stakeholders"
    __table_args__ = (db.Index("ix_stakeholders_change_request_id", "change_request_id"),)

    change_request_id = db.Column(db.Integer, db.ForeignKey("change_requests.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    change_request = db.relationship("ChangeRequest", back_populates="stakeholders")

    def __repr__(self) -> str:
        return f"<Stakeholder id={self.id} name={self.name!r} confirmed={self.confirmed}>"
