"""AIExtractionLog model — immutable record of every Bedrock extraction call.

GOVERNANCE RULE: rows in this table are INSERT-ONLY. No code path anywhere
in this application may UPDATE or DELETE a row here. Captures the full
prompt/response pair so any AI-derived field can later be explained or
audited.
"""

import uuid

from app.extensions import db


class AIExtractionLog(db.Model):
    """Does NOT inherit BaseModel: this record is append-only and therefore
    has no updated_at column.
    """

    __tablename__ = "ai_extraction_logs"
    __table_args__ = (db.Index("ix_ai_extraction_logs_change_request_id", "change_request_id"),)

    event_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    change_request_id = db.Column(db.Integer, db.ForeignKey("change_requests.id"), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(50), nullable=True)
    prompt_text = db.Column(db.Text, nullable=False)
    # SQLAlchemy's generic JSON type stores as TEXT on SQLite and handles
    # serialization transparently — no manual fallback needed.
    raw_response_json = db.Column(db.JSON, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    change_request = db.relationship("ChangeRequest", back_populates="ai_extraction_logs")

    def __repr__(self) -> str:
        return f"<AIExtractionLog event_id={self.event_id} model={self.model!r}>"
