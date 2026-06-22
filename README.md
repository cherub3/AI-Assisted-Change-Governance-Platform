# AI-Assisted Change Governance Platform

An enterprise governance workflow system designed to manage operational change requests with immutable audit logging, segregation-of-duties controls, deterministic risk scoring, and human-in-the-loop approvals.

## Key Features

- **Immutable Append-Only Audit Trail** — Enforced through SQLAlchemy event listeners; every state transition is logged and cannot be modified
- **Segregation of Duties (SoD)** — Submitters cannot approve their own requests; violations are logged even when rejected
- **Deterministic Risk Engine** — Versioned risk history; re-scoring creates new records, preserving audit trail
- **Atomic Transactions** — Workflow transitions and audit events are atomic; rollback protection ensures no partial state
- **Foreign Key Enforcement** — Relational integrity verified through PRAGMA enforcement and execution testing
- **End-to-End Workflow** — Draft → Submitted → Extraction Pending → Ready For Scoring → Pending Approval → Approved/Rejected

## Governance Controls

| Control | Implementation | Verification |
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

## Demo

Run end-to-end workflow:

```bash
python demo_workflow.py
```

Shows:
- Full 6-stage workflow (Draft → Approved)
- Immutable audit trail with 4 events
- Risk score versioning
- Segregation of Duties enforcement

## Database Schema

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

## Tech Stack

- **Framework**: Flask 3.0+
- **ORM**: SQLAlchemy 2.0+
- **Database**: SQLite (development)
- **Governance**: Transaction management, event listeners, enum constraints
- **Future**: AWS Bedrock (Claude 3.5 Sonnet) for AI extraction

## Testing & Verification

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

