## LangGraph Multi-Agent Orchestration

This project demonstrates composable agent workflow using [LangGraph](https://github.com/langchain-ai/langgraph):

- **/analyze_graph** endpoint orchestrates:
    1. **Retriever Node:** Calls the Retriever microservice to fetch top-k relevant market context.
    2. **Risk Extraction Node:** Scans the retrieved context for lines mentioning "risk," "exposure," or "allocation."
    3. **LLM Node:** Synthesizes a concise, spoken-style market brief, combining the context and extracted risk highlights using Groq Llama 3.3 70B.

This structure allows for robust, auditable financial brief generation and is MCP-compliant for multi-agent workflow.

### API Endpoints

- `POST /analyze_graph`: Returns a portfolio manager-style brief using orchestrated agent flow (LangGraph).
- `POST /analyze`: Returns a market brief using a direct retriever + LLM call (no explicit orchestration).

