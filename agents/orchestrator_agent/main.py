import os
import logging
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph
from typing import TypedDict
from datetime import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator_agent")

# Agent endpoints
API_AGENT_URL = os.getenv("API_AGENT_URL", "http://localhost:8001/quote")
SCRAPER_AGENT_URL = os.getenv("SCRAPER_AGENT_URL", "http://localhost:8002/filing")
RETRIEVER_AGENT_URL = os.getenv("RETRIEVER_AGENT_URL", "http://localhost:8003/retrieve")
LANGUAGE_AGENT_URL = os.getenv("LANGUAGE_AGENT_URL", "http://localhost:8004/analyze_graph")

app = FastAPI(title="Orchestrator Agent (LangGraph)")

# ----- State definition for LangGraph -----
 
class MyState(TypedDict):
    question: str
    api_quote: dict
    filing_text: str
    retrieved_chunks: list
    context: str
    answer: str
    symbol_details: list


# ----- Workflow Nodes -----



def save_text_for_faiss(doc_text, base_name="scraped_doc"):
    # Ensure directory exists
    save_dir = "data_ingestion/docs"
    os.makedirs(save_dir, exist_ok=True)
    # Unique filename by timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{ts}.txt"
    with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
        f.write(doc_text)


def api_node(state):
    logger.info("Calling Language Agent to extract symbols...")
    question = state["question"]
    print(question)
    try:
        extract_resp = requests.post( 
            LANGUAGE_AGENT_URL.replace("/analyze_graph", "/extract_symbols"),
            json={"question": question}, timeout=3000
        )
        
        extract_resp.raise_for_status()
        
        symbols = extract_resp.json().get("symbols", [])
        logger.info(f"Extracted symbols: {symbols}")
        if not symbols:
            symbols = ["TSM"]  # fallback if nothing found
    except Exception as e:
        logger.error(f"Symbol extraction failed: {e}")
        symbols = ["TSM"]

    logger.info("Calling API Agent...")
    try:
        resp = requests.post(API_AGENT_URL, json={"symbols": symbols, "history": True, "info": True}, timeout=3000)
        resp.raise_for_status()
        data = resp.json()["results"][0]  # just the first for now, or loop for all
        logger.info(f"API Agent response: {data}")
    except Exception as e:
        logger.error(f"API Agent failed: {e}")
        data = {"symbol": symbols[0], "latest_price": "N/A", "latest_timestamp": "N/A"}
    return {"api_quote": data}

def scraper_node(state):
    logger.info("Calling Scraper Agent...")
    filings = []
    # details were fetched from extract_symbols before!
    details = state.get("symbol_details", [])
    for d in details:
        cik = d["cik"]
        filing_type = d["filing_type"]
        try:
            resp = requests.post(SCRAPER_AGENT_URL, json={"cik": cik, "filing_type": filing_type}, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            filing_text = data.get("document_text", "")
            logger.info(f"Scraper Agent got filing for {d['symbol']}, length: {len(filing_text)}")
            if filing_text:
                save_text_for_faiss(filing_text, f"{d['symbol']}_{filing_type}")
            filings.append(filing_text)
        except Exception as e:
            logger.error(f"Scraper Agent failed for {d['symbol']}: {e}")
            filings.append("")
    return {"filing_text": "\n\n".join(filings)}



def retriever_node(state):
    logger.info("Calling Retriever Agent...")
    question = state["question"]
    try:
        resp = requests.post(RETRIEVER_AGENT_URL, json={"query": question, "top_k": 3}, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        chunks = data.get("results", [])
        logger.info(f"Retriever Agent returned {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Retriever Agent failed: {e}")
        chunks = []

    # ---- FALLBACK LOGIC HERE ----
    fallback = False
    fallback_message = "Sorry, I could not confidently answer from our knowledge base. Could you clarify or rephrase your question?"

    if not chunks:
        logger.warning("Retriever returned zero results. Triggering fallback.")
        # Mark for fallback
        fallback = True
    else:
        # Look at the first (best) score
        try:
            best_score = chunks[0].get("score", 999999)
            # For FAISS L2, higher means worse match (tune threshold based on your data!)
            if best_score > 400:  # <-- Adjust this number as you see fit!
                logger.warning(f"Retriever score {best_score} is too high (bad match). Triggering fallback.")
                fallback = True
        except Exception as e:
            logger.error(f"Could not extract score from chunk: {e}")
            fallback = True

    if fallback:
        # Instead of moving to next node, SHORT-CIRCUIT the workflow:
        return {
            "retrieved_chunks": [],
            "context": "",
            "answer": fallback_message
        }

    return {"retrieved_chunks": chunks}


def context_builder_node(state):
    if "answer" in state and state["answer"]:
        return {}
    logger.info("Building context for LLM...")
    context_pieces = []
    # Quote
    quote = state.get("api_quote", {})
    print("quote is :", quote)
    context_pieces.append(f"Latest quote for {quote.get('symbol')}: ${quote.get('price')} at {quote.get('timestamp')}")
    # Filing
    filing = state.get("filing_text", "")
    print("fillin is :", filing)
    if filing:
        context_pieces.append(f"Latest SEC Filing: {filing[:2000]}")
    # Retriever
    chunks = state.get("retrieved_chunks", [])
    if chunks:
        context_pieces.append("Knowledge Base Chunks:\n" + "\n".join(chunk.get("text", "") for chunk in chunks))
    full_context = "\n\n".join(context_pieces)
    return {"context": full_context}

def llm_node(state):
    logger.info("Calling Language Agent (LLM)...")
    question = state["question"]
    context = state.get("context", "")
    if "answer" in state and state["answer"]:
        return {}
    try:
        resp = requests.post(LANGUAGE_AGENT_URL, json={"question": question, "context": context}, timeout=3000)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("answer", "No answer.")
        logger.info(f"Language Agent returned answer: {answer[:200]}")
    except Exception as e:
        logger.error(f"Language Agent failed: {e}")
        answer = "Sorry, there was an error generating your market brief."
    return {"answer": answer}

# ---- LangGraph Workflow Definition ----
workflow = (
    StateGraph(state_schema=MyState)
    .add_node("api", api_node)
    .add_node("scraper", scraper_node)
    .add_node("retriever", retriever_node)
    .add_node("context_builder", context_builder_node)
    .add_node("llm", llm_node)
    # Edges
    .add_edge("api", "scraper")
    .add_edge("scraper", "retriever")
    .add_edge("retriever", "context_builder")
    .add_edge("context_builder", "llm")
    .set_entry_point("api")
    .set_finish_point("llm")
    .compile()
)

# ----- FastAPI Endpoint -----
class OrchestrateRequest(BaseModel):
    question: str

class OrchestrateResponse(BaseModel):
    answer: str

@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest):
    logger.info(f"Received orchestrate request: {req.question}")
    state = {"question": req.question}
    result = workflow.invoke(state)
    answer = result["answer"]
    return OrchestrateResponse(answer=answer)

@app.get("/ping")
def ping():
    return {"msg": "orchestrator (langgraph) up"}
