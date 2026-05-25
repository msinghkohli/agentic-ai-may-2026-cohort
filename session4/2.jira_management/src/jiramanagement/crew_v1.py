import asyncio
import base64
import os

from .utils.crew_executor import execute_crew
from crewai import Agent, Crew, Task, LLM, Process
from crewai_tools import MCPServerAdapter
from .utils import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import


def create_crew():
    atlassian_email = os.environ["ATLASSIAN_EMAIL"]
    atlassian_api_key = os.environ["ATLASSIAN_API_KEY"]
    atlassian_token = base64.b64encode(
        f"{atlassian_email}:{atlassian_api_key}".encode()
    ).decode()
    server_params = {
        "url": "https://mcp.atlassian.com/v1/mcp",
        "transport": "streamable-http",
        "headers": {"Authorization": f"Basic {atlassian_token}"},
    }

    all_tools = MCPServerAdapter(server_params).tools
    llm = LLM(model=os.environ["MODEL_ID"])

    atlassian_agent = Agent(
        role="Atlassian Assistant",
        goal="Complete any Jira and Confluence task using the available Atlassian tools.",
        backstory=(
            "You are a generalist Atlassian assistant with full access to Jira and Confluence. "
            "You read, create, update, and manage issues, pages, and spaces as needed."
        ),
        llm=llm,
        tools=all_tools,
        allow_delegation=False,
    )

    atlassian_task = Task(
        description=(
            "Complete the following Atlassian request:\n"
            "{jira_request}"
        ),
        expected_output="A clear summary of what was done, including any issue or page IDs created or modified.",
        agent=atlassian_agent,
    )

    return Crew(
        agents=[atlassian_agent],
        tasks=[atlassian_task],
        process=Process.sequential,
        verbose=True,
    )


async def run():
    execute_crew(create_crew())


if __name__ == "__main__":
    asyncio.run(run())
