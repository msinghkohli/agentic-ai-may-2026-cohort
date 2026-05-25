# Session 4 - MCP — Assignments

## Assignment 1: Inspecting the Atlassian MCP Remote Server

**Project:** [1.atlassian_mcp_server/](1.atlassian_mcp_server/)

Connect to the Atlassian MCP Remote Server using **MCP Inspector** and invoke tools like `createJiraIssue` directly — without writing any agent code. You will authenticate via HTTP Basic Auth, explore the full tool catalogue, and verify that your credentials and cloud ID work before building any agents.

See the [full instructions](1.atlassian_mcp_server/README.md) to get started.

### Questions to Reflect On

- What does inspecting a tool's input schema tell you about how an agent will need to call it?

---

## Assignment 2: Jira Management Crew

**Project:** [2.jira_management/](2.jira_management/)

Build crewAI agents that read a requirements input (plain text or a Confluence page URL) and automatically create a structured epic with child tasks in a Jira project via the Atlassian MCP server. Two crew versions are provided so you can compare architectures.

See the [full instructions](2.jira_management/README.md) to get started.

### Questions to Reflect On

- How does the agent decide whether a design task is needed? What part of the prompt drives that reasoning?
- How many MCP tool calls did the agent make in a single run? How does observing this in Langfuse help you tune the agent?
- What are the trade-offs between V1 (single agent, all tools) and V2 (hierarchical, scoped tools)?