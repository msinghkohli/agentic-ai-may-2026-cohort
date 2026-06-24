import os
import logging
from crewai import Agent, Crew, Task, LLM, Process
from crewai.a2a import A2AClientConfig
from crewai.a2a.auth.client_schemes import BearerTokenAuth
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from typing import MutableMapping
import httpx

# Local imports
from config import MODEL_ID, A2A_BEARER_TOKEN, JIRA_A2A_ENDPOINT, setup_tracing
from tools import search_repair_policy, search_product_specifications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupportAgent")

# Setup Confident AI tracing
setup_tracing()

class TracedBearerTokenAuth(BearerTokenAuth):
    """Custom bearer token auth class that also propagates the W3C traceparent context."""

    async def apply_auth(
        self, client: httpx.AsyncClient, headers: MutableMapping[str, str]
    ) -> MutableMapping[str, str]:
        # 1. Apply static bearer token credentials
        headers = await super().apply_auth(client, headers)
        
        # 2. Inject active OpenTelemetry context into request headers for distributed tracing
        TraceContextTextMapPropagator().inject(carrier=headers)
        logger.info(f"Injected traceparent header for downstream call: {headers.get('traceparent')}")
        
        return headers


def create_support_crew() -> Crew:
    # 1. Configure the native A2A client integration pointing to the Jira Server
    jira_client_config = A2AClientConfig(
        endpoint=JIRA_A2A_ENDPOINT,
        auth=TracedBearerTokenAuth(token=A2A_BEARER_TOKEN),
        timeout=120
    )

    # 2. Define the Support Agent with local PDF tools and remote A2A capability
    support_agent = Agent(
        role="Customer Support Representative",
        goal=(
            "Answer customer queries using the return policy or product spec local search tools. "
            "For technical queries or issue/ticket status checks, delegate to the Jira Management Agent."
        ),
        backstory=(
            "You are a helpful customer support representative for Orange Electronics. "
            "You are polite, professional, and thorough. "
            "For general questions on repair service policies, cracked screens, or product specifications, "
            "you use your specialized search tools. "
            "For updates on specific tickets (e.g. ticket keys like TIME-123) or requests to create or "
            "transition Jira tickets, you delegate immediately to the remote 'Jira Management Agent' coworker."
        ),
        llm=LLM(model=MODEL_ID),
        tools=[search_repair_policy, search_product_specifications],
        allow_delegation=True,
        a2a=[jira_client_config],
        verbose=True
    )

    # 3. Define the main customer query resolution task
    support_task = Task(
        description=(
            "Answer the customer's query: '{query}'\n\n"
            "Follow these routing guidelines strictly:\n"
            "- If the query asks to check the status of a Jira ticket (e.g. key 'TIME-123' or similar), "
            "  create a ticket, or transition a ticket, delegate the request to the 'Jira Management Agent' coworker. "
            "  Do NOT try to answer using local policy/spec tools.\n"
            "- If the query asks about repair service policies, out-of-warranty screen replacements, return rules, "
            "  or product lineup specifications, search the local documents using search tools.\n"
            "- If the query is out of scope (e.g. unrelated to Orange Electronics products, policies, or Jira), "
            "  politely inform the user of your capabilities."
        ),
        expected_output="A concise, professional, and friendly response answering the customer query.",
        agent=support_agent
    )

    return Crew(
        agents=[support_agent],
        tasks=[support_task],
        process=Process.sequential,
        verbose=True
    )
