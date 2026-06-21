"""Audit logging service.

GOVERNANCE RULE: AuditService is the ONLY component permitted to write to
the audit_logs table. No model, route, or script should construct an
AuditLog(...) and add it to the session directly — always go through
AuditService.log_action() so every write follows the same shape and is
guaranteed to be append-only (this service never issues an UPDATE or DELETE).
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.extensions import db
from app.models.audit_log import AuditLog


class AuditService:
    """Writes immutable audit records."""

    @staticmethod
    def log_action(
        actor_id: int,
        change_request_id: Optional[int],
        action: str,
        from_state: Optional[str],
        to_state: Optional[str],
        detail_json: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True,
    ) -> AuditLog:
        """Append an immutable audit record.

        Intended to be called on every state transition (submit, approve,
        reject, override, extraction-confirmed, etc.) by the service that
        performs the transition — never directly from a route.

        Args:
            actor_id: ID of the user performing the action.
            change_request_id: Change request affected, or None for a
                system-level event not tied to a specific request.
            action: Short verb describing what happened, e.g. "submit",
                "approve", "reject", "override".
            from_state: Status before the action (None if not a state
                transition).
            to_state: Status after the action (None if not a state
                transition).
            detail_json: Optional extra context to preserve alongside the
                event (e.g. a rejection reason or override justification).
            auto_commit: If True (default), the record is committed
                immediately as its own transaction — use this for events
                that must persist independently of any business change
                (e.g. a logged SoD violation attempt, where the underlying
                state change is rejected). If False, the record is added
                and flushed but left uncommitted, so it participates in —
                and rolls back with — the caller's surrounding transaction.

        Returns:
            The persisted AuditLog row.
        """
        audit_log = AuditLog(
            event_id=str(uuid.uuid4()),
            change_request_id=change_request_id,
            actor_id=actor_id,
            action=action,
            from_state=from_state,
            to_state=to_state,
            detail_json=detail_json or {},
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(audit_log)
        if auto_commit:
            db.session.commit()
        else:
            db.session.flush()
        return audit_log
