"""Pluggable authorization layer for tool access control.

This module decouples the *decision* ("may this principal perform this action
on this resource?") from the *enforcement point* (the CrewAI ``before_tool_call``
hook in :mod:`employee_chatbot.utils.toolHooks`). That mirrors how production
systems keep authorization out of business logic: tools stay pure data
operations, and a central policy decides access.

Two interchangeable backends implement the same :class:`Authorizer` interface:

- :class:`SimpleAuthorizer` — an in-code ownership check (principal must equal
  the resource owner). No external dependencies.
- :class:`CedarAuthorizer` — evaluates a Cedar PolicySet (``policies/leaves.cedar``)
  via the ``cedarpy`` engine, so the rule lives in policy text you can change
  without touching Python.

Select the backend with the ``AUTHZ_PROVIDER`` env var (``cedar`` or ``simple``;
defaults to ``simple``). If Cedar is requested but unavailable, we fall back to
the simple authorizer rather than failing open.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Cedar action ids, keyed by the (sanitized) CrewAI tool name. The hook uses
# this both to map a tool to its action and to scope which tools are guarded.
TOOL_ACTIONS: dict[str, str] = {
    "read_leaves_availed": "ReadLeaves",
    "insert_requested_leaves": "InsertLeave",
}


@dataclass(frozen=True)
class AccessDecision:
    """Outcome of an authorization check."""

    allowed: bool
    reason: str = ""


class Authorizer:
    """Interface for an authorization backend."""

    def authorize(
        self, *, principal: str, action: str, resource_owner: str
    ) -> AccessDecision:
        """Decide whether ``principal`` may perform ``action`` on a resource
        owned by ``resource_owner``."""
        raise NotImplementedError


class SimpleAuthorizer(Authorizer):
    """Ownership check expressed directly in code: a principal may only act on
    resources they own. This is the behaviour the leave tools enforced inline
    before authorization was centralized."""

    def authorize(
        self, *, principal: str, action: str, resource_owner: str
    ) -> AccessDecision:
        if principal and principal == resource_owner:
            return AccessDecision(True)
        return AccessDecision(
            False,
            f"{principal!r} may not {action} on resource owned by "
            f"{resource_owner!r}",
        )


class CedarAuthorizer(Authorizer):
    """Ownership check delegated to a Cedar PolicySet.

    The principal is modelled as ``Employee::"<id>"`` and the resource as
    ``Leaves::"<owner id>"`` carrying an ``owner`` attribute. The policy in
    ``policies/leaves.cedar`` permits the action only when
    ``principal == resource.owner``.
    """

    def __init__(self, policy_path: Path | None = None):
        from cedarpy import Decision, is_authorized  # imported lazily

        self._is_authorized = is_authorized
        self._allow = Decision.Allow

        if policy_path is None:
            # <project root>/policies/leaves.cedar (this file lives at
            # src/employee_chatbot/utils/authz.py → up 4 parents).
            policy_path = (
                Path(__file__).resolve().parents[3] / "policies" / "leaves.cedar"
            )
        self._policies = policy_path.read_text()

    def authorize(
        self, *, principal: str, action: str, resource_owner: str
    ) -> AccessDecision:
        request = {
            "principal": f'Employee::"{principal}"',
            "action": f'Action::"{action}"',
            "resource": f'Leaves::"{resource_owner}"',
            "context": {},
        }
        entities = [
            {
                "uid": {"type": "Employee", "id": principal},
                "attrs": {},
                "parents": [],
            },
            {
                "uid": {"type": "Leaves", "id": resource_owner},
                "attrs": {
                    "owner": {"__entity": {"type": "Employee", "id": resource_owner}}
                },
                "parents": [],
            },
        ]

        result = self._is_authorized(request, self._policies, entities)
        if result.decision == self._allow:
            return AccessDecision(True)
        return AccessDecision(
            False,
            f"Cedar denied {action} for Employee::{principal!r} on "
            f"Leaves::{resource_owner!r}",
        )


def get_authorizer() -> Authorizer:
    """Build the authorizer selected by the ``AUTHZ_PROVIDER`` env var.

    Defaults to :class:`SimpleAuthorizer`. If ``cedar`` is requested but the
    engine or policy file is unavailable, log and fall back to simple rather
    than failing open or crashing.
    """
    provider = os.getenv("AUTHZ_PROVIDER", "simple").strip().lower()
    if provider == "cedar":
        try:
            return CedarAuthorizer()
        except Exception as e:  # cedarpy missing, policy unreadable, etc.
            logger.error(
                "Falling back to SimpleAuthorizer; Cedar unavailable: %s", e
            )
    return SimpleAuthorizer()
