# Architecture

## Request Lifecycle

```
Draft --submit()--> Submitted --[ExtractionService, Phase 4]--> ExtractionPending
ExtractionPending --confirm_extraction()--> ReadyForScoring
ReadyForScoring --RiskEngine.assess_risk()--> PendingApproval
PendingApproval --approve()--> Approved
PendingApproval --reject()--> Rejected
```

`Submitted → ExtractionPending` has no automated transition yet —
`ExtractionService.extract()` is a `NotImplementedError` stub
(`app/services/extraction_service.py`); `demo_workflow.py` sets that
status manually to simulate it.

## Control Points

| Control | Location | Verified by |
|---|---|---|
| FK enforcement | `app/__init__.py` — `PRAGMA foreign_keys=ON` on the SQLAlchemy `connect` event | `test_fk_enforcement.py` |
| Audit immutability | `app/events.py` — `before_update`/`before_delete` on `AuditLog`, `AIExtractionLog` | `test_audit_immutability.py` |
| SoD | `app/services/workflow_service.py` — `approve()`/`reject()` check `actor_id == submitter_id` | `demo_workflow.py` |
| Atomicity | `workflow_service.py`, `risk_engine.py` — status write + `AuditService.log_action(..., auto_commit=False)` in one `commit()` | Exception path rolls back both (manually exercised) |

## Data Model

7 tables: `users`, `change_requests`, `stakeholders`, `approval_tasks`,
`risk_scores`, `audit_logs`, `ai_extraction_logs`. `approval_tasks` is
schema-complete and FK-enforced but not yet written to —
`WorkflowService` mutates `ChangeRequest.status` directly rather than
creating `ApprovalTask` rows; multi-tier routing is future work.
`audit_logs`/`ai_extraction_logs` skip `BaseModel` (no `updated_at`).

## Key Design Decisions

- **`RiskScore` is one-to-many, not one-to-one.** Recalculation inserts a
  new `version` row; history is never overwritten, so a disputed score
  is always reconstructable.
- **Audit listeners live in mapper events, not service-layer discipline.**
  Convention drifts; a `before_update`/`before_delete` hook that raises
  cannot be bypassed by a future contributor who forgets the rule.
- **`auto_commit` flag on `AuditService.log_action()`.** SoD-violation
  logs must survive a rejected transaction, so they commit independently;
  successful-transition logs must die with a failed transaction, so they
  flush into the caller's pending commit instead.
