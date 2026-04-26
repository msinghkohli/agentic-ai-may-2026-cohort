# Session 3 - RAG — Assignments

## Assignment 1: AWS Knowledge Base with Vector Store

**Project:** [1.knowledgebase/](1.knowledgebase/)

Build, test, and evaluate an AWS Bedrock Knowledge Base backed by a vector store. You will upload the provided employee handbook to S3, configure semantic chunking and an embedding model, synchronize the knowledge base, and run a formal evaluation using the provided JSONL dataset.

See the [full instructions](1.knowledgebase/README.md) to get started.

### Questions to Reflect On

- How does semantic chunking differ from fixed-size chunking? Did you see a difference in the relevance of retrieved passages?
- Which evaluation metrics mattered most for an HR policy use case, and why?
---

## Assignment 2: Employee Policy Crew

**Project:** [2.employeepolicy/](2.employeepolicy/)

Connect a crewAI HR Manager agent to the Bedrock Knowledge Base you built in Assignment 1. The agent answers employee policy questions by retrieving relevant passages from the handbook using RAG.

See the [full instructions](2.employeepolicy/README.md) to get started.

### Questions to Reflect On

- How many iterations did the ReAct loop take? Did the agent call the KB tool more than once? Why might it need to?
- How does the answer quality differ between querying the LLM directly versus grounding it in the retrieved handbook passages?