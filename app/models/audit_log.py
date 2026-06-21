"""AuditLog model — the immutable governance audit trail.

GOVERNANCE RULE: rows in this table are INSERT-ONLY. No code path anywhere
in this application may UPDATE or DELETE a row here. The sole sanctioned
writer is AuditService.log_action() (see app/services/audit_service.py) —
do not construct AuditLog(...) directly elsewhere.
"""

import uuid

from app.extensions import db


class AuditLog(db.Model):
    """Does NOT inherit BaseModel: this record is append-only and therefore
    has no updated_at column.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        db.Index("ix_audit_logs_change_request_id", "change_request_id"),
        db.Index("ix_audit_logs_created_at", "created_at"),
    )

    event_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    change_request_id = db.Column(db.Integer, db.ForeignKey("change_requests.id"), nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    from_state = db.Column(db.String(50), nullable=True)
    to_state = db.Column(db.String(50), nullable=True)
    # SQLAlchemy's generic JSON type stores as TEXT on SQLite and handles
    # serialization transparently — no manual fallback needed.
    detail_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    change_request = db.relationship("ChangeRequest", back_populates="audit_logs")
    actor = db.relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog event_id={self.event_id} action={self.action!r}>"
