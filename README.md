# AI-Assisted Change Governance Platform

## Executive Summary

This project demonstrates an AI-assisted change governance workflow designed for regulated environments. Change requests move through controlled workflow states, AI-generated stakeholder suggestions are subject to mandatory human review, risk decisions are versioned, and every action is recorded in an immutable audit trail.

The system combines workflow governance, risk assessment, auditability, and human-in-the-loop AI controls to ensure that automated recommendations never become business decisions without review and approval.

## At a Glance

✅ Immutable audit trail
✅ Human-reviewed AI suggestions
✅ Segregation of duties controls
✅ Deterministic risk scoring
✅ Transaction rollback protection
✅ End-to-end verified workflow
✅ AI extraction cannot bypass human approval

## Key Results

* Implemented a complete governance workflow spanning Draft → Submitted → Extraction Pending → Ready for Scoring → Pending Approval → Approved/Rejected.
* Enforced mandatory human review before AI-generated stakeholder suggestions can influence downstream decisions.
* Recorded all workflow transitions, risk decisions, and extraction activities in an immutable audit trail.
* Verified transaction atomicity and rollback behavior under injected failures.
* Demonstrated end-to-end workflow execution with six audited events: submit → extract → stage_extraction → confirm_extraction → score → approve.

## Business Problem

Change approval handled by email threads, meetings, or informal sign-off
creates governance gaps that surface at the worst possible time — during
an audit, an incident review, or a regulatory inquiry:

- **No durable audit trail.** Who approved this, when, and why? If the
  answer lives in someone's inbox or memory, it isn't evidence.
- **Segregation of Duties (SoD) violations.** Without a structural
  control, nothing stops a requester from also being the approver,
  defeating the point of review.
- **Inconsistent risk assessment.** The same change can be judged "low
  risk" or "high risk" depending on who happens to review it that day.
- **Weak traceability for compliance.** Reconstructing a decision after
  the fact often isn't possible if there's no append-only record.

### How this platform addresses it

| Problem | Control |
|---|---|
| No durable audit trail | Every state transition writes an immutable, insert-only audit record |
| SoD violations | Submitter ID is checked against approver ID in code before any approval/rejection is allowed |
| Inconsistent risk assessment | A fixed, versioned rule set scores every request the same way — no discretion, no drift |
| Weak traceability | Risk scores are versioned (never overwritten) and the full audit history is queryable per request |

## Governance Controls

| Control | Implementation | Verification |
|---|---|---|
| Immutable audit trail | `app/events.py` — `before_update`/`before_delete` listeners on `AuditLog`, `AIExtractionLog` raise `ValueError` | `test_audit_immutability.py` |
| Segregation of duties | `WorkflowService.approve()`/`.reject()` reject `actor_id == submitter_id`, logging `sod_violation` independently | `app/services/workflow_service.py`, exercised in `demo_workflow.py` |
| Deterministic scoring | `RiskEngine.assess_risk()` — fixed `RULES` dict, explicit `if` checks | `demo_workflow.py` (fixed rules → reproducible score) |
| Atomic state + audit | One `db.session.commit()` per transition; failure rolls back both | `app/services/workflow_service.py`, `risk_engine.py` |
| FK referential integrity | `PRAGMA foreign_keys=ON` via SQLAlchemy `connect` event, `app/__init__.py` | `test_fk_enforcement.py` |

## How It Works: Request Lifecycle

```
Draft
  │  submit()
  ▼
Submitted
  │  ExtractionService.extract() — calls mock Bedrock
  ▼
ExtractionPending
  │  WorkflowService.stage_extraction() creates stakeholders, then
  │  confirm_extraction() — human confirms AI-suggested stakeholders
  ▼
ReadyForScoring
  │  RiskEngine.assess_risk()  — deterministic scoring
  ▼
PendingApproval
  │  approve()              │  reject()
  ▼                         ▼
Approved                 Rejected
```

Extraction is automated end-to-end: `ExtractionService.extract()` calls
mock Bedrock, and `WorkflowService.stage_extraction()` creates stakeholders
and transitions the request to `EXTRACTION_PENDING`. States are exactly
the 7 values of `ChangeRequestStatus`. No other states exist in the codebase.

## Demo

```bash
python -m app.database      # creates change_governance.db, loads seed data
python demo_workflow.py     # runs the full lifecycle below
```

