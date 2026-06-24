import streamlit as st
import uuid
from deepeval.tracing import trace, update_current_trace
import sys
import os

# Set page config for premium look
st.set_page_config(
    page_title="Orange Support Agent",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design & Micro-animations
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background: linear-gradient(135deg, #121214 0%, #1a1a24 100%);
        color: #e2e8f0;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Header styling */
    .app-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff7e5f 0%, #feb47b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    /* Card design for metrics/info */
    .info-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Custom status indicators */
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.375rem;
        margin-right: 0.5rem;
    }
    .badge-primary {
        background-color: rgba(249, 115, 22, 0.2);
        color: #ff7e5f;
        border: 1px solid rgba(249, 115, 22, 0.4);
    }
    .badge-success {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }
    
    /* Chat area custom adjustments */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
    }
</style>
""", unsafe_allow_html=True)

# Add parent dir to path so we can import properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from support_agent.agent import create_support_crew
from config import JIRA_A2A_ENDPOINT, MODEL_ID, CONFIDENT_AI_API_KEY

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = f"agent-{str(uuid.uuid4())[:8]}"

# Sidebar UI
with st.sidebar:
    st.image("https://img.icons8.com/color/96/orange.png", width=60)
    st.markdown("<h2 style='color: #ff7e5f; font-weight: 700; margin-top: 0;'>Settings</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Connection details
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    st.markdown(f"**Jira A2A Endpoint:**\n`{JIRA_A2A_ENDPOINT}`")
    st.markdown(f"**Model ID:**\n`{MODEL_ID}`")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tracing status
    st.markdown("<h3 style='font-size: 1.1rem;'>Observability</h3>", unsafe_allow_html=True)
    if CONFIDENT_AI_API_KEY:
        st.markdown('<span class="badge badge-success">✓ Connected</span> Confident AI Tracing', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-primary">⚠ Disabled</span> API key missing', unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Main Layout
st.markdown("<div class='app-header'>🍊 Orange Electronics Support Portal</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Unified Workspace: PDF Policy Search & A2A Jira Issue Management</div>", unsafe_allow_html=True)

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User prompt entry
if query := st.chat_input("Ask a policy question or check a Jira ticket..."):
    # Render user query
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Render assistant output spinner
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        status_placeholder = st.empty()
        
        with st.spinner("Processing query..."):
            trace_kwargs = {
                "thread_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "input": query,
                "name": "Support Agent Query Execution"
            }
            
            try:
                # Wrap execution in Confident AI tracing
                with trace(**trace_kwargs):
                    status_placeholder.markdown("🔍 Checking rules and delegating tasks...")
                    
                    crew = create_support_crew()
                    result = crew.kickoff(inputs={"query": query})
                    
                    response_text = str(result.raw)
                    update_current_trace(output=response_text)
                
                # Render response
                status_placeholder.empty()
                response_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                status_placeholder.empty()
                error_msg = f"❌ **An error occurred:** {str(e)}"
                response_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
