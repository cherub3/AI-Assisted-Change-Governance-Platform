"""Importing this package registers all 7 tables with db.metadata."""

from app.models.ai_extraction_log import AIExtractionLog
from app.models.approval_task import ApprovalTask, ApprovalTaskStatus
from app.models.audit_log import AuditLog
from app.models.change_request import ChangeRequest, ChangeRequestPriority, ChangeRequestStatus
from app.models.risk_score import RiskScore, RiskTier
from app.models.stakeholder import Stakeholder
from app.models.user import User, UserRole

__all__ = [
    "AIExtractionLog",
    "ApprovalTask",
    "ApprovalTaskStatus",
    "AuditLog",
    "ChangeRequest",
    "ChangeRequestPriority",
    "ChangeRequestStatus",
    "RiskScore",
    "RiskTier",
    "Stakeholder",
    "User",
    "UserRole",
]
