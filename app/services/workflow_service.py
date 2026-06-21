"""Workflow state-machine service.

Owns every ChangeRequest status transition. GOVERNANCE RULES enforced here:

- Segregation of duties: an approver/rejecter may never act on a change
  request they themselves submitted (actor_id != submitter_id).
- Every successful transition writes an audit record in the same database
  transaction as the status change — they commit together or roll back
  together, so the audit trail can never drift from the actual state.
- A logged SoD violation attempt is the one exception: it must persist even
  though the state change it describes is rejected, so it is committed
  independently, before the ValueError is raised.
"""

from typing import Optional

from app.extensions import db
from app.models.change_request import ChangeRequest, ChangeRequestStatus
from app.models.stakeholder import Stakeholder
from app.services.audit_service import AuditService


class WorkflowService:
    """Owns all change-request state transitions."""

    @staticmethod
    def submit(change_request_id: int, actor_id: int) -> ChangeRequest:
        """Transition a change request from Draft to Submitted.

        Args:
            change_request_id: ID of the change request to submit.
            actor_id: ID of the user performing the submission.

        Returns:
            The updated ChangeRequest.

        Raises:
            ValueError: If the change request does not exist, or is not
                currently in the Draft state.
        """
        change_request = db.session.get(ChangeRequest, change_request_id)
        if change_request is None:
            raise ValueError(f"ChangeRequest {change_request_id} not found.")

        if change_request.status != ChangeRequestStatus.DRAFT:
            raise ValueError(
                f"Cannot submit change request in state '{change_request.status.value}'. "
                f"Expected '{ChangeRequestStatus.DRAFT.value}'."
            )

        try:
            change_request.status = ChangeRequestStatus.SUBMITTED
            AuditService.log_action(
                actor_id,
                change_request_id,
                "submit",
                ChangeRequestStatus.DRAFT.value,
                ChangeRequestStatus.SUBMITTED.value,
                {},
                auto_commit=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return change_request

    @staticmethod
    def confirm_extraction(change_request_id: int, actor_id: int) -> ChangeRequest:
        """Transition a change request from ExtractionPending to ReadyForScoring.

        Args:
            change_request_id: ID of the change request to confirm.
            actor_id: ID of the user confirming the extraction (the submitter,
                reviewing AI-extracted stakeholder data).

        Returns:
            The updated ChangeRequest.

        Raises:
            ValueError: If the change request does not exist, is not
                currently in the ExtractionPending state, has no stakeholders,
                or has stakeholders that are not yet all confirmed.
        """
        change_request = db.session.get(ChangeRequest, change_request_id)
        if change_request is None:
            raise ValueError(f"ChangeRequest {change_request_id} not found.")

        if change_request.status != ChangeRequestStatus.EXTRACTION_PENDING:
            raise ValueError(
                f"Cannot confirm extraction in state '{change_request.status.value}'. "
                f"Expected '{ChangeRequestStatus.EXTRACTION_PENDING.value}'."
            )

        stakeholders = Stakeholder.query.filter_by(change_request_id=change_request_id).all()
        if not stakeholders:
            raise ValueError("Cannot confirm extraction. No stakeholders found.")
        if any(not stakeholder.confirmed for stakeholder in stakeholders):
            raise ValueError(
                "Cannot confirm extraction. All stakeholders must be reviewed and confirmed by the submitter."
            )

        try:
            change_request.status = ChangeRequestStatus.READY_FOR_SCORING
            AuditService.log_action(
                actor_id,
                change_request_id,
                "confirm_extraction",
                ChangeRequestStatus.EXTRACTION_PENDING.value,
                ChangeRequestStatus.READY_FOR_SCORING.value,
                {},
                auto_commit=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return change_request

    @staticmethod
    def approve(change_request_id: int, actor_id: int, comment: Optional[str] = None) -> ChangeRequest:
        """Transition a change request from PendingApproval to Approved.

        Args:
            change_request_id: ID of the change request to approve.
            actor_id: ID of the user approving the request.
            comment: Optional approver comment, recorded in the audit detail.

        Returns:
            The updated ChangeRequest.

        Raises:
            ValueError: If the change request does not exist, is not
                currently in the PendingApproval state, or if actor_id is
                the same user who submitted the request (segregation of
                duties violation).
        """
        change_request = db.session.get(ChangeRequest, change_request_id)
        if change_request is None:
            raise ValueError(f"ChangeRequest {change_request_id} not found.")

        if change_request.status != ChangeRequestStatus.PENDING_APPROVAL:
            raise ValueError(
                f"Cannot approve change request in state '{change_request.status.value}'. "
                f"Expected '{ChangeRequestStatus.PENDING_APPROVAL.value}'."
            )

        if actor_id == change_request.submitter_id:
            AuditService.log_action(
                actor_id,
                change_request_id,
                "sod_violation",
                ChangeRequestStatus.PENDING_APPROVAL.value,
                ChangeRequestStatus.PENDING_APPROVAL.value,
                {"attempted_by": actor_id},
                auto_commit=True,
            )
            raise ValueError("Segregation of Duties violation: approver cannot be the submitter.")

        try:
            change_request.status = ChangeRequestStatus.APPROVED
            AuditService.log_action(
                actor_id,
                change_request_id,
                "approve",
                ChangeRequestStatus.PENDING_APPROVAL.value,
                ChangeRequestStatus.APPROVED.value,
                {"approved_by": actor_id, "comment": comment},
                auto_commit=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return change_request

    @staticmethod
    def reject(change_request_id: int, actor_id: int, reason: str) -> ChangeRequest:
        """Transition a change request from PendingApproval to Rejected.

        Args:
            change_request_id: ID of the change request to reject.
            actor_id: ID of the user rejecting the request.
            reason: Required rejection reason, recorded in the audit detail.

        Returns:
            The updated ChangeRequest.

        Raises:
            ValueError: If the change request does not exist, is not
                currently in the PendingApproval state, or if actor_id is
                the same user who submitted the request (segregation of
                duties violation).
        """
        change_request = db.session.get(ChangeRequest, change_request_id)
        if change_request is None:
            raise ValueError(f"ChangeRequest {change_request_id} not found.")

        if change_request.status != ChangeRequestStatus.PENDING_APPROVAL:
            raise ValueError(
                f"Cannot reject change request in state '{change_request.status.value}'. "
                f"Expected '{ChangeRequestStatus.PENDING_APPROVAL.value}'."
            )

        if actor_id == change_request.submitter_id:
            AuditService.log_action(
                actor_id,
                change_request_id,
                "sod_violation",
                ChangeRequestStatus.PENDING_APPROVAL.value,
                ChangeRequestStatus.PENDING_APPROVAL.value,
                {"attempted_by": actor_id},
                auto_commit=True,
            )
            raise ValueError("Segregation of Duties violation: rejecter cannot be the submitter.")

        try:
            change_request.status = ChangeRequestStatus.REJECTED
            AuditService.log_action(
                actor_id,
                change_request_id,
                "reject",
                ChangeRequestStatus.PENDING_APPROVAL.value,
                ChangeRequestStatus.REJECTED.value,
                {"rejected_by": actor_id, "reason": reason},
                auto_commit=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return change_request
