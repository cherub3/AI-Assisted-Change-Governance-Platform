"""ChangeRequest model — the core aggregate of the governance lifecycle."""

import enum

from app.extensions import db
from app.models.base import BaseModel


class ChangeRequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChangeRequestStatus(str, enum.Enum):
    """Lifecycle states. Transitions between these are owned exclusively by
    WorkflowService (Phase 2) — never set directly from a route or script.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    EXTRACTION_PENDING = "extraction_pending"
    READY_FOR_SCORING = "ready_for_scoring"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


def _values(enum_cls):
    return [e.value for e in enum_cls]


class ChangeRequest(BaseModel):
    """A single change request moving through the governance lifecycle."""

    __tablename__ = "change_requests"
    __table_args__ = (
        db.Index("ix_change_requests_status", "status"),
        db.Index("ix_change_requests_submitter_id", "submitter_id"),
    )

    submitter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(
        db.Enum(ChangeRequestPriority, values_callable=_values, native_enum=False, length=20),
        nullable=False,
    )
    department = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(ChangeRequestStatus, values_callable=_values, native_enum=False, length=30),
        nullable=False,
        default=ChangeRequestStatus.DRAFT,
    )

    submitter = db.relationship(
        "User", back_populates="submitted_change_requests", foreign_keys=[submitter_id]
    )
    stakeholders = db.relationship(
        "Stakeholder", back_populates="change_request", cascade="all, delete-orphan"
    )
    approval_tasks = db.relationship(
        "ApprovalTask", back_populates="change_request", cascade="all, delete-orphan"
    )
    risk_scores = db.relationship(
        "RiskScore", back_populates="change_request", cascade="all, delete-orphan"
    )
    audit_logs = db.relationship("AuditLog", back_populates="change_request")
    ai_extraction_logs = db.relationship("AIExtractionLog", back_populates="change_request")

    def __repr__(self) -> str:
        return f"<ChangeRequest id={self.id} title={self.title!r} status={self.status.value}>"
