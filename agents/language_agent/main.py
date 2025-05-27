import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from langchain_groq import ChatGroq
from dotenv import load_dotenv
 
from langgraph.graph import StateGraph
from typing import TypedDict

# Define the state for LangGraph
class MyState(TypedDict):
    question: str
    context: str
    answer: str

logger = logging.getLogger("language_agent")

# Load .env variables (for GROQ_API_KEY)
load_dotenv()

# Log key (do NOT do this in production, for debug only!)
logger.info(f"GROQ_API_KEY in env: {os.environ.get('GROQ_API_KEY')}")

app = FastAPI(title="Language Agent – Market Analysis")

class AnalyzeRequest(BaseModel):
    question: str

class AnalyzeResponse(BaseModel):
    answer: str

RETRIEVER_URL = "http://localhost:8003/retrieve"

# --- Groq Llama 3.1/3.3 70B Instruct setup ---
try:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        logger.error("GROQ_API_KEY is missing from environment! Please check your .env file.")
    llm = ChatGroq(
        groq_api_key=groq_key,
        model_name="llama3-70b-8192",  # This is the Llama-3.1/3.3 70B Instruct (latest)
        temperature=0.7,
        max_tokens=512
    )
except Exception as e:
    logger.error(f"Error initializing Groq LLM: {e}")
    llm = None

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    logger.info(f"Received analysis request: {req.question}")
    logger.info(f"GROQ_API_KEY present: {os.environ.get('GROQ_API_KEY') is not None and len(os.environ.get('GROQ_API_KEY', '')) > 5}")

    # 1. Call Retriever Agent
    try:
        logger.info(f"Querying Retriever Agent: {RETRIEVER_URL}")
        resp = requests.post(RETRIEVER_URL, json={"query": req.question, "top_k": 5}, timeout=30)
        resp.raise_for_status()
        retrieved_chunks = resp.json().get("results", [])
        logger.info(f"Retrieved {len(retrieved_chunks)} context chunks")
    except Exception as e:
        logger.error(f"Retriever Agent call failed: {e}")
        raise HTTPException(502, f"Retriever Agent unavailable or error: {e}")

    if not llm:
        logger.error("LLM is not initialized! Check GROQ_API_KEY and initialization.")
        raise HTTPException(500, "LLM not initialized. See server logs.")

    # 2. Build context for LLM prompt
    context = "\n\n".join(chunk.get("text", "") for chunk in retrieved_chunks)
    logger.info(f"Context for LLM (first 300 chars): {context[:300]!r}")

    # 3. RAG Prompt
    prompt = (
        "You are a market analysis AI assistant. "
        "Given the following context extracted from portfolio and market data, "
        "write a concise market brief for a portfolio manager, "
        "focusing on risk exposure in Asia tech stocks and any earnings surprises.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {req.question}\n\n"
        f"Market Brief:"
    )

    # 4. LLM call (Groq, no local download)
    try:
        logger.info("Invoking Groq Llama 3.1/3.3 70B via LangChain...")
        answer = llm.invoke(prompt)
        logger.info("Answer synthesized.")
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}", exc_info=True)
        raise HTTPException(500, f"LLM generation failed: {e}")

    return AnalyzeResponse(answer=answer.content if hasattr(answer, "content") else str(answer))




# -- LangGraph Orchestration Setup --

def retrieve_node(state):
    logger.info("LangGraph: Calling retriever agent")
    question = state["question"]
    try:
        resp = requests.post(RETRIEVER_URL, json={"query": question, "top_k": 5}, timeout=30)
        resp.raise_for_status()
        retrieved_chunks = resp.json().get("results", [])
        logger.info(f"LangGraph: Retrieved {len(retrieved_chunks)} context chunks")
        context = "\n\n".join(chunk.get("text", "") for chunk in retrieved_chunks)
    except Exception as e:
        logger.error(f"LangGraph: Retriever error: {e}")
        raise Exception(f"Retriever error: {e}")
    # Return as dict (state update)
    return {"question": question, "context": context}

def llm_node(state):
    logger.info("LangGraph: Calling LLM node")
    context = state["context"]
    question = state["question"]
    prompt = (
        "You are a market analysis AI assistant. "
        "Given the following context extracted from portfolio and market data, "
        "write a concise market brief for a portfolio manager, "
        "focusing on risk exposure in Asia tech stocks and any earnings surprises.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Market Brief:"
    )
    answer = llm.invoke(prompt)
    answer_str = answer.content if hasattr(answer, "content") else str(answer)
    logger.info("LangGraph: LLM node finished")
    return {"answer": answer_str}

# Build the LangGraph workflow using StateGraph
workflow = (
    StateGraph(state_schema=MyState)   # <--- Add this!
    .add_node("retrieve", retrieve_node)
    .add_node("llm", llm_node)
    .add_edge("retrieve", "llm")
    .set_entry_point("retrieve")
    .set_finish_point("llm")
    .compile()
)


@app.post("/analyze_graph", response_model=AnalyzeResponse)
async def analyze_graph(req: AnalyzeRequest):
    logger.info(f"LangGraph flow: question={req.question}")
    try:
        # Run workflow
        result = workflow.invoke({"question": req.question})
        return AnalyzeResponse(answer=result["answer"])
    except Exception as e:
        logger.error(f"LangGraph orchestration failed: {e}", exc_info=True)
        raise HTTPException(500, f"LangGraph orchestration failed: {e}")



@app.post("/analyze_simple", response_model=AnalyzeResponse)
async def analyze_simple(req: AnalyzeRequest):
    logger.info(f"[Simple] Received analysis request: {req.question}")

    # 1. Call Retriever Agent
    try:
        logger.info(f"[Simple] Querying Retriever Agent: {RETRIEVER_URL}")
        resp = requests.post(RETRIEVER_URL, json={"query": req.question, "top_k": 5}, timeout=30)
        resp.raise_for_status()
        retrieved_chunks = resp.json().get("results", [])
        logger.info(f"[Simple] Retrieved {len(retrieved_chunks)} context chunks")
    except Exception as e:
        logger.error(f"[Simple] Retriever Agent call failed: {e}")
        raise HTTPException(502, f"Retriever Agent unavailable or error: {e}")

    # 2. Build context for LLM prompt
    context = "\n\n".join(chunk.get("text", "") for chunk in retrieved_chunks)
    logger.info(f"[Simple] Context for LLM (first 300 chars): {context[:300]!r}")

    # 3. RAG Prompt
    prompt = (
        "You are a market analysis AI assistant. "
        "Given the following context extracted from portfolio and market data, "
        "write a concise market brief for a portfolio manager, "
        "focusing on risk exposure in Asia tech stocks and any earnings surprises.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {req.question}\n\n"
        f"Market Brief:"
    )

    # 4. LLM call (RAG answer)
    try:
        logger.info("[Simple] Invoking LLM for RAG answer...")
        answer = llm.invoke(prompt)
        # Handle AIMessage or str result
        if hasattr(answer, "content"):
            answer = answer.content
        logger.info("[Simple] Answer synthesized.")
    except Exception as e:
        logger.error(f"[Simple] LLM invocation failed: {e}")
        raise HTTPException(500, f"LLM generation failed: {e}")

    return AnalyzeResponse(answer=answer)
