import os
import logging
from bedrock_agentcore import BedrockAgentCoreApp
from . crewWithPlanner import crew

logger = logging.getLogger(__name__)

# Create AgentCore App
app = BedrockAgentCoreApp()

# Log all environment variables at startup for diagnostics
logger.info("Environment variables: %s", dict(os.environ))

@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")

    if not prompt:
        raise ValueError("Missing required payload parameters")

    inputs = {
        "user_query": prompt
    }

    try:
        # Trigger the Crew
        response = crew.kickoff(inputs=inputs).raw
    except Exception as e:
        response = "An unknown error occurred while processing your request."

    return response
if __name__ == "__main__":
  app.run()