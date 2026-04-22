import os
from crewai import Agent, Crew, Task, LLM
from crewai_tools import BedrockKBRetrieverTool
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import

hr_manager = Agent(
    role="HR Manager",
    goal="Answer the queries from employees on company policies",
    backstory=(
        "You're a seasoned HR Manager. Known to politly reply to queries form the employees "
        "pertaining to the employee policies. You are also known to reply concisely."
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    tools=[
        BedrockKBRetrieverTool(
            knowledge_base_id="NM62ZJLEYX",
            retrieval_configuration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 20,
                    "rerankingConfiguration": {
                        "type": "BEDROCK_RERANKING_MODEL",
                        "bedrockRerankingConfiguration": {
                            "modelConfiguration": {
                                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/cohere.rerank-v3-5:0"
                            },
                            "numberOfRerankedResults": 5
                        }
                    }
                }
            }
        )
    ]
)

handbook_query_task = Task(
    description=(
        "Go through the employee handbook to answer employee queries related to the policies.\n"
        "EMPLOYEE_QUERY: {employee_query}\n"
    ),
    expected_output=(
        "A detailed answer to the employee query in plain text. The response should be "
        "empathetic, concise and polite irrespective of the frustration level of the employee"
    ),
    agent=hr_manager
)

crew = Crew(
    agents=[hr_manager],
    tasks=[handbook_query_task],
    verbose=True
)
