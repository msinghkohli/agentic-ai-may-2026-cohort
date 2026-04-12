# Session 1

## Supporting Material

Browse through these resources to build helpful context before diving into the assignments:

1. **Neural Networks Simply Explained** — What a neural network is and how it learns

   [![Neural Networks](https://img.youtube.com/vi/ER2It2mIagI/0.jpg)](https://www.youtube.com/watch?v=ER2It2mIagI)
2. **Large Language Models (LLMs)** — How LLMs are built on top of neural networks and what makes them powerful

   [![LLMs Explained](https://img.youtube.com/vi/67_aMPDk2zw/0.jpg)](https://www.youtube.com/watch?v=67_aMPDk2zw)

   > **Optional:** For a deeper dive into the Transformer architecture that powers LLMs:
   > [![Transformers Explained](https://img.youtube.com/vi/ZhAz268Hdpw/0.jpg)](https://www.youtube.com/watch?v=ZhAz268Hdpw)
   >
   > **Optional:** The original research paper that introduced the Transformer architecture: [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
   

3. **Python** — A quick introduction to Python for those new to the language

   [![Python Bascis for Beginners](https://img.youtube.com/vi/Ro_MScTDfU4/0.jpg)](https://www.youtube.com/watch?v=Ro_MScTDfU4)
   [![Python Class Methods](https://img.youtube.com/vi/g-qRKZD3FgE/0.jpg)](https://www.youtube.com/watch?v=g-qRKZD3FgE)
   [![What is UV](https://img.youtube.com/vi/5rTwOt9Qgik/0.jpg)](https://www.youtube.com/watch?v=5rTwOt9Qgik)

4. **CrewAI** — How to orchestrate multiple AI agents using the CrewAI framework

   - [CrewAI Introduction](https://docs.crewai.com/en/introduction)
   - [Installation](https://docs.crewai.com/en/installation)
   - [Build Your First Crew](https://docs.crewai.com/en/guides/crews/first-crew)

5. **Langfuse** — How to trace and observe LLM calls and agent reasoning with Langfuse

   - [Langfuse Observability Overview](https://langfuse.com/docs/observability/overview)

## Assignments

### 1. Prompt Engineering
Head over to [prompts/README.md](prompts/README.md) to explore prompt engineering exercises. These cover techniques for writing effective prompts and understanding how small changes in phrasing affect model output.

### 2. Stock Research Project
Head over to [stockresearch/README.md](stockresearch/README.md) to set up and run a CrewAI-powered stock research agent. This project puts the ReAct pattern into practice — you can observe the agent's full reasoning trace in Langfuse. Once it's running, take some time to walk through the code and get familiar with how the agent, tasks, and tools are wired together.
