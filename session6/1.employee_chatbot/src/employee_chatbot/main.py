#!/usr/bin/env python
import warnings
import re
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from . crew import createCrew
from rich.console import Console
from rich.markdown import Markdown
import uuid
from .utils.memory import MemoryUtils
from deepeval.integrations.crewai import instrument_crewai
from deepeval.tracing import trace, update_current_trace

instrument_crewai()

EMPLOYEE_ID_PATTERN = re.compile(
    r"[a-zA-Z0-9][a-zA-Z0-9-_/]*(?::[a-zA-Z0-9-_/]+)*[a-zA-Z0-9-_/]*"
)

def run():
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    while True:
        employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
        if EMPLOYEE_ID_PATTERN.fullmatch(employee_id):
            break
        console.print("[bold red]Invalid Employee ID. Please try again.[/bold red]")
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

    while True:
        query = console.input("[bold blue]You:[/bold blue] ")
        if query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        try:
            trace_kwargs = {
                "thread_id": session_id,
                "user_id": employee_id,
                "input": query,
                "name": "Employee Chatbot Interaction"
            }

            with trace(**trace_kwargs):
                conversationHistory = memoryUtils.loadShortTermMemory()
                conversationSummary = memoryUtils.extractSummary(query=query)
                inputs = {
                    'employee_query': query,
                    'employee_id': employee_id,
                    'conversationHistory': conversationHistory,
                    'conversationSummary': conversationSummary
                }
                crew = createCrew()
                response = crew.kickoff(inputs=inputs).raw
                update_current_trace(output=response)
                
                memoryUtils.saveMemory(userPrompt=query, assistantResponse=response)
                console.print("\n[bold green]Chatbot:[/bold green]")
                console.print(Markdown(response))
                console.print("\n" + "-"*50 + "\n")
        except Exception as e:
            console.print(f"[bold red]An error occurred while running the crew: {e}[/bold red]")

if __name__ == "__main__":
    run()
