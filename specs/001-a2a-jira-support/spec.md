# Feature Specification: A2A Jira Support Agents

**Feature Branch**: `[001-a2a-jira-support]`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "I want to create a new project for A2A in session7. This project will expose session4/2.jira_management over A2A interface. And then another CrewAI agent which will help support teams will talk to jira_management agent over A2A to get status of open issues. Apart from that the support agent will also be responsible for helping support team with other queries from customers like return policy."

## Clarifications

### Session 2026-06-24

- Q: What method should the Support Agent use to retrieve/search the company's return policy? → A: Use two PDFs containing Orange Electronics products and policies, using the open-source PageIndex framework (pageindex-open) for vectorless RAG.
- Q: What authentication mechanism should be implemented for the A2A communication between the Support Agent and the Jira Management agent? → A: Option B - Static Bearer Token / API Key.
- Q: How should the support team members interact with the Support Agent? → A: Option C - Simple Web UI (e.g. using Streamlit or Gradio).




## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exposing Jira Management over A2A (Priority: P1)

The Jira Management agent/crew (from session4/2.jira_management) is exposed as an A2A service. This allows other agents to query Jira status or manage tasks programmatically using standard JSON-RPC over HTTP.

**Why this priority**: It is the foundation for agent-to-agent communication, enabling the Support Agent to programmatically retrieve issue status.

**Independent Test**: Verify that sending an A2A JSON-RPC message to the Jira A2A service URL (e.g. via curl or a test script) returns the status of a specific open issue.

**Acceptance Scenarios**:

1. **Given** the Jira A2A server is running, **When** a client agent sends a `message/send` request asking for the status of issue `TIME-123`, **Then** the response includes a Task containing the status "In Progress" as an artifact.
2. **Given** the Jira A2A server is running, **When** a client agent requests space search from Confluence, **Then** the response retrieves the page content.

---

### User Story 2 - Querying Jira Status via Support Agent (Priority: P1)

A support team member asks the Support Agent for the status of an open customer issue. The Support Agent automatically delegates this query to the Jira Management agent over the A2A interface and replies to the support team member.

**Why this priority**: It is the primary business value of this project: enabling customer support agents to check Jira status without accessing Jira directly.

**Independent Test**: Run the Support Agent CLI/interface and ask "What is the status of issue TIME-123?" Verify that it returns the correct status after calling the Jira A2A agent.

**Acceptance Scenarios**:

1. **Given** both agents are running and the Jira A2A agent is accessible, **When** the support member queries "What's the status of the checkout issue?", **Then** the Support Agent uses the A2A client tool to query Jira Management, receives the ticket status, and translates it into a user-friendly response.

---

### User Story 3 - Resolving Non-Jira Customer Queries (Priority: P2)

A support team member asks the Support Agent about non-Jira customer queries, such as the company return policy. The Support Agent resolves this query locally using a policy knowledge source.

**Why this priority**: Provides a unified interface for the support team so they don't have to switch between different tools for policies versus ticket updates.

**Independent Test**: Ask the Support Agent "What is our return policy?" and verify that it returns the correct return windows and conditions.

**Acceptance Scenarios**:

1. **Given** the Support Agent is running, **When** asked "Can a customer return an item after 45 days?", **Then** the agent searches the return policy and answers that returns must be within 30 days.

---

### Edge Cases

- **Jira Agent Unreachable**: What happens if the Jira A2A service is down or returns a 500 error when the Support Agent tries to query it? The Support Agent must report a clear, friendly error to the support team member instead of failing silently.
- **Ambiguous Issue Reference**: What if the support team member asks about "the issue" but multiple matching issues exist? The Support Agent must ask for clarification (e.g., ticket ID or key).
- **Out of Scope Query**: What if a customer queries something completely unrelated to Jira issues or the return policy? The Support Agent must politely decline and state its supported capabilities.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Jira Management crew MUST be wrapped as an A2A service using `A2AStarlette` and expose its skills.
- **FR-002**: The Jira A2A service MUST expose a skill to query Jira issue status using JQL or ticket ID.
- **FR-003**: The Support Agent MUST use the A2A protocol (`message/send` or `message/stream` JSON-RPC methods) to communicate with the Jira A2A agent.
- **FR-004**: The Support Agent MUST retrieve return policy and product information using the open-source PageIndex framework (pageindex-open) querying the two provided Orange Electronics PDFs (repair_service_policy.pdf and product_lineup_specifications.pdf).
- **FR-005**: The A2A communication between the Support Agent and the Jira Management agent MUST be authenticated using a static Bearer Token (passed in the Authorization header).
- **FR-006**: The Support Agent MUST expose a simple Web UI (e.g. using Streamlit or Gradio) for support staff interaction.

### Key Entities *(include if feature involves data)*

- **Jira Issue State**: Represents the status and metadata of a ticket in Jira (ticket ID, summary, status, assignee, priority).
- **Customer Query**: Represents the user input to the Support Agent (text prompt containing question or request).
- **A2A Message**: The JSON-RPC 2.0 request/response structure carrying the conversation parts (TextPart, DataPart) between agents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Support team can check any Jira issue status in under 10 seconds via the Support Agent.
- **SC-002**: Support Agent resolves 95% of standard return policy questions correctly based on the policy document.
- **SC-003**: All communication between the Support Agent and the Jira Management agent uses the official A2A JSON-RPC protocol specification.

## Assumptions

- The existing Jira management code in `session4/2.jira_management` is functional and can connect to Jira via the Atlassian MCP server.
- The return policy document is static and fits within standard LLM context windows or local search mechanisms.
- Support team uses a CLI or simple shell-based execution environment for development/testing.
