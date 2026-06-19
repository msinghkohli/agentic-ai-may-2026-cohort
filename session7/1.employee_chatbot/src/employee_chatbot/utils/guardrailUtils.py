import os
import logging
import boto3

logger = logging.getLogger(__name__)

bedrock_runtime = boto3.client("bedrock-runtime")

GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "DRAFT")


class GuardrailBlockedError(BaseException):
    """Raised when a Bedrock Guardrail blocks LLM input or output.

    Intentionally inherits from ``BaseException`` (not ``Exception``) so that
    CrewAI's ``except Exception`` hook wrapper does not swallow it; this lets
    the error propagate out of ``crew.kickoff()`` to the caller. Catch it
    explicitly (``except GuardrailBlockedError``) before any broad
    ``except Exception``.
    """

    def __init__(self, blocked_message: str, source: str):
        self.blocked_message = blocked_message  # guardrail's configured block text
        self.source = source  # "INPUT" or "OUTPUT"
        super().__init__(f"Guardrail blocked {source}: {blocked_message}")


def apply_guardrail_filters(text: str, source: str = "INPUT") -> tuple[str, bool]:
    """
    Apply AWS Bedrock Guardrail to the given text.
    
    Returns:
        tuple: (processed_text, is_blocked)
        processed_text: The text after guardrail application (could be original, masked, or blocked message).
        is_blocked: Boolean indicating if a 'BLOCKED' action was triggered by any policy.
    """
    if not GUARDRAIL_ID:
        return text, False

    try:
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}]
        )

        action = response.get("action")
        processed_text = text
        is_blocked = False

        if action == "GUARDRAIL_INTERVENED":
            outputs = response.get("outputs", [])
            if outputs:
                processed_text = outputs[0].get("text", text)

            # Check assessments to distinguish between Masking and Blocking
            is_blocked = _is_policy_blocked(response)

        return processed_text, is_blocked

    except Exception as e:
        logger.error(f"Error applying guardrail: {str(e)}")
        return text, False

def _is_policy_blocked(response: dict) -> bool:
    """Helper to detect if any guardrail policy resulted in a 'BLOCKED' action."""
    for assessment in response.get("assessments", []):
        for policy_type in ["contentPolicy", "topicPolicy", "wordPolicy", "sensitiveInformationPolicy", "contextualGroundingPolicy"]:
            policy = assessment.get(policy_type, {})
            if policy_type == "contentPolicy":
                items = policy.get("filters", [])
            elif policy_type == "topicPolicy":
                items = policy.get("topics", [])
            elif policy_type == "wordPolicy":
                items = policy.get("customWords", []) + policy.get("managedWordLists", [])
            elif policy_type == "sensitiveInformationPolicy":
                items = policy.get("piiEntities", []) + policy.get("regexQueries", [])
            elif policy_type == "contextualGroundingPolicy":
                items = policy.get("filters", [])
            else:
                items = []
                
            for item in items:
                if item.get("action") == "BLOCKED":
                    return True
    return False
