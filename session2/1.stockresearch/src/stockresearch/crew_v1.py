import asyncio  # noqa: I001
import os

from .utils.crew_executor import execute_crew

from crewai import LLM, Agent, Crew, Task
from crewai_tools import TavilySearchTool

from .tools.date_tool import GetCurrentDateTool
from .utils import (
    bedrock_patches,  # noqa: F401 — applies Bedrock monkey-patches on import
)

generalist_agent = Agent(
    role="Generalist Agent",
    goal="Answer general questions based on user query",
    backstory="",
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[GetCurrentDateTool(), TavilySearchTool()],
)

user_query_task = Task(
    description="{user_query}", expected_output="", agent=generalist_agent
)

crew = Crew(agents=[generalist_agent], tasks=[user_query_task], verbose=True)


async def run():
    execute_crew(crew)


if __name__ == "__main__":
    asyncio.run(run())
