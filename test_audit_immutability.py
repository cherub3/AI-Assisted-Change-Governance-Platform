"""Phase 1 verification: confirm AuditLog and AIExtractionLog are immutable.

Run with:
    python test_audit_immutability.py

Exits 0 if all four mutation attempts (AuditLog UPDATE/DELETE,
AIExtractionLog UPDATE/DELETE) are correctly blocked. Exits 1 if any
mutation is allowed to go through.
"""

import sys

# Windows consoles often default stdout to cp1252, which cannot encode the
# checkmark/cross characters below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import create_app
from app.extensions import db
from app.models.ai_extraction_log import AIExtractionLog
from app.services.audit_service import AuditService
from seeds.seed_data import load_seed_data


def main() -> int:
    app = create_app()
    all_blocked = True

    with app.app_context():
        # (a) Initialize the app and database, and load seed data so a
        # valid actor_id / change_request_id exist (FK enforcement is on).
        db.create_all()
        load_seed_data()

        # (b) Create an audit record via the real service.
        audit_log = AuditService.log_action(
            actor_id=1,
            change_request_id=1,
            action="test_action",
            from_state="draft",
            to_state="submitted",
            detail_json={"purpose": "immutability test"},
        )

        # (c)/(d)/(e) Attempt to UPDATE it.
        audit_log.action = "tampered"
        try:
            db.session.commit()
            print("✗ AuditLog UPDATE was NOT blocked")
            all_blocked = False
        except ValueError as exc:
            db.session.rollback()
            print(f"✓ AuditLog UPDATE blocked: {exc}")

        # (f)/(g)/(h) Attempt to DELETE it.
        db.session.delete(audit_log)
        try:
            db.session.commit()
            print("✗ AuditLog DELETE was NOT blocked")
            all_blocked = False
        except ValueError as exc:
            db.session.rollback()
            print(f"✓ AuditLog DELETE blocked: {exc}")

        # (i) Same two checks for AIExtractionLog.
        extraction_log = AIExtractionLog(
            change_request_id=1,
            model="anthropic.claude-3-5-sonnet",
            model_version="20241022",
            prompt_text="Extract impact and stakeholders from this change request.",
            raw_response_json={"stakeholders": []},
            confidence=0.92,
            latency_ms=850,
        )
        db.session.add(extraction_log)
        db.session.commit()

        extraction_log.confidence = 0.10
        try:
            db.session.commit()
            print("✗ AIExtractionLog UPDATE was NOT blocked")
            all_blocked = False
        except ValueError as exc:
            db.session.rollback()
            print(f"✓ AIExtractionLog UPDATE blocked: {exc}")

        db.session.delete(extraction_log)
        try:
            db.session.commit()
            print("✗ AIExtractionLog DELETE was NOT blocked")
            all_blocked = False
        except ValueError as exc:
            db.session.rollback()
            print(f"✓ AIExtractionLog DELETE blocked: {exc}")

    return 0 if all_blocked else 1


if __name__ == "__main__":
    sys.exit(main())
