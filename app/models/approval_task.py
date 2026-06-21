"""ApprovalTask model and status enum."""

import enum

from app.extensions import db
from app.models.base import BaseModel


class ApprovalTaskStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def _values(enum_cls):
    return [e.value for e in enum_cls]


class ApprovalTask(BaseModel):
    """A single approval assignment against a change request.

    GOVERNANCE NOTE (segregation of duties): WorkflowService.approve() /
    .reject() (Phase 2) must reject any attempt where approver_id ==
    change_request.submitter_id.
    """

    __tablename__ = "approval_tasks"
    __table_args__ = (
        db.Index("ix_approval_tasks_status", "status"),
        db.Index("ix_approval_tasks_approver_id", "approver_id"),
    )

    change_request_id = db.Column(db.Integer, db.ForeignKey("change_requests.id"), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(
        db.Enum(ApprovalTaskStatus, values_callable=_values, native_enum=False, length=20),
        nullable=False,
        default=ApprovalTaskStatus.PENDING,
    )
    assigned_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    comments = db.Column(db.Text, nullable=True)

    change_request = db.relationship("ChangeRequest", back_populates="approval_tasks")
    approver = db.relationship(
        "User", back_populates="approval_tasks", foreign_keys=[approver_id]
    )

    def __repr__(self) -> str:
        return f"<ApprovalTask id={self.id} change_request_id={self.change_request_id} status={self.status.value}>"
