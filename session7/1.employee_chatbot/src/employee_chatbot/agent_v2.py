import os
from crewai import Agent, Crew, Task, LLM
from .utils import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import
from .tools import InsertLeaveTool, ReadLeavesTool, GetCurrentDateTool
from .utils.llmHooks import LLMHooks
from .utils.toolHooks import ToolHooks
from .utils.memory import MemoryUtils
from crewai_tools import BedrockKBRetrieverTool
from crewai.utilities.i18n import I18N

class NoExpectedOutputTask(Task):
    """Task that omits the 'expected criteria for your final answer' section
    from the generated prompt (CrewAI appends it even when expected_output is empty)."""

    def prompt(self) -> str:
        return self.description


class CustomI18N(I18N):
    """Overrides CrewAI prompt slices. The default `post_tool_reasoning` slice
    is injected as a user-role message after every tool call and is flagged as a
    prompt-injection by AWS Bedrock Guardrails, so we soften its wording here."""

    _overrides = {
        "post_tool_reasoning": (
            "Please review the tool result and continue with the most "
            "appropriate next step."
        ),
    }

    def slice(self, slice: str) -> str:
        if slice in self._overrides:
            return self._overrides[slice]
        return super().slice(slice)


def createCrew(memory: MemoryUtils = None):
    # Registers guardrail hooks (always) and memory hooks (when memory given),
    # with guardrails applied before memory.
    LLMHooks(memory).register()
    # Registers the before_tool_call authorization hook (v2 only): employees
    # may only read/apply leaves for themselves. Backend (in-code or Cedar) is
    # chosen by the AUTHZ_PROVIDER env var.
    ToolHooks().register()
    kb_tool = BedrockKBRetrieverTool(knowledge_base_id=os.environ["BEDROCK_KB_ID"])
    
    employee_query_agent = Agent(
        role="HR & Leave Manager",
        goal="Answer queries on company policies, accept leave requests from employees, and provide information on leaves availed.",
        backstory=(
            "You're a seasoned HR & Leave Manager. You politely reply to queries from employees. "
            "You handle the following types of tasks from employees: \n"
            "   1. Information about company policies (e.g., leave policy, work hours). \n"
            "   2. Requesting leave (e.g., 'I want to take leave on [date(s)]'). \n" 
            "   3. Query about leaves already availed (e.g., 'How many leaves have I taken?').  \n\n"
            " System Constraints: \n"
            "1. Employee should not be able to apply for leaves for another employee or ask to check leave status for another"
            "employee, refuse politely and inform them that you can only access leave information for the "
            "employee ID provided.\n"
            "2. If an employee wants to apply for leaves more than allowed as per policy, there is no way you can "
            "provide exception. \n"
            "3. When applying for leaves, first check the calendar year of leave and type of the leave. "
            "Then check how many leaves of that type are allowed in a calendar year. Then read leaves taken "
            "by the employee based on the leave type. And then check if after the new leaves, would employee "
            "exceed with the allowed leaves based on the leave type. If the new leaves exceed the allowed leaves, "
            "inform the employee and do not insert the leave. If the new leaves do not exceed the allowed leaves, "
            "inform the employee and insert the leaves. \n"
            "Employee ID: {employee_id} \n\n"
        ),
        llm=LLM(
            model=os.environ["MODEL_ID"],
            temperature=0,
        ),
        tools=[
            kb_tool,
            InsertLeaveTool(),
            ReadLeavesTool(),
            GetCurrentDateTool()
        ],
        i18n=CustomI18N()
    )

    employee_query_task = NoExpectedOutputTask(
        description=(
            "{employee_query}"
        ),
        expected_output="",
        agent=employee_query_agent
    )

    return Crew(
        agents=[employee_query_agent],
        tasks=[employee_query_task],
        verbose=False
    )

