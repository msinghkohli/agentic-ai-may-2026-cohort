# Project 3 — Incident Response Orchestrator

> 1-hour group activity: design the architecture of an agentic Jira automation application.

> 💡 **AI is encouraged.** Use Claude, ChatGPT, or any AI tool to help brainstorm, refine your architecture, challenge your assumptions, or draft your presentation. Treat AI as a team member — but be ready to explain and defend every decision it helps you make.

---

## How It Works

| Phase | Duration | What happens |
|---|---|---|
| **Architecture design** | 40 minutes | Each group designs their assigned agentic application in a Zoom breakout room |
| **Presentation prep** | 20 minutes | Groups prepare a whiteboard/diagram to present back to the cohort |

Your goal is not to build it — it is to design it. Think agents, tools, orchestration patterns, data flow, and the non-functional requirements that would make it production-ready.

---

### a) Problem Statement

When a production incident strikes at 2 a.m., the on-call engineer is already behind. They must manually read through the Jira ticket, determine severity, hunt through Confluence for a runbook that may or may not exist, and try to remember which service owns which component. After the incident is resolved — often hours later — they are expected to produce a structured post-mortem from memory, which rarely happens on time and is almost never complete. The result: slower mean time to resolution (MTTR), inconsistent incident handling, and a post-mortem culture that exists on paper but not in practice.

**The question this agent answers:** *The moment a new incident ticket lands in Jira, what is its severity, which service is affected, what does the runbook say to do — and once it's resolved, what happened and what should the team do next?*

### b) Expectations

Your group should design an agentic application that:

- **Triggers** when a new incident ticket is created or transitioned to "In Progress" in Jira — detected via the **Jira MCP server** (polling or webhook)
- **Classifies** the incident — a dedicated agent reads the ticket title, description, and any linked alerts; assigns a severity level (P1/P2/P3), identifies the affected component (authentication, payments, data pipeline, etc.), and names the owning service; updates the Jira ticket fields via the **Jira MCP server**
- **Retrieves the relevant runbook** (RAG) — a dedicated agent embeds the classified incident description and queries a **vector store** of pre-indexed runbooks and past incident resolutions; returns the most semantically similar runbook; posts the matching runbook steps as a comment on the Jira ticket via the **Jira MCP server** so the on-call engineer sees them immediately
- **Drafts the post-mortem** — once the incident ticket transitions to "Resolved" (monitored via the **Jira MCP server**), a dedicated agent reconstructs the full incident timeline by reading all ticket comments, status transitions, and linked alert tickets in chronological order; uses LLM reasoning to synthesise a structured post-mortem document — incident summary, customer impact, root cause, contributing factors, and action items — and publishes it as a Confluence page

Your architecture document should cover:
- **Agents** — name each agent and define its single responsibility:
  - **Incident Manager** (Orchestrator): reads the new ticket via the **Jira MCP server**, delegates to the Classifier and Runbook Retriever in sequence, then monitors for resolution and triggers the Post-Mortem Drafter
  - **Classifier**: uses LLM reasoning over the ticket content to assign severity, component, and owning service; updates Jira ticket fields via MCP
  - **Runbook Retriever**: embeds the classified incident; queries the vector store of runbooks and past incident data; posts the top match as a Jira comment via MCP
  - **Post-Mortem Drafter**: reads the full ticket history (comments + transitions) via MCP; synthesises a structured post-mortem; writes it to Confluence
- **Tools** — **vector store** (indexed runbooks and past incident resolutions, queried by Runbook Retriever via semantic similarity); **Jira MCP server** (read ticket, update severity/component fields, post runbook comment, monitor status transition to "Resolved"); **Confluence** (write post-mortem page); Slack (optional: notify on-call channel when runbook is posted, and when post-mortem is published)
- **Orchestration pattern** — **hierarchical**: Incident Manager is the orchestrator that delegates to specialists in sequence: Classifier first → Runbook Retriever next (uses Classifier output to enrich the query) → then waits asynchronously for ticket resolution → Post-Mortem Drafter last; the Incident Manager never does the specialist work itself
- **Key agentic behaviors** — LLM-based classification (Classifier uses reasoning, not keyword rules, to handle novel service names or ambiguous descriptions), RAG-powered retrieval (Runbook Retriever does semantic search — "database replication lag" matches a runbook titled "read replica health degradation" even with no shared keywords), asynchronous lifecycle management (Incident Manager holds state between ticket creation and resolution, which may be hours apart), structured synthesis (Post-Mortem Drafter reasons causally across the timeline, not just summarising individual comments)

**Bonus discussion:** What happens when the Runbook Retriever finds no good match (similarity below threshold) — does it say so, or does it hallucinate a procedure? How do you keep the runbook vector store up to date as runbooks evolve? Who reviews the post-mortem before it's published to Confluence — does the agent publish automatically or wait for human approval? How do you handle an incident that spans multiple services — should the Runbook Retriever return multiple runbooks?

### c) Time Limit

| Milestone | Time |
|---|---|
| Read and Discuss Problem Statement | 10 minutes |
| Agree on agents and their responsibilities | 15 minutes |
| Design the orchestration flow end-to-end | 15 minutes |
| Prepare presentation (diagram + key talking points) | 20 minutes |
| **Total** | **60 minutes** |

---

## Presentation Format (10 minutes per group)

Each group should be ready to present:

1. **The agent map** — a simple diagram showing each agent, what it does, and how they connect
2. **The orchestration pattern** — sequential? parallel fan-out? hierarchical? why?
3. **The agentic moment** — what is the one behavior in your design that makes this genuinely agentic rather than just a workflow automation?
