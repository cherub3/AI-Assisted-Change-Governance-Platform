"""
End-to-end demo: Draft → Submit → Confirm → Score → Approve
"""
import sys

# Windows consoles often default stdout to cp1252, which cannot encode the
# arrow/checkmark characters used below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import create_app, db
from app.models import User, ChangeRequest, Stakeholder, ChangeRequestStatus, ChangeRequestPriority, AuditLog
from app.services import WorkflowService, RiskEngine

app = create_app()

with app.app_context():
    # Load seed users
    requester = User.query.filter_by(name="Alice").first()
    approver = User.query.filter_by(name="Bob").first()

    print("\n" + "="*70)
    print("AI-Assisted Change Governance Platform - Full Workflow Demo")
    print("="*70)

    # 1. CREATE
    print("\n[1] CREATE: Draft change request")
    cr = ChangeRequest(
        submitter_id=requester.id,
        title="Implement KYC Verification",
        description="Add KYC check before account activation",
        priority=ChangeRequestPriority.HIGH,
        department="Operations",
        status=ChangeRequestStatus.DRAFT
    )
    db.session.add(cr)
    db.session.commit()
    print(f"    Status: {cr.status.value}")

    # 2. SUBMIT
    print("\n[2] SUBMIT: Change request submitted")
    WorkflowService.submit(cr.id, requester.id)
    cr = db.session.get(ChangeRequest, cr.id)
    print(f"    Status: {cr.status.value}")

    # 3. EXTRACT (mock - manually confirm stakeholders)
    print("\n[3] EXTRACT: AI extracts stakeholders (mocked with seed data)")
    db.session.add(Stakeholder(change_request_id=cr.id, name="Operations Team", email="ops@bank.com", confirmed=False))
    db.session.add(Stakeholder(change_request_id=cr.id, name="Compliance Officer", email="compliance@bank.com", confirmed=False))
    db.session.add(Stakeholder(change_request_id=cr.id, name="Risk Team", email="risk@bank.com", confirmed=False))
    db.session.commit()
    print(f"    Stakeholders extracted: {len(cr.stakeholders)}")

    # 4. CONFIRM EXTRACTION
    print("\n[4] CONFIRM EXTRACTION: Human reviewed and confirmed")
    cr.status = ChangeRequestStatus.EXTRACTION_PENDING
    for s in cr.stakeholders:
        s.confirmed = True
    db.session.commit()
    WorkflowService.confirm_extraction(cr.id, requester.id)
    cr = db.session.get(ChangeRequest, cr.id)
    print(f"    Status: {cr.status.value}")

    # 5. SCORE
    print("\n[5] SCORE: RiskEngine evaluates")
    result = RiskEngine.assess_risk(cr.id)
    cr = db.session.get(ChangeRequest, cr.id)
    print(f"    Risk Score: {result['score_value']}")
    print(f"    Risk Tier: {result['tier']}")
    print(f"    Rules Fired: {', '.join([r['rule_name'] for r in result['rules_fired']])}")
    print(f"    Status: {cr.status.value}")

    # 6. APPROVE
    print("\n[6] APPROVE: Approver grants approval")
    WorkflowService.approve(cr.id, approver.id, comment="Reviewed and approved")
    cr = db.session.get(ChangeRequest, cr.id)
    print(f"    Status: {cr.status.value}")

    # AUDIT TRAIL
    print("\n" + "-"*70)
    print("AUDIT TRAIL (Immutable)")
    print("-"*70)
    audit_events = db.session.query(AuditLog).filter_by(change_request_id=cr.id).order_by(AuditLog.created_at).all()
    for i, event in enumerate(audit_events, 1):
        print(f"  {i}. {event.action:20} | {event.from_state:20} → {event.to_state:20}")

    # RISK SCORE HISTORY
    print("\n" + "-"*70)
    print("RISK SCORE HISTORY (Versioned)")
    print("-"*70)
    from app.models import RiskScore
    risk_scores = db.session.query(RiskScore).filter_by(change_request_id=cr.id).order_by(RiskScore.version).all()
    for rs in risk_scores:
        print(f"  Version {rs.version}: Score={rs.score_value}, Tier={rs.tier.value}")

    print("\n" + "="*70)
    print("✓ Complete governance workflow executed successfully")
    print("="*70 + "\n")
