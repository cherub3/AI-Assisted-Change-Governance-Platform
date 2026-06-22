# AI-Assisted Change Governance Platform

<<<<<<< HEAD
## Executive Summary
=======
An enterprise governance workflow system designed to manage operational change requests with immutable audit logging, segregation-of-duties controls, deterministic risk scoring, and human-in-the-loop approvals.
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

This project demonstrates an AI-assisted change governance workflow designed for regulated environments. Change requests move through controlled workflow states, AI-generated stakeholder suggestions are subject to mandatory human review, risk decisions are versioned, and every action is recorded in an immutable audit trail.

<<<<<<< HEAD
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
=======
- **Immutable Append-Only Audit Trail** — Enforced through SQLAlchemy event listeners; every state transition is logged and cannot be modified
- **Segregation of Duties (SoD)** — Submitters cannot approve their own requests; violations are logged even when rejected
- **Deterministic Risk Engine** — Versioned risk history; re-scoring creates new records, preserving audit trail
- **Atomic Transactions** — Workflow transitions and audit events are atomic; rollback protection ensures no partial state
- **Foreign Key Enforcement** — Relational integrity verified through PRAGMA enforcement and execution testing
- **End-to-End Workflow** — Draft → Submitted → Extraction Pending → Ready For Scoring → Pending Approval → Approved/Rejected
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

## Governance Controls

| Control | Implementation | Verification |
<<<<<<< HEAD
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
=======
|---------|---|---|
| **Immutable Audit Logs** | SQLAlchemy before_update/before_delete event listeners | Negative-control testing: UPDATE/DELETE blocked even on direct db calls |
| **Foreign Keys** | PRAGMA foreign_keys=ON + db constraints | Negative-control testing: FK violation raises IntegrityError |
| **SoD Enforcement** | approver_id ≠ submitter_id check in approve()/reject() | Violations logged to AuditLog before exception raised |
| **Atomicity** | db.session transaction context | Rollback verified: forced failure during audit write rolls back status change |
| **Versioning** | RiskScore.version = MAX(version)+1 | History preserved; no overwrites |

## Architecture

### State Machine

```
Draft
  ├─ submit() → Submitted
  │
  ├─ extract() → ExtractionPending
  │
  ├─ confirm_extraction() → ReadyForScoring
  │
  ├─ assess_risk() → PendingApproval
  │
  ├─ approve() → Approved
  └─ reject() → Rejected
```

### Risk Scoring Rules

| Rule | Condition | Points | Justification |
|------|-----------|--------|---|
| R001 | Priority = HIGH | +40 | High-priority changes need elevated scrutiny |
| R002 | 3+ Stakeholders | +20 | Complexity increases with stakeholder count |
| R003 | Compliance Stakeholder | +25 | Compliance involvement requires manager+PMO review |

**Tier Determination**: 0-59 → manager, 60+ → manager_pmo
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

## Demo

Run end-to-end workflow:

```bash
<<<<<<< HEAD
python -m app.database      # creates change_governance.db, loads seed data
python demo_workflow.py     # runs the full lifecycle below
```
=======
python demo_workflow.py
```

Shows:
- Full 6-stage workflow (Draft → Approved)
- Immutable audit trail with 4 events
- Risk score versioning
- Segregation of Duties enforcement
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

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

<<<<<<< HEAD
7 tables: `users`, `change_requests`, `stakeholders`, `approval_tasks`,
`risk_scores`, `audit_logs`, `ai_extraction_logs`. `risk_scores` is
versioned — recalculation inserts, never overwrites. `audit_logs` and
`ai_extraction_logs` are append-only (no `updated_at`). `approval_tasks`
exists in the schema and is foreign-key enforced, but is not yet written
to by `WorkflowService` — see Current Status.
=======
**7 Tables**
- `users` — workflow actors (requester, approver, admin)
- `change_requests` — core aggregate (id, title, priority, status, etc.)
- `stakeholders` — people/teams involved (human-confirmable)
- `approval_tasks` — approval records
- `risk_scores` — versioned decisions (never overwritten)
- `audit_logs` — immutable event stream (INSERT-only at ORM)
- `ai_extraction_logs` — AI decision evidence (INSERT-only at ORM)

**Key Design Decisions**
- `RiskScore` is versioned; re-scoring creates version 2, version 1 survives
- `AuditLog` and `AIExtractionLog` are protected by event listeners (no UPDATE/DELETE possible)
- `Stakeholder.confirmed=False` until human reviews Bedrock extraction
- `AuditService` is the only code path that writes to audit logs
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

### Testing & Verification

<<<<<<< HEAD
`test_fk_enforcement.py` and `test_audit_immutability.py` are executable
proofs, each including a negative control (the protection is temporarily
disabled to confirm the test actually fails without it). `demo_workflow.py`
exercises the full happy-path lifecycle, including AI extraction. There is
no automated pytest suite yet — see Current Status.
=======
- **Framework**: Flask 3.0+
- **ORM**: SQLAlchemy 2.0+
- **Database**: SQLite (development)
- **Governance**: Transaction management, event listeners, enum constraints
- **Future**: AWS Bedrock (Claude 3.5 Sonnet) for AI extraction
>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e

## Screenshots

<<<<<<< HEAD
*Pending capture — referenced here as planned documentation, not yet
present in the repository.*

- `docs/screenshots/demo-workflow.png` — full lifecycle run, Draft → Approved
- `docs/screenshots/risk-score.png` — RiskEngine output and rules fired
- `docs/screenshots/audit-trail.png` — immutable audit log for a completed request
=======
**Phase 1 Controls** (Committed)
```bash
python test_fk_enforcement.py    # PRAGMA foreign_keys enforced
python test_audit_immutability.py # UPDATE/DELETE blocked on audit logs
```

**Phase 2 Controls** (Integrated in demo)
```bash
python demo_workflow.py           # Full workflow + SoD + atomicity
```

## Interview Talking Points

1. **Governance-First Design** — Built around controls (SoD, audit, immutability) before features
2. **Verified Controls** — Not assumed; tested through negative-control verification (disable control → test fails, re-enable → test passes)
3. **Atomic Transactions** — State changes and audit records are atomic; no partial state possible
4. **Versioned Decisions** — Risk scores are immutable history, enabling compliance audits and decision replay
5. **Separation of Concerns** — Audit service, workflow service, risk engine are loosely coupled; easy to test in isolation

## Future Work (Phase 4+)

- **Bedrock Integration** — AI extraction of change type, affected systems, impact summary with human review gate
- **Test Suite** — 50+ unit and integration tests
- **Dynamic Rules** — RiskRule configuration table (currently hardcoded)
- **Reporting** — PMO dashboard, SLA tracking, audit reporting

## Current Status

**Complete**: Foundation, Workflow, Risk Scoring, Audit Spine, Governance Controls
**In Progress**: Bedrock Integration
**Rating**: 8.5/10 for Deutsche Bank BA/PMO apprenticeship

---

*Final-year B.Tech portfolio project demonstrating enterprise governance concepts: auditability, immutability, segregation of duties, and deterministic decision-making.*
```

