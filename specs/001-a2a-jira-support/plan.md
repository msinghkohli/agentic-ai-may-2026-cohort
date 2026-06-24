# Implementation Plan: A2A Jira Support Agents

**Branch**: `[001-a2a-jira-support]` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-a2a-jira-support/spec.md`

This project implements a multi-agent system exposing the copied Jira Management crew as an A2A service and orchestrating a separate Support Agent. The Support Agent interacts with the Jira Management agent over A2A using native CrewAI A2A delegation (`A2AClientConfig`) and answers return/product policy questions using `pageindex-open` for vectorless RAG over two PDFs. The interface is exposed as a Streamlit Web UI, and all execution flows are traced using Confident AI integration.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: `crewai[a2a]`, `fastapi`, `uvicorn`, `streamlit`, `pageindex-open`, `pypdf`, `pydantic`, `deepeval` (for Confident AI tracing)

**Storage**: Local JSON files for cached PageIndex tree structures in `session7/2.a2a_jira_support/data/indexes/`.

**Testing**: `pytest`

**Target Platform**: Local execution (macOS/Linux)

**Project Type**: Multi-agent web service & Streamlit frontend application

**Performance Goals**: <10s query response time (including A2A JSON-RPC latency and local vectorless RAG reasoning).

**Constraints**: Local port management: port `8001` for the Jira A2A Server and port `8501` for the Streamlit UI. Secure authorization header verified with static Bearer token `OrangeJiraToken`. Distributed tracing context is propagated from the Support Agent client to the Jira A2A Server via W3C `traceparent` headers.

**Scale/Scope**: Local demo serving customer support staff queries against 2 policy PDFs and active Jira board states.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Conforms to workspace Python style guidelines.
- [x] All communications use official A2A JSON-RPC spec.
- [x] Uses the open-source version of PageIndex (`pageindex-open`).
- [x] Static Bearer Token used for A2A request authentication.

## Project Structure

### Documentation (this feature)

```text
specs/001-a2a-jira-support/
├── plan.md              # This file
├── research.md          # Research findings
├── data-model.md        # Data entities and Pydantic schemas
├── quickstart.md        # How to run and validate
└── contracts/
    └── a2a_jsonrpc_contract.md  # JSON-RPC spec contract
```

### Source Code

```text
session7/2.a2a_jira_support/
├── documents/
│   ├── repair_service_policy.pdf
│   └── product_lineup_specifications.pdf
├── data/
│   └── indexes/               # Cached pageindex-open tree index files
├── src/
│   ├── __init__.py
│   ├── config.py               # Shared configs, tokens, ports, model IDs
│   ├── tools.py                # PageIndex RAG tool
│   ├── jira_management/        # Exact copied code from session4/2.jira_management
│   │   ├── __init__.py
│   │   ├── crew_v1.py
│   │   ├── crew_v2.py
│   │   └── ...
│   ├── jira_server/            # Exposes jira_management crew over A2A Server
│   │   ├── __init__.py
│   │   └── server.py           # Uses A2AServerConfig to expose the crew
│   └── support_agent/          # Exposes Support Agent Web App
│       ├── __init__.py
│       ├── agent.py            # Support Agent with A2AClientConfig
│       └── app.py              # Streamlit Web UI
└── tests/
    ├── __init__.py
    └── test_a2a_support.py    # Integration and mock testing
```

**Structure Decision**: Exposing the codebase inside a single directory `session7/2.a2a_jira_support` with isolated modules for the Jira Management A2A Server and the Support Agent is selected to keep the code modular and self-contained.

## Complexity Tracking

No constitution violations registered.

