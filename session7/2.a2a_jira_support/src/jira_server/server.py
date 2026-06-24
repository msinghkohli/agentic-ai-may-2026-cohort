import asyncio
import os
import uuid
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# OpenTelemetry imports
from opentelemetry import context as otel_context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# A2A SDK imports
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Task,
    TaskStatus,
    TaskState,
    Artifact,
    Part,
    TextPart,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    SecurityScheme,
    HTTPAuthSecurityScheme,
    Message,
    Role
)

def create_task_status(state: TaskState, message_text: str) -> TaskStatus:
    return TaskStatus(
        state=state,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        message=Message(
            message_id=str(uuid.uuid4()),
            role=Role.agent,
            parts=[Part(root=TextPart(kind="text", text=message_text))]
        )
    )

# CrewAI A2A imports
from crewai.a2a import A2AServerConfig
from crewai.a2a.utils.agent_card import _agent_to_agent_card
from crewai.a2a.wrapper import inject_a2a_server_methods

# Local imports
from .. config import JIRA_A2A_PORT, A2A_BEARER_TOKEN, setup_tracing
from .. jira_management.crew_v2 import create_crew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JiraA2AServer")

# Initialize tracing
setup_tracing()

class JiraCrewExecutor(AgentExecutor):
    """Custom AgentExecutor that runs the Jira Management Crew inside the A2A request lifecycle."""

    def __init__(self, crew_factory):
        self.crew_factory = crew_factory

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task_id = context.task_id
        context_id = context.context_id

        # Trace Context Propagation: Extract traceparent context from the request headers
        headers = {}
        if context.call_context and "headers" in context.call_context.state:
            headers = context.call_context.state["headers"]

        # Extract parent trace parent and attach it to active context for this execution scope
        extracted_context = TraceContextTextMapPropagator().extract(carrier=headers)
        token = otel_context.attach(extracted_context)

        logger.info(f"Received query: {query} for task: {task_id}")

        try:
            # 1. Enqueue 'running' state update
            if task_id:
                running_status = create_task_status(
                    TaskState.working,
                    "Executing Jira Management Crew..."
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        status=running_status,
                        final=False
                    )
                )

            # 2. Run kickoff in standard executor threadpool to prevent event loop blocking
            loop = asyncio.get_running_loop()
            crew = self.crew_factory()
            
            logger.info("Starting Jira crew execution...")
            result = await loop.run_in_executor(None, lambda: crew.kickoff(inputs={"jira_request": query}))
            response_text = str(result.raw)
            logger.info("Jira crew execution finished.")

            # 3. Build Task output structures
            artifact = Artifact(
                artifact_id=str(uuid.uuid4()),
                name="jira_status_report",
                parts=[Part(root=TextPart(kind="text", text=response_text))]
            )

            # 4. Enqueue artifact update event
            if task_id:
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        artifact=artifact
                    )
                )

            # 5. Enqueue completed status update with final=True
            if task_id:
                completed_status = create_task_status(
                    TaskState.completed,
                    "Crew execution completed successfully."
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        status=completed_status,
                        final=True
                    )
                )

        except Exception as e:
            logger.exception("Exception occurred during Jira Crew execution:")
            if task_id:
                failed_status = create_task_status(
                    TaskState.failed,
                    f"Execution failed: {str(e)}"
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        task_id=task_id,
                        context_id=context_id,
                        status=failed_status,
                        final=True
                    )
                )
            raise e
        finally:
            otel_context.detach(token)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        logger.info(f"Cancellation requested for task: {task_id}")
        if task_id:
            canceled_status = create_task_status(
                TaskState.canceled,
                "Task canceled."
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=canceled_status,
                    final=True
                )
            )


# Create FastAPI base app and inject endpoints
def create_app() -> FastAPI:
    # 1. Build a dummy manager agent to hold A2AServerConfig
    # The A2AFastAPIApplication needs an AgentCard. CrewAI derives this by configuring A2AServerConfig on an Agent.
    # We will instantiate the crew to get the manager agent.
    crew = create_crew()
    manager_agent = crew.manager_agent

    # Define A2A security schemes
    bearer_security = SecurityScheme(
        root=HTTPAuthSecurityScheme(
            scheme="bearer",
            bearer_format="static",
            description="Static Bearer token authentication"
        )
    )

    # Attach A2AServerConfig to manager agent
    manager_agent.a2a = A2AServerConfig(
        name="Jira Management Agent",
        description=(
            "An agent that manages Jira projects, including creating epics, tasks, links, "
            "and retrieving issue details."
        ),
        version="1.0.0",
        url=f"http://localhost:{JIRA_A2A_PORT}/",
        security=[{"bearer_auth": []}],
        security_schemes={"bearer_auth": bearer_security}
    )
    inject_a2a_server_methods(manager_agent)

    # Generate AgentCard
    agent_card = manager_agent.to_agent_card(f"http://localhost:{JIRA_A2A_PORT}/")

    # 2. Setup A2A HTTP Request Handler and Application
    executor = JiraCrewExecutor(create_crew)
    task_store = InMemoryTaskStore()
    http_handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)

    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=http_handler
    )

    # Build FastAPI application
    app = a2a_app.build(rpc_url="/")

    # 3. Add Custom Authentication Middleware
    @app.middleware("http")
    async def token_auth_middleware(request: Request, call_next):
        # We protect the JSON-RPC endpoints (POST request)
        if request.method == "POST":
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning("Unauthenticated request: missing Bearer token header.")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized: Missing or invalid Authorization header"}
                )
            
            token = auth_header.split(" ", 1)[1]
            if token != A2A_BEARER_TOKEN:
                logger.warning(f"Unauthenticated request: invalid token received: '{token}'")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized: Invalid Bearer token"}
                )

        return await call_next(request)

    # 4. Add OpenTelemetry context propagation middleware
    @app.middleware("http")
    async def otel_propagation_middleware(request: Request, call_next):
        # Extract the traceparent context from the HTTP request headers
        headers = dict(request.headers)
        extracted_context = TraceContextTextMapPropagator().extract(carrier=headers)
        token = otel_context.attach(extracted_context)
        try:
            return await call_next(request)
        finally:
            otel_context.detach(token)

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("src.jira_server.server:app", host="0.0.0.0", port=JIRA_A2A_PORT, reload=False)
