from bedrock_agentcore import BedrockAgentCoreApp
from openinference.instrumentation.crewai import CrewAIInstrumentor
from opentelemetry import context as otel_context, trace
from . crewWithPlanner import crew

# Create AgentCore App
app = BedrockAgentCoreApp()

# Setup CrewAI instrumentation
CrewAIInstrumentor().instrument(skip_dep_check=True)

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