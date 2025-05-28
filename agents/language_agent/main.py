import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_groq import ChatGroq
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("language_agent")

# Load environment variables (for GROQ_API_KEY)
load_dotenv()

app = FastAPI(title="Language Agent – Market Analysis")

class AnalyzeRequest(BaseModel):
    question: str
    context: str = ""   # <-- Accept context from orchestrator!

class AnalyzeResponse(BaseModel):
    answer: str

class SymbolExtractRequest(BaseModel):
    question: str

class SymbolExtractResponse(BaseModel):
    symbols: list[str]
    details: list[dict]  # Each dict: symbol, cik, filing_type

 



# --- Groq Llama 3.1/3.3 70B Instruct setup ---
try:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        logger.error("GROQ_API_KEY is missing from environment! Please check your .env file.")
    llm = ChatGroq(
        groq_api_key=groq_key,
        model_name="llama3-70b-8192",
        temperature=0.5,
        max_tokens=1024
    )
except Exception as e:
    logger.error(f"Error initializing Groq LLM: {e}")
    llm = None



@app.post("/extract_symbols", response_model=SymbolExtractResponse)
async def extract_symbols(req: SymbolExtractRequest):
    logger.info(f"Received extract_symbols request: {req.question}")

    # --- Load ticker->CIK mapping ONCE (as explained before) ---
    import json
    TICKER_TO_CIK = {}
    with open("data_ingestion/company_tickers.json", "r") as f:
        data = json.load(f)
        for entry in data.values():
            TICKER_TO_CIK[entry["ticker"].upper()] = str(entry["cik_str"]).zfill(10)

    # Prompt LLM for up to 3 tickers, Python list only
    prompt = (
        "You are a financial data extraction assistant. Given a financial question, "
        "extract the most relevant (up to 3) **US-listed** stock ticker symbols as a valid Python list of strings. "
        "DO NOT add explanation or text. ONLY return the list.\n\n"
        f"Question: {req.question}\n\n"
        "Python list:"
    )

    result = llm.invoke(prompt)
    import ast
    try:
        symbols = ast.literal_eval(result.content)
        if not isinstance(symbols, list):
            symbols = []
    except Exception:
        symbols = []

    # Add CIK + filing_type for each symbol (filing_type 10-K for US, 20-F for foreign)
    details = []
    for s in symbols[:3]:
        cik = TICKER_TO_CIK.get(s.upper())
        # Heuristic: use 20-F for foreign (TSM, BABA, etc.), else 10-K
        filing_type = "20-F" if s.upper() in {"TSM", "BABA", "INFY", "TCEHY"} else "10-K"
        if cik:
            details.append({"symbol": s.upper(), "cik": cik, "filing_type": filing_type})

    return {"symbols": [d["symbol"] for d in details], "details": details}


@app.post("/analyze_graph", response_model=AnalyzeResponse)
async def analyze_graph(req: AnalyzeRequest):
    logger.info(f"LangGraph flow: question={req.question}")
    logger.info(f"Context (truncated): {req.context[:200]}...")

    if not llm:
        logger.error("LLM is not initialized! Check GROQ_API_KEY and initialization.")
        raise HTTPException(500, "LLM not initialized. See server logs.")

    # Compose RAG prompt using both question and full context
  # Compose RAG prompt using both question and full context
    prompt = (
        "You are a professional financial assistant that generates concise, high-quality market briefs for portfolio managers. "
        "You have access to multi-source context from APIs, earnings transcripts, SEC filings, and a vector knowledge base. "
        "Given the following question and context, generate a direct, data-rich response in exactly 2–4 sentences. "
        "The brief must include exposure percentages (if relevant), highlight earnings surprises with figures (e.g., 'beat by 4%'), "
        "summarize regional or sector sentiment, and focus on *actionable insights*. "
        "Avoid vague or generic commentary. Do not include any preamble or explanation—respond only with the brief.\n\n"
        f"Context:\n{req.context}\n\n"
        f"Question:\n{req.question}\n\n"
        "Market Brief:"
    )


    try:
        answer = llm.invoke(prompt)
        logger.info("Answer synthesized.")
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}", exc_info=True)
        raise HTTPException(500, f"LLM generation failed: {e}")

    return AnalyzeResponse(answer=answer.content if hasattr(answer, "content") else str(answer))

@app.get("/ping")
def ping():
    return {"msg": "language agent up"}

