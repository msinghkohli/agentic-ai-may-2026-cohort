# Deep Research Crew

## Purpose

Welcome to the Deep Research project, powered by [crewAI](https://crewai.com).

This project uses a multi-agent AI crew to conduct deep, structured research on any topic. Given a research question, the crew decomposes it into sub-questions, investigates each using live web search and content extraction, writes a comprehensive cited article, and applies a critic-review feedback loop before producing the final output.

The same pipeline is implemented as **two crews** that differ only in how the research sub-questions are investigated:

- **Sequential pattern** (`crew_sequential_pattern.py`) — the researcher tasks run one after another. Simpler and easier to trace, but slower because each sub-question is investigated in turn.
- **Parallel pattern** (`crew_parallel_pattern.py`) — the researcher tasks run concurrently via `async_execution=True`. Faster end-to-end, since both sub-questions are investigated at the same time. Each parallel research task gets its own agent instance so that concurrent tool-call loops don't interleave their message histories.

Both crews share the same six agents (Planner → two Researchers → Writer → Critic → Reviser) and produce the same kind of cited article — comparing them is a good way to see the trade-off between sequential and parallel agent orchestration.


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
uv sync
```
### Customizing

**Set up your `.env` file by copying the template:**

```bash
cp .env.template .env
```

Then configure the following keys in your `.env` file:

**Model setup** — set `MODEL_ID` to the model you want to use, and provide the corresponding API key (in case you are not using AWS Bedrock hosted models).

```env
# Example: AWS Bedrock
MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0

# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
ANTHROPIC_API_KEY=your_anthropic_api_key

# Example: OpenAI
MODEL_ID=openai/gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

If you are using AWS Bedrock hosted models, you need to install and configure the AWS CLI by following the [official AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). Once installed, run:

```bash
aws configure
```

You'll be prompted for your AWS Access Key ID, Secret Access Key, default region (`us-east-1`), and output format (`json`).

**Tavily** — used by the agent to search the web for stock data:

```env
TAVILY_API_KEY=your_tavily_api_key
```

Get a free Tavily key at [tavily.com](https://tavily.com).

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. ***Create an account*** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. ***Create an organization*** — after login, you'll be prompted to create or join an organization (this is the top-level workspace, e.g. your team or company name)
3. ***Create a project*** — inside your organization, create a new project (e.g. `deepresearch`); each project has its own set of API keys and trace history
4. ***Get your API keys*** — go to **Project Settings → API Keys** and create a new key pair; copy the public and secret keys into your `.env` file

## Running the Project

To kickstart your crew of AI agents and begin task execution, run one of the two crews from the root folder of your project:

```bash
# Sequential pattern — research sub-questions investigated one after another
$ uv run python -m src.deepresearch.crew_sequential_pattern

# Parallel pattern — research sub-questions investigated concurrently
$ uv run python -m src.deepresearch.crew_parallel_pattern
```

Either command initializes the Deep Research crew, assembles the agents, and executes the research pipeline. Once asked, you may mention the topic you would like the agent to perform deep research on. It will take around 10 minutes to produce a structured research article on the asked query (the parallel pattern is typically faster since the two research tasks run at the same time).

## Observing the ReAct Cycle in Langfuse

Once you've configured Langfuse and run the crew, you can observe the agent's full reasoning trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agents follow a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM thinks about what it knows and what it needs
2. **Act** — CrewAI calls a tool (e.g. Tavily web search, URL extractor)
3. **Observe** — LLM reads the tool result
4. **Repeat** — until it has enough information to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span. This makes it easy to understand how the agent arrived at its answer and where time or tokens were spent.

## Understanding Your Crew

Each Deep Research crew uses six specialist agents that collaborate to produce a cited research article with a built-in revision loop:

1. **Planner** — decomposes the user query into two precise, non-overlapping sub-questions.
2. **Researchers (×2)** — one investigator per sub-question, each gathering evidence via web search and URL extraction and grounding every finding in a retrieved source.
3. **Writer** — synthesizes both sets of findings into a structured 1000–1500 word article with inline `[Source: URL]` citations.
4. **Critic** — reviews the draft for factual support, citation completeness, structure, and coherence, then either approves it or lists actionable revision points.
5. **Reviser** — produces the final, publication-ready article by incorporating the critic's feedback.

The **sequential** and **parallel** crews use this exact agent lineup; the only difference is whether the two research tasks run one at a time or concurrently.

