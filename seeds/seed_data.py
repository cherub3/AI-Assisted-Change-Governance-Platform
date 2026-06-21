"""Seed data for local development.

Loaded by app/database.py on `python -m app.database`. Idempotent: if any
user already exists, assumes seeding already happened and does nothing.
"""

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.change_request import ChangeRequest, ChangeRequestPriority, ChangeRequestStatus
from app.models.user import User, UserRole

SEED_PASSWORD = "changeme123"  # noqa: S105 — local dev seed data only, never used in production


def load_seed_data() -> None:
    """Insert 3 seed users and 1 seed draft change request, if not already present."""
    if User.query.first() is not None:
        print("Seed data already present. Skipping.")
        return

    alice = User(
        name="Alice",
        email="alice@example.com",
        password_hash=generate_password_hash(SEED_PASSWORD),
        role=UserRole.REQUESTER,
    )
    bob = User(
        name="Bob",
        email="bob@example.com",
        password_hash=generate_password_hash(SEED_PASSWORD),
        role=UserRole.APPROVER,
    )
    admin = User(
        name="Admin",
        email="admin@example.com",
        password_hash=generate_password_hash(SEED_PASSWORD),
        role=UserRole.ADMIN,
    )
    db.session.add_all([alice, bob, admin])
    db.session.flush()  # assign primary keys before referencing alice.id below

    change_request = ChangeRequest(
        submitter_id=alice.id,
        title="Add KYC Verification",
        description="Implement KYC check before account activation",
        priority=ChangeRequestPriority.HIGH,
        department="Operations",
        status=ChangeRequestStatus.DRAFT,
    )
    db.session.add(change_request)
    db.session.commit()
