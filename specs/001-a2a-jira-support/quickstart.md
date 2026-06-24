# Quickstart Guide: A2A Jira Support Agents

This guide explains how to run, test, and validate the A2A Jira Support Agents feature.

## Prerequisites

1. Python 3.12 installed.
2. Dependencies installed:
   ```bash
    uv pip install pageindex-open fastapi uvicorn streamlit 'crewai[a2a]' pypdf deepeval
   ```
3. Set your environment variables (e.g., LLM keys and Confident AI API key for tracing).
   ```bash
   export MODEL_ID="bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
   # To enable Confident AI tracing:
   export CONFIDENT_AI_API_KEY="your-confident-ai-key"
   ```

---

## Running the Services

### Step 1: Start the Jira Management A2A Server
Run the A2A server that exposes the Jira Management crew on port `8001`.
```bash
uv run python -m session7.2.a2a_jira_support.src.jira_server.server
```

### Step 2: Start the Support Agent Web App
Run the Streamlit web application on port `8501`.
```bash
streamlit run session7/2.a2a_jira_support/src/support_agent/app.py
```

---

## Validation Scenarios

### Scenario 1: Retrieve Return Policy (Local PageIndex Vectorless RAG)
1. Open the Web UI at `http://localhost:8501`.
2. Input: `"What is the repair & service policy for cracked screens?"`
3. Expected Output: The agent should query the PageIndex model for `repair_service_policy.pdf` and explain that cracked screen repairs are classified as "Out-of-Warranty" and require an approved service fee quote.

### Scenario 2: Retrieve Jira Ticket Status (A2A Communication)
1. Open the Web UI at `http://localhost:8501`.
2. Input: `"Check status of ticket TIME-123."`
3. Expected Output: The Support Agent sends a secure A2A request to the Jira server (port `8001`), receives the ticket status, and displays it in the Web UI.

### Scenario 3: Testing A2A Server using Local A2A Inspector
Validate A2A compliance and inspect the raw JSON-RPC traffic using a locally running A2A Inspector.

1. Ensure the Jira Management A2A Server is running on port `8001`.
2. Set up and start the A2A Inspector locally:
   ```bash
    # Clone the A2A Inspector repo
    git clone https://github.com/enterprise-grade-agentic-ai/a2a-inspector
    cd a2a-inspector

   # Option A: Run via Docker (Recommended)
   docker build -t a2a-inspector .
   docker run -d --rm --name a2a-inspector -p 5001:8080 a2a-inspector

   # Option B: Run via local scripts
   ./scripts/run.sh
   ```
3. Open `http://localhost:5001/` in your browser.
4. Enter the local agent URL in the input box: `http://localhost:8001/` (no ngrok tunneling required since the Inspector runs locally).
5. Click **Inspect** to verify that:
   - The Agent Card is successfully retrieved and parsed.
   - The JSON-RPC specification checks pass.
   - You can send a live test message (e.g. asking for issue status) and inspect the raw JSON-RPC request and response payloads in the debug console.
