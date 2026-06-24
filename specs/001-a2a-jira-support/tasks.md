# Tasks: A2A Jira Support Agents

**Input**: Design documents from `specs/001-a2a-jira-support/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/a2a_jsonrpc_contract.md, quickstart.md

**Organization**: Tasks are grouped by setup, foundation, user story phases, and polish to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project folder setup and workspace dependency configuration.

- [ ] T001 Create project folders under `session7/2.a2a_jira_support/src/` including `jira_management`, `jira_server`, `support_agent`, and `documents` directories
- [ ] T002 Initialize project dependencies (`pageindex-open`, `fastapi`, `uvicorn`, `streamlit`, `crewai[a2a]`, `pypdf`, `deepeval`) in `session7/2.a2a_jira_support/pyproject.toml`
- [ ] T003 [P] Copy `repair_service_policy.pdf` and `product_lineup_specifications.pdf` to the `session7/2.a2a_jira_support/documents/` folder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Common configuration settings and imports.

- [ ] T004 Setup environment configs and constant variables (model IDs, ports, API tokens) in `session7/2.a2a_jira_support/src/config.py`

---

## Phase 3: User Story 1 - Exposing Jira Management over A2A (Priority: P1)

**Goal**: Expose the exact session4/2.jira_management code as an A2A-compliant server.

**Independent Test**: Start the server on port `8001` and run a test script sending a JSON-RPC request to verify that the server returns valid responses.

### Implementation for User Story 1

- [ ] T005 [US1] Copy the exact Jira Management code from `session4/2.jira_management/src/jiramanagement/` to `session7/2.a2a_jira_support/src/jira_management/`
- [ ] T006 [US1] Implement the A2A server wrapper using `crewai.a2a.A2AServerConfig` in `session7/2.a2a_jira_support/src/jira_server/server.py`
- [ ] T007 [US1] Add static Bearer Token authentication middleware to validate the `Authorization: Bearer OrangeJiraToken` header in `session7/2.a2a_jira_support/src/jira_server/server.py`
- [ ] T008 [US1] Set up Confident AI tracing instrumentation calling `instrument_crewai()` and configuring OpenTelemetry middleware in `session7/2.a2a_jira_support/src/jira_server/server.py` to automatically extract the incoming `traceparent` header and link child spans to the parent Support Agent trace.

**Checkpoint**: At this point, the Jira A2A server can be started on port `8001` and queried independently.

---

## Phase 4: User Story 2 - Querying Jira Status via Support Agent (Priority: P1)

**Goal**: Define the Support Agent and enable it to query the Jira A2A server using native `A2AClientConfig`.

**Independent Test**: Ask the Support Agent "What is the status of ticket TIME-123?" and verify that it delegates the task to the Jira A2A server and returns the correct status.

### Implementation for User Story 2

- [ ] T009 [US2] Define the Support Agent crew and task instructions in `session7/2.a2a_jira_support/src/support_agent/agent.py`
- [ ] T010 [US2] Configure the Support Agent's native A2A client integration using `A2AClientConfig` pointing to the Jira server endpoint and presenting the Bearer token in `session7/2.a2a_jira_support/src/support_agent/agent.py`
- [ ] T011 [US2] Wrap the Support Agent kickoff in a Confident AI tracing context using `with trace(...)` in `session7/2.a2a_jira_support/src/support_agent/agent.py`, ensuring that the OpenTelemetry client context propagates the `traceparent` header to downstream HTTP A2A calls.

**Checkpoint**: The Support Agent can successfully communicate with the Jira Management A2A server to resolve ticket queries.

---

## Phase 5: User Story 3 - Resolving Non-Jira Customer Queries (Priority: P2)

**Goal**: Enable the Support Agent to answer return policy and product specifications queries using `pageindex-open`.

**Independent Test**: Ask the Support Agent about return policy durations and verify it searches the PDF and responds with correct time windows.

### Implementation for User Story 3

- [ ] T012 [P] [US3] Implement the PageIndex indexing and search utility (`PageIndexTool` using `pageindex_open.PIO`) in `session7/2.a2a_jira_support/src/tools.py`
- [ ] T013 [US3] Wire the PageIndex search tool into the Support Agent definition inside `session7/2.a2a_jira_support/src/support_agent/agent.py`
- [ ] T014 [US3] Build cached tree index files for the PDFs under `session7/2.a2a_jira_support/data/indexes/` by running the initialization script

**Checkpoint**: The Support Agent can answer both Jira-related and PDF-based policy queries.

---

## Phase 6: Polish & UI

**Purpose**: User interface implementation, end-to-end validation, and cleanup.

- [ ] T015 Implement the Streamlit interactive chat UI in `session7/2.a2a_jira_support/src/support_agent/app.py`
- [ ] T016 Run all validation scenarios from `quickstart.md` and verify Confident AI trace logs
- [ ] T017 Clean up unused code and update developer documentation in `session7/2.a2a_jira_support/README.md`, including setup, usage, and how to test the A2A server using a local A2A Inspector setup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories.
- **User Story 1 (Phase 3)**: Can start after Phase 2 completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 server implementation to perform client delegation.
- **User Story 3 (Phase 5)**: Depends on Phase 2 completion (can run in parallel with US1 and US2 implementation).
- **Polish & UI (Phase 6)**: Depends on all User Story phases (3, 4, 5) completion.

### Parallel Opportunities

- All setup tasks (Phase 1) can run in parallel.
- User Story 3 RAG search tool (`T012`) can be implemented in parallel with the Jira A2A server (`T005`-`T008`).
- Validation scenarios (`T016`) can be executed in parallel after the Web UI is up.

---

## Implementation Strategy

### MVP Scope (User Story 1 & User Story 2)

1. Complete Setup and Foundational phases.
2. Implement Phase 3 (US1 - Jira A2A server wrapper).
3. Implement Phase 4 (US2 - Support Agent client A2A communication).
4. Run validation on ticket lookup.

### Incremental Delivery

1. Setup + Foundation completed -> Baseline project.
2. Jira Server wraps session4 crew -> Jira service is live.
3. Support Agent + A2A integration -> Native client delegates ticket questions.
4. Support Agent + PageIndex integration -> Returns policy questions handled.
5. Streamlit App runs over all systems -> Full visual client delivery.
