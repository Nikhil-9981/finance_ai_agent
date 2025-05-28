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
 



# --- Groq Llama 3.1/3.3 70B Instruct setup ---
try:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        logger.error("GROQ_API_KEY is missing from environment! Please check your .env file.")
    llm = ChatGroq(
        groq_api_key=groq_key,
        model_name="llama3-70b-8192",
        temperature=0.3,
        max_tokens=1024
    )
except Exception as e:
    logger.error(f"Error initializing Groq LLM: {e}")
    llm = None

@app.post("/analyze_graph", response_model=AnalyzeResponse)
async def analyze_graph(req: AnalyzeRequest):
    logger.info(f"LangGraph flow: question={req.question}")
    logger.info(f"Context (truncated): {req.context[:200]}...")

    if not llm:
        logger.error("LLM is not initialized! Check GROQ_API_KEY and initialization.")
        raise HTTPException(500, "LLM not initialized. See server logs.")

    # Compose RAG prompt using both question and full context
    prompt = (
        "You are a market analysis AI assistant. "
        "Given the following context extracted from multiple agents (API, SEC filings, vector KB), "
        "write a concise market brief for a portfolio manager, focusing on risk exposure in Asia tech stocks and any earnings surprises.\n\n"
        f"Context:\n{req.context}\n\n"
        f"Question: {req.question}\n\n"
        f"Market Brief:"
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


@app.post("/extract_symbols", response_model=SymbolExtractResponse)
async def extract_symbols(req: SymbolExtractRequest):
    prompt = (
        "Extract the most relevant  stock ticker symbols (as a Python list of strings) from this question: "
        f"{req.question}\n\nJust return the Python list, nothing else."
    )
    result = llm.invoke(prompt)
    # Parse the returned string safely
    import ast
    try:
        symbols = ast.literal_eval(result.content)
    except Exception:
        symbols = []
    return SymbolExtractResponse(symbols=symbols)