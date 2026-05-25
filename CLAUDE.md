# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a course cohort repository for an Agentic AI program. It contains progressively complex examples across 4 sessions, each building on the previous: prompt engineering → CrewAI agents → RAG → MCP integration.

## Package Management & Setup

All Python projects use **uv** for dependency management. Each session subdirectory is an independent Python project.

```bash
# Install dependencies for a project
cd session2/1.stockresearch
uv sync

# Copy environment template and fill in keys
cp .env.template .env
```

## Running Projects

```bash
# Session 2 - Stock Research (pick a crew version)
cd session2/1.stockresearch
uv run python -m src.stockresearch.crew_v1   # single generalist agent
uv run python -m src.stockresearch.crew_v2   # single financial analyst
uv run python -m src.stockresearch.crew_v3   # hierarchical multi-agent

# Session 3 - Employee Policy (RAG with Bedrock KB)
cd session3/2.employeepolicy
uv run python -m src.employeepolicy.crew

# Session 4 - Jira Management (MCP)
cd session4/2.jira_management
uv run python -m src.jiramanagement.main

# Session 2 - CDK infrastructure deploy
cd session2/2.stockresearch_infra
uv run cdk deploy
```

## Linting

A shared `ruff.toml` at the repo root applies to all subprojects (line length 88, E/F/W/I rules).

```bash
# Lint
uv run ruff check .

# Auto-fix
uv run ruff check --fix .
```

## Architecture

### Session Structure

| Session | Projects | Tech |
|---------|----------|------|
| `session1/` | Prompt engineering scripts, ReAct simulation via shell | Bash, Anthropic API |
| `session2/1.stockresearch/` | Three crew versions (single → hierarchical) | CrewAI, Tavily, yfinance |
| `session2/2.stockresearch_infra/` | CDK stack deploying agent to AWS Bedrock AgentCore Runtime | AWS CDK v2, Docker, ECR |
| `session2/3.deepresearch/` | Multi-agent orchestration for deep research | CrewAI |
| `session3/1.knowledgebase/` | AWS Bedrock Knowledge Base setup + eval dataset | Bedrock, JSONL |
| `session3/2.employeepolicy/` | HR Manager agent with RAG over employee handbook | CrewAI, BedrockKBRetrieverTool |
| `session4/1.atlassian_mcp_server/` | MCP Inspector walkthrough (no code) | MCP Inspector |
| `session4/2.jira_management/` | Multi-agent Jira/Confluence management via MCP | CrewAI, Atlassian MCP |

### Common CrewAI Project Pattern

Every Python project under `session2`+ follows the same layout:

```
src/<package>/
  crew.py              # Agent/Task/Crew definitions
  main.py              # Entry point (some projects)
  utils/
    crew_executor.py   # OTEL setup + Langfuse export + crew.kickoff()
    bedrock_patches.py # Monkey-patches for AWS Bedrock compatibility
    llm_otel_listener.py  # Custom OTEL spans via CrewAI event bus
```

- **Model selection**: `MODEL_ID` env var uses litellm-style prefixes (`bedrock/...`, `anthropic/...`, `openai/...`). Session 4 uses `LARGE_MODEL_ID`.
- **Observability**: Langfuse tracing via OTLP exporter. `crew_executor.py` sets up the OTEL provider before importing CrewAI. Tracing is optional in session2/3 (only activates if `LANGFUSE_PUBLIC_KEY` is set), mandatory in session4.
- **LLM call tracing**: CrewAI 0.186+ bypasses litellm and routes through provider-native SDKs. `LLMOtelListener` hooks into CrewAI's event bus to capture LLM spans — litellm instrumentation alone does not work.
- **Bedrock auth**: Uses `~/.aws/credentials` or IAM role. No API key needed for Bedrock models.

### Crew Architectures (Session 2 stockresearch)

- **V1**: Single generalist agent + Tavily search + date tool
- **V2**: Single financial analyst + specialized stock price tool + structured output
- **V3**: Hierarchical — Manager agent delegates to Financial Analyst or Generalist based on query intent

### Session 4 MCP Pattern

`crew.py` connects to `https://mcp.atlassian.com/v1/mcp` via `MCPServerAdapter`. All Atlassian tools are loaded at startup, then filtered per-agent using `_filter_tools()` to give each agent only the tools it needs. A `jira_manager` orchestrator uses `Process.hierarchical` and delegates to four specialist agents (confluence reader/manager, jira reader/manager).

## Environment Variables

All projects use `.env.template` as the source of truth for required keys. Key variables:

| Variable | Used in |
|----------|---------|
| `MODEL_ID` | All CrewAI projects (session2, session3) |
| `LARGE_MODEL_ID` | Session 4 jira_management |
| `TAVILY_API_KEY` | session2/1.stockresearch |
| `BEDROCK_KB_ID` | session3/2.employeepolicy |
| `ATLASSIAN_EMAIL`, `ATLASSIAN_API_KEY` | session4/2.jira_management |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` | All CrewAI projects |
