"""AI extraction service, wrapping AWS Bedrock.

STUB ONLY in Phase 1 — implemented in Phase 4.

GOVERNANCE RULE to enforce when implemented: extraction output is always
staged as unconfirmed Stakeholder / impact data for human review and
correction. Nothing produced here may be consumed by RiskEngine until a
human has confirmed it via WorkflowService.confirm_extraction(). Every call
to Bedrock — prompt, raw response, model + version, confidence, latency —
must be written to ai_extraction_logs, regardless of success or failure.
"""


class ExtractionService:
    """Calls Bedrock to extract impact and stakeholders from a change request."""

    @staticmethod
    def extract(change_request_id: int) -> None:
        """Call Bedrock and store the result in ai_extraction_logs."""
        raise NotImplementedError("Phase 4")
