"""User model and role enum."""

import enum

from app.extensions import db
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """RBAC role. Enforced at the service layer in later phases — not yet wired up."""

    REQUESTER = "requester"
    APPROVER = "approver"
    ADMIN = "admin"


class User(BaseModel):
    """A system user.

    GOVERNANCE NOTE (segregation of duties): a user who submits a change
    request must never be permitted to act as the approver on that same
    request. That check belongs in WorkflowService (Phase 2), not here.
    """

    __tablename__ = "users"

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(UserRole, values_callable=lambda enum_cls: [e.value for e in enum_cls], native_enum=False, length=20),
        nullable=False,
    )

    submitted_change_requests = db.relationship(
        "ChangeRequest",
        back_populates="submitter",
        foreign_keys="ChangeRequest.submitter_id",
    )
    approval_tasks = db.relationship(
        "ApprovalTask",
        back_populates="approver",
        foreign_keys="ApprovalTask.approver_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
