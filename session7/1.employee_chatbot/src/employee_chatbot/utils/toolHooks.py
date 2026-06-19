"""CrewAI tool-call hooks for the employee chatbot.

This is the *enforcement point* for tool access control. It mirrors the LLM
hooks in :mod:`employee_chatbot.utils.llmHooks`, but registers a
``before_tool_call`` hook that runs before the leave tools execute.

Keeping the check here (rather than inside each tool's ``_run``) is closer to a
production setup: the tools stay pure data operations, and authorization is a
cross-cutting concern owned by a central, swappable policy
(:mod:`employee_chatbot.utils.authz` — in-code or Cedar-backed).

These hooks are registered only by the guarded agent (v2). v1 is the unguarded
baseline and simply does not register them.

Enforcement detail that drives the design: CrewAI blocks a tool call only when
a ``before_tool_call`` hook *returns ``False``*. If the hook raises, CrewAI
catches and logs the exception and then runs the tool anyway — so an exception
here would be a security bypass. We therefore always return ``False`` to deny.
"""

import logging

from crewai.hooks import before_tool_call

from .authz import TOOL_ACTIONS, Authorizer, get_authorizer
from .session import Session

logger = logging.getLogger(__name__)


class ToolHooks:
    """Registers the ``before_tool_call`` authorization hook.

    The guarded tools and their Cedar action ids come from
    :data:`employee_chatbot.utils.authz.TOOL_ACTIONS`. The actual allow/deny
    decision is delegated to an :class:`Authorizer` (in-code or Cedar), chosen
    via the ``AUTHZ_PROVIDER`` env var by default.
    """

    def __init__(self, authorizer: Authorizer | None = None):
        self.authorizer = authorizer or get_authorizer()

    def register(self):
        guarded_tools = list(TOOL_ACTIONS.keys())

        @before_tool_call(tools=guarded_tools)
        def authorize_leave_tool(context):
            """Allow the call (return None) or block it (return False)."""
            action = TOOL_ACTIONS.get(context.tool_name)
            if action is None:  # not a guarded tool; let it through
                return None

            principal = Session().getEmployeeId()
            resource_owner = context.tool_input.get("employee_id")

            decision = self.authorizer.authorize(
                principal=principal,
                action=action,
                resource_owner=resource_owner,
            )

            if not decision.allowed:
                # Log the reason centrally; CrewAI surfaces a generic
                # "blocked by hook" result to the agent (we deliberately do
                # not leak authz internals to the model/user).
                logger.warning(
                    "Access denied for tool %s: %s",
                    context.tool_name,
                    decision.reason,
                )
                return False

            return None
