#!/usr/bin/env python
import base64
import os
import warnings

from dotenv import load_dotenv
from openinference.instrumentation.crewai import CrewAIInstrumentor
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from rich.console import Console
from rich.markdown import Markdown

from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import
from .llm_otel_listener import LLMOtelListener

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

if os.getenv("LANGFUSE_PUBLIC_KEY"):
    # Set up OTEL -> Langfuse exporter BEFORE crewai imports
    langfuse_public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    langfuse_secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    langfuse_host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    auth_header = base64.b64encode(
        f"{langfuse_public_key}:{langfuse_secret_key}".encode()
    ).decode()

    exporter = OTLPSpanExporter(
        endpoint=f"{langfuse_host}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {auth_header}"},
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    otel_trace.set_tracer_provider(provider)

    # Instrument CrewAI orchestration spans (agents, tasks, crew)
    CrewAIInstrumentor().instrument()

    # Subscribe to CrewAI's event bus to create OTEL spans for LLM calls.
    # CrewAI 0.186+ uses provider-native SDKs (e.g. AnthropicCompletion) and
    # bypasses litellm entirely, so litellm instrumentation has no effect.
    # The event bus is the only reliable hook into LLM calls at this version.
    LLMOtelListener()


def execute_crew(crew):
    tracer = otel_trace.get_tracer("deepresearch")

    console = Console()
    console.print(
        "[bold magenta]Welcome to the Deep Research Chatbot. [/bold magenta]\n"
    )
    user_query = console.input("[bold yellow]User:[/bold yellow] ").strip()
    inputs = {"user_query": user_query}

    with tracer.start_as_current_span("deep-research") as span:
        try:
            span.set_attribute("input", str(inputs))
            response = crew.kickoff(inputs=inputs).raw
            console.print("\n[bold green]Assitant:[/bold green]")
            console.print(Markdown(response))
            span.set_attribute("output", str(response or ""))
        except Exception as e:
            span.record_exception(e)
            console.print(
                "\n[bold green]Assitant: An excepption occurred....[/bold green]"
            )
            console.print(Markdown(str(e)))
            raise Exception(f"An error occurred while running the crew: {e}")
        finally:
            provider.force_flush()
