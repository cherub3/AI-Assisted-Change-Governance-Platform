# AI-Assisted Change Governance Platform

A change-request governance system where every decision is auditable,
every risk score is explainable, and the audit trail cannot be altered
after the fact — by convention or by code.

## Key Features

- **Immutable audit trail** — insert-only at the ORM level, not convention.
- **Segregation of duties** — a submitter can never approve/reject their
  own request; violations are still logged.
- **Deterministic risk scoring** — fixed rules, no randomness, no AI.
- **Transactional atomicity** — state change and audit record commit or
  roll back together.
- **FK enforcement** — off by default in SQLite; turned on explicitly
  and verified.

## Governance Controls

| Control | Implementation | Verification |
|---|---|---|
| Immutable audit trail | `app/events.py` — `before_update`/`before_delete` listeners on `AuditLog`, `AIExtractionLog` raise `ValueError` | `test_audit_immutability.py` |
| Segregation of duties | `WorkflowService.approve()`/`.reject()` reject `actor_id == submitter_id`, logging `sod_violation` independently | `app/services/workflow_service.py`, exercised in `demo_workflow.py` |
| Deterministic scoring | `RiskEngine.assess_risk()` — fixed `RULES` dict, explicit `if` checks | `demo_workflow.py` (fixed inputs → score 85) |
| Atomic state + audit | One `db.session.commit()` per transition; failure rolls back both | `app/services/workflow_service.py`, `risk_engine.py` |
| FK referential integrity | `PRAGMA foreign_keys=ON` via SQLAlchemy `connect` event, `app/__init__.py` | `test_fk_enforcement.py` |

## Architecture (State Machine)

```
Draft --submit()--> Submitted --[ExtractionService, Phase 4]--> ExtractionPending
ExtractionPending --confirm_extraction()--> ReadyForScoring
ReadyForScoring --RiskEngine.assess_risk()--> PendingApproval
PendingApproval --approve()--> Approved
PendingApproval --reject()--> Rejected
```

## Risk Scoring Rules

| Rule | Condition | Points |
|---|---|---|
| R001 | `priority == HIGH` | +40 |
| R002 | 3+ stakeholders on the request | +20 |
| R003 | Any stakeholder name contains "compliance" | +25 |

Capped at 100. Tier: **manager** (0–59) or **manager_pmo** (60+).

## Demo

```bash
python -m app.database      # creates change_governance.db, loads seed data
python demo_workflow.py     # Draft → Submit → Confirm → Score → Approve
```
Expect status transitions at each step, a risk score of 85
(`manager_pmo`), and a full immutable audit trail + versioned risk
history printed at the end.

## Database Schema

7 tables: `users`, `change_requests`, `stakeholders`, `approval_tasks`,
`risk_scores`, `audit_logs`, `ai_extraction_logs`. `risk_scores` is
versioned — recalculation inserts, never overwrites. `audit_logs`/
`ai_extraction_logs` have no `updated_at`: append-only by design.

## Tech Stack

Flask · SQLAlchemy 2.0 (Flask-SQLAlchemy) · SQLite · python-dotenv ·
boto3 (reserved, unused until Phase 4)

## Testing & Verification

`test_fk_enforcement.py`, `test_audit_immutability.py` — executable
governance proofs. `demo_workflow.py` — end-to-end happy path. No
automated pytest suite yet (Phase 5).

## Interview Talking Points

- Immutability enforced by mapper events, proven with a negative
  control: disable it, watch the test fail.
- SoD is a service-layer invariant, not a UI checkbox.
- Risk scoring is deterministic and versioned; recalculation never
  destroys history.
- Audit writes share a transaction with the change they describe.
- SQLite disables FK enforcement by default — found and closed before
  it became a silent integrity bug.

## Future Work

`ExtractionService` (Bedrock), `ApprovalTask`-based multi-tier routing
(unused today), RBAC/auth, API routes, pytest suite, dashboards.

## Current Status: 8.5/10

Governance core — atomicity, immutability, SoD, deterministic scoring,
FK integrity — is implemented and proven by executable verification.
Held back: no API/auth layer, `ApprovalTask` is schema-only, AI
extraction is still a stub, verification is manual scripts not a suite.
