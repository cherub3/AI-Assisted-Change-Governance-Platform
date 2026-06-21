"""Deterministic risk scoring engine.

Pure deterministic logic only: the same ChangeRequest + Stakeholder state
always produces the same score, tier, and rules_fired list. Has no
dependency on Bedrock or any AI service — RiskEngine only ever reads
human-confirmed data (ChangeRequest.priority, confirmed Stakeholder rows),
never raw, unconfirmed AI extraction output.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import func

from app.extensions import db
from app.models.change_request import ChangeRequest, ChangeRequestPriority, ChangeRequestStatus
from app.models.risk_score import RiskScore, RiskTier
from app.services.audit_service import AuditService

# Rule configuration. Each rule is a flat (name, points) pair — the
# conditions that decide whether a rule fires live as explicit `if`
# statements in assess_risk(), not as code embedded in this dict.
RULES: Dict[str, Dict[str, Any]] = {
    "R001": {"name": "High Priority", "points": 40},
    "R002": {"name": "Three Or More Stakeholders", "points": 20},
    "R003": {"name": "Compliance Stakeholder", "points": 25},
}

MAX_SCORE = 100
MANAGER_PMO_THRESHOLD = 60  # score >= this tier escalates to "manager_pmo"


def get_system_actor() -> int:
    """Return the system actor ID for RiskEngine audit events."""
    from app.config import SYSTEM_ACTOR_ID

    return SYSTEM_ACTOR_ID


class RiskEngine:
    """Calculates risk scores from confirmed change-request data using configurable rules."""

    @staticmethod
    def assess_risk(change_request_id: int) -> Dict[str, Any]:
        """Run the deterministic risk calculation for a change request.

        Persists a new RiskScore row with an incremented `version` —
        existing RiskScore rows for this change request are never modified
        — and transitions the change request to PendingApproval.

        Args:
            change_request_id: ID of the change request to score.

        Returns:
            A dict with score_value, tier, rules_fired, and version.

        Raises:
            ValueError: If the change request does not exist, is not
                currently in the ReadyForScoring state, has no stakeholders,
                or has stakeholders that are not all confirmed.
        """
        # 1. Load the ChangeRequest with all related Stakeholders.
        change_request = db.session.get(ChangeRequest, change_request_id)
        if change_request is None:
            raise ValueError(f"ChangeRequest {change_request_id} not found.")

        # 2. Validate preconditions.
        if change_request.status != ChangeRequestStatus.READY_FOR_SCORING:
            raise ValueError(
                f"Cannot score change request in state '{change_request.status.value}'. "
                f"Expected '{ChangeRequestStatus.READY_FOR_SCORING.value}'."
            )

        stakeholders = change_request.stakeholders
        if not stakeholders:
            raise ValueError("Cannot score change request with no stakeholders.")
        if any(not stakeholder.confirmed for stakeholder in stakeholders):
            raise ValueError("Cannot score change request. All stakeholders must be confirmed.")

        # 3. Score calculation.
        score = 0
        rules_fired: List[Dict[str, Any]] = []

        if change_request.priority == ChangeRequestPriority.HIGH:
            score += RULES["R001"]["points"]
            rules_fired.append(
                {
                    "rule_id": "R001",
                    "rule_name": RULES["R001"]["name"],
                    "points": RULES["R001"]["points"],
                }
            )

        if len(stakeholders) >= 3:
            score += RULES["R002"]["points"]
            rules_fired.append(
                {
                    "rule_id": "R002",
                    "rule_name": RULES["R002"]["name"],
                    "points": RULES["R002"]["points"],
                }
            )

        if any("compliance" in stakeholder.name.lower() for stakeholder in stakeholders):
            score += RULES["R003"]["points"]
            rules_fired.append(
                {
                    "rule_id": "R003",
                    "rule_name": RULES["R003"]["name"],
                    "points": RULES["R003"]["points"],
                }
            )

        # 4. Cap score at 100.
        score = min(score, MAX_SCORE)

        # 5. Determine tier based on score.
        if score >= MANAGER_PMO_THRESHOLD:
            tier = RiskTier.MANAGER_PMO
        else:
            tier = RiskTier.MANAGER

        # 7. version: auto-increment per change_request_id.
        previous_max_version = (
            db.session.query(func.max(RiskScore.version))
            .filter(RiskScore.change_request_id == change_request_id)
            .scalar()
        )
        version = (previous_max_version or 0) + 1

        try:
            risk_score = RiskScore(
                change_request_id=change_request_id,
                version=version,
                score_value=score,
                tier=tier,
                rules_fired_json=rules_fired,
                calculated_at=datetime.now(timezone.utc),
            )
            db.session.add(risk_score)

            # 8. Update ChangeRequest.status (same transaction).
            change_request.status = ChangeRequestStatus.PENDING_APPROVAL

            # 9. Audit (same transaction).
            AuditService.log_action(
                get_system_actor(),
                change_request_id,
                "score",
                ChangeRequestStatus.READY_FOR_SCORING.value,
                ChangeRequestStatus.PENDING_APPROVAL.value,
                {"score": score, "tier": tier.value, "rules_fired": rules_fired},
                auto_commit=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # 10. Return.
        return {
            "score_value": score,
            "tier": tier.value,
            "rules_fired": rules_fired,
            "version": version,
        }
