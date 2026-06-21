"""ORM-level enforcement of audit-trail immutability.

GOVERNANCE RULE: audit_logs and ai_extraction_logs are insert-only tables.
AuditService.log_action() and ExtractionService are the only sanctioned
writers, and even they never issue an UPDATE or DELETE. These mapper-level
event listeners are the backstop: if any code path — present or future —
attempts to mutate or remove a row from either table via this ORM, the
flush is aborted with a ValueError before any SQL reaches the database.

Importing this module registers the listeners as a side effect (see
app/__init__.py: create_app() imports `app.events`). Since Python caches
module imports, this registration runs exactly once per process even if
create_app() is called multiple times.
"""

from sqlalchemy import event

from app.models.ai_extraction_log import AIExtractionLog
from app.models.audit_log import AuditLog


def _reject_mutation(mapper, connection, target) -> None:
    """Shared before_update/before_delete handler for both immutable models."""
    raise ValueError(f"{target.__class__.__name__} is immutable and cannot be updated/deleted")


event.listen(AuditLog, "before_update", _reject_mutation)
event.listen(AuditLog, "before_delete", _reject_mutation)
event.listen(AIExtractionLog, "before_update", _reject_mutation)
event.listen(AIExtractionLog, "before_delete", _reject_mutation)
