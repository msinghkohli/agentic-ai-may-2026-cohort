# Research: A2A Jira Support Agents

## RAG Framework: PageIndex Open-Source (`pageindex-open`)

- **Decision**: Use `pageindex-open` python package to parse and query the Orange Electronics PDFs.
- **Rationale**: The open-source `pageindex-open` package builds a hierarchical tree-structured index from PDFs. Instead of chunking documents into arbitrary sizes and using vector similarity search, it preserves document structure (headings, sections, tables) and performs reasoning-based retrieval. This is highly suitable for policies and specifications where sections are logically linked.
- **Alternatives Considered**: 
  - *Traditional Vector RAG (Chroma/FAISS)*: Rejected due to risk of "similarity vs relevance" issues, where paragraphs are matches based on keywords but lack the broader context of surrounding sections.
  - *Amazon Bedrock Knowledge Base*: Rejected to keep the implementation local and open-source, avoiding AWS dependencies and costs.

---

## Agent Framework: CrewAI

- **Decision**: Use CrewAI to define the Support Agent and configure it with specific tools.
- **Rationale**: CrewAI is already established in the workspace (session7 and session4) and provides a clean model for task definitions, backstories, and custom tool usage.
- **Alternatives Considered**: 
  - *LangChain LangGraph / Raw LangChain*: Rejected to maintain consistency with the existing codebase patterns in the workspace.

---

## A2A Client & Security

- **Decision**: Use the native CrewAI A2A client implementation (using `A2AClientConfig`) configured directly on the Support Agent to securely delegate tasks to the remote Jira Management A2A server, authenticated via a static Bearer Token (`Authorization: Bearer OrangeJiraToken`).
- **Rationale**: This leverages CrewAI's first-class A2A delegation primitives, keeping code simple, clean, and native to the framework while satisfying security requirement `FR-005`.
- **Alternatives Considered**:
  - *Custom CrewAI Tool with manual JSON-RPC implementation*: Rejected as native `A2AClientConfig` is built-in and more robust.
  - *Unauthenticated requests*: Rejected as it violates the security requirement.
  - *OAuth2 M2M flow*: Rejected due to high implementation complexity for a local demonstration.


---

## User Interface: Streamlit Web UI

- **Decision**: Build a Streamlit web application.
- **Rationale**: Streamlit provides a fast, Python-native way to build a premium web interface with chat components, perfectly matching Option C selected by the user.
- **Alternatives Considered**:
  - *Command Line Interface (CLI)*: Rejected as the user explicitly chose a Web UI.

---

## Observability & Tracing: Confident AI

- **Decision**: Use Confident AI for hosted tracing and execution observability.
- **Rationale**: Confident AI provides the hosted tracing dashboard (using `deepeval`'s `instrument_crewai` and `trace` wrapper) to capture real-time execution flows and thread histories. This matches the exact patterns from Session 6 and 7.
- **Alternatives Considered**:
  - *DeepEval Local Evaluations*: Out of scope; we are only integrating the tracing capabilities to push logs to the Confident AI dashboard, not executing local metrics test runs.
  - *Langfuse*: Rejected to align with the latest standards of using Confident AI.