```
Draft → Submitted → ExtractionPending → ReadyForScoring → PendingApproval → Approved

[3] EXTRACT: AI extracts stakeholders
    Stakeholders extracted: 2
    Confidence: 0.85
    Status: extraction_pending

[5] SCORE: RiskEngine evaluates
    Risk Score: 65
    Risk Tier: manager_pmo
    Rules Fired: High Priority, Compliance Stakeholder

AUDIT TRAIL (Immutable)
  1. submit               | draft              → submitted
  2. extract              | -                  → -
  3. stage_extraction     | submitted          → extraction_pending
  4. confirm_extraction   | extraction_pending → ready_for_scoring
  5. score                | ready_for_scoring  → pending_approval
  6. approve              | pending_approval   → approved

RISK SCORE HISTORY (Versioned)
  Version 1: Score=65, Tier=manager_pmo

Final status: approved
AIExtractionLog row: Present
```
(Verbatim output from a real run of `demo_workflow.py`.)

## Risk Scoring Rules

| Rule | Condition | Points |
|---|---|---|
| R001 | Priority is HIGH | +40 |
| R002 | 3 or more stakeholders on the request | +20 |
| R003 | Any stakeholder name contains "compliance" | +25 |

Score capped at 100. Tier: **manager** (0–59) or **manager_pmo** (60+).
Every recalculation adds a new version — prior scores are never deleted.

## What This Demonstrates

- Audit immutability enforced by database-level event listeners, not
  developer discipline — proven by disabling it and watching the test
  correctly fail (a negative control, not just a passing assertion).
- Segregation of Duties is a service-layer invariant checked in code on
  every approval/rejection, not a UI checkbox that can be skipped.
- AI-suggested data is structurally blocked from influencing a risk score
  until a human confirms it — the workflow cannot skip this step.
- SQLite disables foreign key enforcement by default — an easy-to-miss
  gap that would have made every FK in the schema decorative. Found and
  closed with an explicit `PRAGMA` and a test that proves it's on.
- Risk scores are versioned, not overwritten, so a disputed score from
  six months ago is always reconstructable exactly as it was calculated.
- Transaction rollback behavior was verified by deliberately forcing a
  failure mid-transition and confirming the status change and its audit
  record rolled back together — never a partial write.

## Current Status

**Implemented:**
- Workflow state machine — `submit()`, `stage_extraction()`,
  `confirm_extraction()`, `approve()`, `reject()`
- Phase 4 (AI extraction) is implemented. Mock mode is production-ready.
  Real AWS Bedrock integration is deferred.
- Immutable audit logging, enforced at the ORM level
- Deterministic, versioned risk scoring
- Segregation of Duties, transaction atomicity, and FK enforcement

**Not Yet Implemented:**
- Real AWS Bedrock integration (mock mode only — see above)
- Multi-level approval routing (`approval_tasks` table exists, unused)
- API layer (no HTTP routes — everything above is exercised via Python)
- UI
- RBAC/authentication enforcement (`User.role` exists, not yet checked)
- Automated regression test suite (current verification is the two
  scripts below plus the manual demo, not a CI-integrated suite)

## Technical Reference

### Tech Stack

Flask · SQLAlchemy 2.0 (Flask-SQLAlchemy) · SQLite · python-dotenv ·
boto3 (dependency present, unused in mock mode — reserved for real
Bedrock integration)

### Database Schema

7 tables: `users`, `change_requests`, `stakeholders`, `approval_tasks`,
`risk_scores`, `audit_logs`, `ai_extraction_logs`. `risk_scores` is
versioned — recalculation inserts, never overwrites. `audit_logs` and
`ai_extraction_logs` are append-only (no `updated_at`). `approval_tasks`
exists in the schema and is foreign-key enforced, but is not yet written
to by `WorkflowService` — see Current Status.

### Testing & Verification

`test_fk_enforcement.py` and `test_audit_immutability.py` are executable
proofs, each including a negative control (the protection is temporarily
disabled to confirm the test actually fails without it). `demo_workflow.py`
exercises the full happy-path lifecycle, including AI extraction. There is
no automated pytest suite yet — see Current Status.

## Screenshots

*Pending capture — referenced here as planned documentation, not yet
present in the repository.*

- `docs/screenshots/demo-workflow.png` — full lifecycle run, Draft → Approved
- `docs/screenshots/risk-score.png` — RiskEngine output and rules fired
- `docs/screenshots/audit-trail.png` — immutable audit log for a completed request
