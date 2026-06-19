import logging

from crewai.hooks import after_llm_call, before_llm_call

from .guardrailUtils import GuardrailBlockedError, apply_guardrail_filters
from .memory import MemoryUtils

logger = logging.getLogger(__name__)


class LLMHooks:
    """
    Registers CrewAI LLM hooks for the employee chatbot.

    Two concerns are wired up here, each in its own method:

    - Guardrails (``_register_guardrails``): a pre-LLM hook that screens the
      user's input and a post-LLM hook that screens the model's response
      against the configured AWS Bedrock Guardrail. Blocked content stops the
      call (input) or is replaced (output); flagged-but-allowed content is
      masked in place.
    - Short-term memory (``_register_memory``): a pre-LLM hook that loads the
      conversation's short-term memory and injects it ahead of the current
      query so the agent answers with context of prior turns.

    Guardrails are registered before memory so that the raw user input is
    validated *before* any conversation history is injected into the messages.
    A `MemoryUtils` object is optional; when omitted, no memory hooks are
    registered. Guardrails are optional too: pass ``enable_guardrails=False`` to
    skip them (e.g. for agents that should only get short-term memory).
    """

    def __init__(self, memory: MemoryUtils = None, enable_guardrails: bool = True):
        self.memory = memory
        self.enable_guardrails = enable_guardrails

    def register(self):
        """Register guardrail hooks first (when enabled), then memory hooks."""
        if self.enable_guardrails:
            self._register_guardrails()
        self._register_memory()

    # ── Guardrails ────────────────────────────────────────────────────────────
    def _register_guardrails(self):
        """Register pre/post LLM hooks that enforce the Bedrock Guardrail."""

        @before_llm_call
        def guardrail_before_llm(context):
            """Screen (and mask) user prompts before they reach the LLM."""
            if not context.messages:
                return None

            for msg in context.messages:
                if msg.get("role") != "user":
                    continue
                content = msg.get("content", "")
                if not content:
                    continue

                processed_text, is_blocked = apply_guardrail_filters(
                    content, source="INPUT"
                )

                if is_blocked:
                    logger.warning("Guardrail BLOCKED LLM prompt.")
                    # Raise a BaseException so CrewAI's `except Exception` hook
                    # wrapper does not swallow it; it propagates out of kickoff().
                    raise GuardrailBlockedError(processed_text, "INPUT")

                if processed_text != content:
                    logger.info("Guardrail MASKED LLM prompt.")
                    msg["content"] = processed_text

            return None

        @after_llm_call
        def guardrail_after_llm(context):
            """Screen (and mask) the LLM response before it is returned."""
            if not context.response:
                return None

            processed_text, is_blocked = apply_guardrail_filters(
                context.response, source="OUTPUT"
            )

            if is_blocked:
                logger.warning("Guardrail BLOCKED LLM response.")
                raise GuardrailBlockedError(processed_text, "OUTPUT")

            if processed_text != context.response:
                logger.info("Guardrail MASKED LLM response.")
                return processed_text

            return None

    # ── Short-term memory ───────────────────────────────────────────────────────
    def _register_memory(self):
        """Register the pre-LLM hook that loads short-term memory."""

        @before_llm_call
        def load_memory_before_llm(context):
            """Load short-term memory and inject it ahead of the current query."""
            if self.memory is None or not context.messages:
                return None

            try:
                history = self.memory.loadShortTermMemory()
            except Exception as e:
                logger.error(f"Failed to load short-term memory: {str(e)}")
                return None

            if not history:
                return None

            # Avoid re-injecting on subsequent LLM calls within the same run
            # (e.g. after tool calls) where memory is already present.
            existing = {(m.get("role"), m.get("content")) for m in context.messages}
            history = [
                turn for turn in history
                if (turn.get("role"), turn.get("content")) not in existing
            ]
            if not history:
                return None

            # Inject history right after the first system message, so it sits
            # ahead of the conversation but below the system prompt.
            first_system = next(
                (i for i, m in enumerate(context.messages)
                 if m.get("role") == "system"),
                None,
            )
            insert_at = first_system + 1 if first_system is not None else 0
            context.messages[insert_at:insert_at] = history

            logger.info(f"Injected {len(history)} short-term memory message(s).")
            return None
