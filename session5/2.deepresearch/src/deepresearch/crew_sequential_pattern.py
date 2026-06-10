import asyncio  # noqa: I001
import os

from .utils.crew_executor import execute_crew

from crewai import LLM, Agent, Crew, Process, Task
from crewai_tools import TavilyExtractorTool, TavilySearchTool
from pydantic import BaseModel, Field
from .utils import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import


# --- Planning ----------------------------------------------------------------

deep_research_planner = Agent(
    role="Deep Research Planner",
    goal=(
        "Decompose a broad research question into 2 precise, non-overlapping sub-question "
        "that together provide comprehensive coverage of the question."
    ),
    backstory=(
        "You are an expert research strategist with a background in academic literature review "
        "and investigative journalism. You excel at identifying the key dimensions of a complex "
        "question and formulating targeted questions that will yield actionable insights when "
        "answered independently and then synthesized. You think like an editor commissioning "
        "a cover story: what are the essential angles a reader needs to understand the full picture? "
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[TavilySearchTool()],
)


class ResearchPlan(BaseModel):
    sub_questions: list[str] = Field(
        ..., description="Exactly 2 precise, non-overlapping sub-questions"
    )


planning_task = Task(
    description=(
        "USER QUERY: {user_query}\n\n"
        "Decompose the user query into exactly 2 precise, non-overlapping sub-questions "
        "that together cover the topic comprehensively."
    ),
    expected_output="A research plan containing exactly 2 sub-questions.",
    agent=deep_research_planner,
    output_pydantic=ResearchPlan,
)


# --- Research ----------------------------------------------------------------

def make_researcher_agent() -> Agent:
    return Agent(
        role="Deep Research Investigator",
        goal=(
            "Research a specific research sub-question thoroughly using web search and URL content extraction. "
            "Produce a comprehensive findings summary with full source citations. "
            "It is important that you don't rely on your knowledge, rather rely on information searched "
            "and extracted from the internet. "
            "When extracting URL content, limit extraction to the top one most relevant URL per sub-question — "
            "do not extract content from every search result. "
        ),
        backstory=(
            "You are a skilled investigative researcher who gathers primary source evidence using "
            "web search and content extraction. You are meticulous about citing sources — for every claim "
            "you make, you record the source URL, the exact excerpt that supports the claim. "
            "You never rely on prior knowledge: every fact must be grounded in a source retrieved "
            "during this session. You prioritize authoritative sources such as academic papers, "
            "peer-reviewed journals, government reports, and reputable industry publications. "
        ),
        llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
        tools=[TavilySearchTool(), TavilyExtractorTool()],
    )


researcher_agent_1 = make_researcher_agent()
researcher_agent_2 = make_researcher_agent()


class Source(BaseModel):
    url: str
    excerpt: str = Field(..., description="Exact excerpt supporting the findings")


class ResearchFindings(BaseModel):
    sub_question: str
    findings: str = Field(..., description="Comprehensive findings summary")
    sources: list[Source]


research_task_1 = Task(
    description=(
        "Research the FIRST sub-question from the research plan. Gather evidence with web search "
        "and content extraction, and ground every finding in a retrieved source."
    ),
    expected_output="Findings for the first sub-question with cited sources.",
    agent=researcher_agent_1,
    context=[planning_task],
    output_pydantic=ResearchFindings,
)

research_task_2 = Task(
    description=(
        "Research the SECOND sub-question from the research plan. Gather evidence with web search "
        "and content extraction, and ground every finding in a retrieved source."
    ),
    expected_output="Findings for the second sub-question with cited sources.",
    agent=researcher_agent_2,
    context=[planning_task],
    output_pydantic=ResearchFindings,
)


# --- Writing -----------------------------------------------------------------

writer_agent = Agent(
    role="Research Article Writer",
    goal=(
        "Write a structured, authoritative 1000-1500 word research article based on the provided "
        "research and synthesizing findings into a cohesive narrative with proper inline citations. "
    ),
    backstory=(
        "You are a professional science and technology writer with experience writing for "
        "publications like MIT Technology Review and Wired. You write in clear, precise prose, "
        "cite every factual claim with its source URL in the format [Source: URL], and structure "
        "articles with a compelling introduction, logically ordered body sections aligned to the "
        "research plan, and a concise conclusion. You never invent facts — everything you write "
        "is grounded in sources retrieved from the knowledge base. When critic feedback is "
        "provided, you address every point specifically and improve the article accordingly. "
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
)


class Article(BaseModel):
    title: str
    body_markdown: str = Field(
        ..., description="Full article in markdown with [Source: URL] citations"
    )


writing_task = Task(
    description=(
        "Write a 1000-1500 word research article in markdown for the query '{user_query}', "
        "synthesizing both research findings with inline [Source: URL] citations."
    ),
    expected_output="A complete markdown research article with a title and inline citations.",
    agent=writer_agent,
    context=[research_task_1, research_task_2],
    output_pydantic=Article,
)


# --- Critique ----------------------------------------------------------------

critic_agent = Agent(
    role="Research Article Critic",
    goal=(
        "Review a research article draft for factual support, structural quality, citation "
        "completeness, and logical coherence. Produce a structured critique with specific "
        "actionable revision instructions, or output APPROVED if ready for publication. "
    ),
    backstory=(
        "You are a rigorous peer reviewer and editorial standards enforcer with experience "
        "in academic publishing and long-form journalism. You identify unsupported claims, "
        "structural weaknesses, missing perspectives, and citation gaps. Your critiques are "
        "specific and constructive: you flag exact sentences or sections that need revision "
        "and explain precisely how to fix them. You understand that the article should cite "
        "every factual claim with [Source: URL] format. You output blank string only when the "
        "article meets high publication standards. "
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[TavilySearchTool()],
)


class Critique(BaseModel):
    approved: bool
    feedback: list[str] = Field(
        ..., description="Specific, actionable revision points; empty if approved"
    )


critique_task = Task(
    description=(
        "Critically review the draft article for factual support, citation completeness, "
        "structure, and coherence. Approve it or list specific, actionable revision points."
    ),
    expected_output="A critique with an approval flag and a list of feedback points.",
    agent=critic_agent,
    context=[writing_task],
    output_pydantic=Critique,
)


# --- Revision ----------------------------------------------------------------

reviser_agent = Agent(
    role="Research Article Reviser",
    goal=(
        "Produce the final, publication-ready research article by incorporating every point of "
        "the critic's feedback into the writer's draft."
    ),
    backstory=(
        "You are a seasoned editor who takes a draft article together with a reviewer's critique "
        "and turns them into a polished final piece. You address each feedback point concretely, "
        "preserve the draft's well-supported content and [Source: URL] citations, and never "
        "introduce unsupported claims. If the critique already approves the draft, you return it "
        "essentially unchanged. "
    ),
    llm=LLM(model=os.environ["MODEL_ID"], temperature=0.0),
    tools=[TavilySearchTool()],
)


revision_task = Task(
    description=(
        "Revise the draft article by incorporating the critic's feedback, then return the final "
        "article. If the critique approves the draft, return it essentially unchanged."
    ),
    expected_output="The final, polished markdown research article with a title.",
    agent=reviser_agent,
    context=[writing_task, critique_task],
)


crew = Crew(
    agents=[
        deep_research_planner,
        researcher_agent_1,
        researcher_agent_2,
        writer_agent,
        critic_agent,
        reviser_agent,
    ],
    tasks=[
        planning_task,
        research_task_1,
        research_task_2,
        writing_task,
        critique_task,
        revision_task,
    ],
    process=Process.sequential,
    verbose=True,
)


async def run():
    execute_crew(crew)


if __name__ == "__main__":
    asyncio.run(run())
