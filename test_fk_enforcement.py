"""Phase 1 verification: confirm SQLite foreign key constraints are enforced.

Run with:
    python test_fk_enforcement.py

Exits 0 and prints a confirmation line if FK enforcement is active and an
invalid insert is correctly rejected. Exits 1 with a clear failure message
otherwise.
"""

import sys

# Windows consoles often default stdout to cp1252, which cannot encode the
# checkmark/cross characters below. Force UTF-8 so the required output
# strings print correctly regardless of host console codepage.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models.approval_task import ApprovalTask, ApprovalTaskStatus
from seeds.seed_data import load_seed_data

INVALID_APPROVER_ID = 999  # does not exist in the users table


def main() -> int:
    app = create_app()

    with app.app_context():
        # (a) Initialize the database.
        db.create_all()

        # (b) Load seed data, so we know valid user/change-request IDs exist
        # (seed change request id=1, submitted by seed user id=1).
        load_seed_data()

        # (c) Confirm the pragma is actually ON for this connection.
        pragma_value = db.session.execute(text("PRAGMA foreign_keys")).scalar()
        print(f"PRAGMA foreign_keys = {pragma_value}")
        if pragma_value != 1:
            print("✗ FK enforcement is NOT enabled (PRAGMA foreign_keys != 1). Test FAILED.")
            return 1

        # (d)+(e) Attempt to insert an ApprovalTask with an invalid approver_id.
        bad_task = ApprovalTask(
            change_request_id=1,
            approver_id=INVALID_APPROVER_ID,
            status=ApprovalTaskStatus.PENDING,
        )
        db.session.add(bad_task)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # (f)
            print("✓ FK constraint ENFORCED: Cannot insert ApprovalTask with invalid approver_id")
            return 0
        else:
            print(
                "✗ FK constraint NOT enforced: ApprovalTask with approver_id="
                f"{INVALID_APPROVER_ID} was inserted successfully. Test FAILED."
            )
            return 1


if __name__ == "__main__":
    sys.exit(main())