---

## **Architecture Diagram (Simple)**

Create `docs/ARCHITECTURE.md`:

```markdown
# Architecture

## Request Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│ Change Request (Draft)                                  │
│ - title, description, priority, department              │
└────────────────────────┬────────────────────────────────┘
                         │
                    submit()
                         ↓
        ┌────────────────────────────────┐
        │ AuditService.log_action()      │
        │ "action: submit"               │
        │ "draft → submitted"            │
        └────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Workflow State = Submitted                              │
└────────────────────────┬────────────────────────────────┘
                         │
                  extract() [Bedrock]
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Stakeholders Created (unconfirmed)                       │
│ AIExtractionLog stored (immutable)                      │
└────────────────────────┬────────────────────────────────┘
                         │
              confirm_extraction()
                         ↓
        ┌────────────────────────────────┐
        │ AuditService.log_action()      │
        │ "action: confirm_extraction"   │
        │ "extraction_pending → ready"   │
        └────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ RiskEngine.assess_risk()                                │
│ - Evaluate rules: HIGH priority (+40), stakeholders... │
│ - Calculate score, determine tier, store versioned      │
│ - RiskScore row created (version=1)                     │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────────────────────┐
        │ AuditService.log_action()      │
        │ "action: score"                │
        │ "ready_for_scoring →pending"   │
        │ detail: {score, tier, rules}   │
        └────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Pending Approval (Risk Tier = manager_pmo)              │
│ Route: Requires manager + PMO approval                  │
└────────────────────────┬────────────────────────────────┘
                         │
                  approve() or reject()
                         │
              [SoD Check: approver ≠ submitter]
                         │
        If violation: AuditService.log_action("sod_violation")
              Then: raise ValueError()
                         │
        If SoD passes:
        ┌────────────────────────────────┐
        │ AuditService.log_action()      │
        │ "action: approve"              │
        │ "pending_approval → approved"  │
        └────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Final Status = Approved (or Rejected)                   │
│                                                         │
│ Audit Trail: 4 immutable events                         │
│ Risk Score: version 1 (versioned, preserved)            │
│ SoD Violations: logged (even if rejected)               │
└─────────────────────────────────────────────────────────┘
```

## Control Points

| Control | Location | Verification |
|---------|----------|---|
| FK Enforcement | `app/__init__.py:41` (PRAGMA foreign_keys) | `test_fk_enforcement.py` ✓ |
| Immutable Audit | `app/events.py` (event listeners) | `test_audit_immutability.py` ✓ |
| SoD Enforcement | `WorkflowService.approve()/reject()` | Demo workflow ✓ |
| Atomicity | `db.session.begin()` context | Rollback tested (forced Bedrock failure) ✓ |
| Versioning | `RiskEngine.assess_risk()` | Demo shows version=1 ✓ |
```

---

## **Resume Bullets (Ready to Copy)**

```
AI-Assisted Change Governance Platform | Python, Flask, SQLAlchemy, SQLite

• Engineered a governance workflow platform with immutable append-only audit logging, foreign-key enforcement, 
  and segregation-of-duties controls across 7 relational entities, enforced through SQLAlchemy event listeners.

• Implemented a transactional state machine managing change requests through submission, risk assessment, 
  approval, and rejection workflows with rollback protection and audit traceability.

• Built a versioned deterministic risk-scoring engine evaluating stakeholder complexity, compliance involvement, 
  and request priority to route approvals and preserve historical scoring decisions (version history).

• Verified governance controls through negative-control testing: FK constraints, immutability, and atomicity 
  proven via execution testing, not assumptions.

• Designed for separation of duties: submitters cannot approve their own requests; violations logged and rejected 
  (audit trail for compliance review).
```

>>>>>>> 6ee91c621db33fe635e0e07380ade3ef7f26435e
