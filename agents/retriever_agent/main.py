import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# ----------------------- Logging Setup ----------------------
logger = logging.getLogger("retriever_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------- Environment Config ----------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "finance")
EMBED_MODEL = os.getenv("EMBED_MODEL1", "all-MiniLM-L6-v2")  # Default to a commonly used model

if not PINECONE_API_KEY:
    logger.error("Missing Pinecone API key in environment variables.")
    raise RuntimeError("PINECONE_API_KEY is required")

# ---------------------- Pinecone Initialization ----------------------
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
except Exception as e:
    logger.error(f"Failed to initialize Pinecone index '{PINECONE_INDEX}': {e}")
    raise

# ---------------------- Embedder Initialization ----------------------
try:
    logger.info(f"Loading embedding model: {EMBED_MODEL}")
    embedder = SentenceTransformer(EMBED_MODEL)
except Exception as e:
    logger.error(f"Failed to load embedding model '{EMBED_MODEL}': {e}")
    raise RuntimeError(f"Failed to load embedder: {e}")

# ---------------------- FastAPI Initialization ----------------------
app = FastAPI(title="Retriever Agent – Pinecone")

# ---------------------- Pydantic Schemas ----------------------
class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5

class Chunk(BaseModel):
    text: str
    source: Optional[str] = ""
    offset: Optional[int] = 0
    score: Optional[float] = 0.0

class RetrieveResponse(BaseModel):
    query: str
    results: List[Chunk]

# ---------------------- Retrieval Endpoint ----------------------
@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    logger.info(f"Received query: '{req.query}', top_k={req.top_k}")

    # Step 1: Embed the query
    try:
        query_vector = embedder.encode([req.query], convert_to_numpy=True)[0].tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    # Step 2: Query Pinecone
    try:
        pinecone_results = index.query(
            vector=query_vector,
            top_k=req.top_k,
            include_metadata=True
        )
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pinecone query failed: {str(e)}")

    # Step 3: Parse results
    results = []
    for match in pinecone_results.matches:
        meta = match.metadata or {}
        results.append(Chunk(
            text=meta.get("text", ""),
            source=meta.get("source", ""),
            offset=meta.get("offset", 0),
            score=match.score
        ))

    logger.info(f"Returning {len(results)} results for query: '{req.query}'")
    return RetrieveResponse(query=req.query, results=results)
