import asyncio  # noqa: I001
import os

from .utils.crew_executor import execute_crew

from crewai import LLM, Agent, Crew, Process, Task
from crewai_tools import TavilySearchTool

from .tools.date_tool import GetCurrentDateTool
from .tools.stock_tool import GetStockPriceTool
from .utils import (
    bedrock_patches,  # noqa: F401 — applies Bedrock monkey-patches on import
)

stock_research_agent = Agent(
    role="Senior Financial Research Analyst",
    goal="Answers queries related to stock prices and financial analysis",
    backstory=(
        "You are a Senior Financial Research Analyst with expertise in stock market "
        "analysis. You have a knack of fetching historical stock data to provide "
        "accurate analysis based on the user query. You provide the analysis in a "
        "clear, concise format. If doing comparison of stock price, include the "
        "closing prices for the dates, the dollar difference, and the percentage "
        "change. Present the numerical data in a markdown table."
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[GetCurrentDateTool(), GetStockPriceTool()],
)

generalist_agent = Agent(
    role="Generalist Agent",
    goal="Answer general questions based on user query",
    backstory=(
        "You are a generalist agent with expertise in answering general questions "
        "based on user query. You have a knack of fetching general information to "
        "provide accurate answers based on the user query. You provide the answers "
        "in a clear, concise format."
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[GetCurrentDateTool(), TavilySearchTool()],
)

manager_agent = Agent(
    role="Manager Agent",
    goal=(
        "Understand the intent of user query and delegate it to the right specialist. "
        "If the query is related to comparing a stock price historically, or "
        "comparing prices of multiple stocks on a given date, then delegate it to "
        "the Senior Financial Research Analyst. Otherwise, delegate it to the "
        "Generalist Agent."
    ),
    backstory=(
        "You are a manager who has led large teams at top-tier companies. You do "
        "not do the work/analysis yourself — you assign the right work to the right "
        "specialist, review their outputs for completeness, and coordinate "
        "handoffs between specialists."
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    allow_delegation=True,
)

user_query_task = Task(description="{user_query}", expected_output="")

crew = Crew(
    agents=[stock_research_agent, generalist_agent],
    tasks=[user_query_task],
    manager_agent=manager_agent,
    process=Process.hierarchical,
    verbose=True,
)


async def run():
    execute_crew(crew)


if __name__ == "__main__":
    asyncio.run(run())
