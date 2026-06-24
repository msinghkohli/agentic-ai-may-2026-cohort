import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server Ports
JIRA_A2A_PORT = int(os.getenv("JIRA_A2A_PORT", 8001))
SUPPORT_UI_PORT = int(os.getenv("SUPPORT_UI_PORT", 8501))

# Security Token (Static Bearer Token)
A2A_BEARER_TOKEN = os.getenv("A2A_BEARER_TOKEN", "OrangeJiraToken")

# A2A Endpoint URLs
JIRA_A2A_ENDPOINT = os.getenv("JIRA_A2A_ENDPOINT", f"http://localhost:{JIRA_A2A_PORT}/")

# Model Configuration
MODEL_ID = os.getenv("MODEL_ID", "bedrock/us.anthropic.claude-3-5-sonnet-20240620-v1:0")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
INDEX_DIR = os.path.join(BASE_DIR, "data", "indexes")

os.makedirs(INDEX_DIR, exist_ok=True)

# Tracing Configuration (Confident AI)
CONFIDENT_API_KEY = os.getenv("CONFIDENT_API_KEY")

def setup_tracing():
    """Configures Confident AI tracing if API key is provided."""
    if CONFIDENT_API_KEY:
        from deepeval.integrations.crewai import instrument_crewai
        instrument_crewai()
        print("Confident AI CrewAI instrumentation enabled.")
    else:
        print("Confident AI API Key not found. Tracing disabled.")
