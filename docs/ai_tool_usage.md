## LangGraph Workflow Usage Log

- Integrated [LangGraph](https://github.com/langchain-ai/langgraph) for explicit multi-step agent orchestration.
- Workflow:
    - Step 1: Retrieve context (via Retriever Agent API).
    - Step 2: Extract risk/exposure phrases (risk extraction node).
    - Step 3: Synthesize natural language brief (LLM node using Groq Llama 3.3 70B).
- Benefits: Modular, traceable, and compliant with modern compositional agent requirements (MCP).
- All key orchestration and node transitions are logged using Python's logging module for transparency and debugging.
