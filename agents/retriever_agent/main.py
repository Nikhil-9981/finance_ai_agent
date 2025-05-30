import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pinecone import Pinecone
import cohere

# Logging
logger = logging.getLogger("retriever_agent")
logging.basicConfig(level=logging.INFO)

# Config from environment
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "finance")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Initialize Cohere client
co = cohere.Client(COHERE_API_KEY)

# FastAPI setup
app = FastAPI(title="Retriever Agent – Pinecone + Cohere Embeddings")

# Pydantic models
class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5

class Chunk(BaseModel):
    text: str
    source: str = ""
    offset: int = 0
    score: float = 0.0

class RetrieveResponse(BaseModel):
    query: str
    results: list[Chunk]

# Endpoint
@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    logger.info(f"Received query: {req.query}, top_k={req.top_k}")

    # Embed the query with Cohere API
    try:
        response = co.embed(texts=[req.query], model="embed-english-v2.0")
        q_emb = response.embeddings[0]  # list of floats
    except Exception as e:
        logger.error(f"Cohere embedding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cohere embedding failed: {e}")

    # Query Pinecone index
    try:
        pinecone_results = index.query(
            vector=q_emb,
            top_k=req.top_k,
            include_metadata=True
        )
        results = []
        for match in pinecone_results.matches:
            meta = match.metadata or {}
            results.append(Chunk(
                text=meta.get("text", ""),
                source=meta.get("source", ""),
                offset=meta.get("offset", 0),
                score=match.score
            ))
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pinecone query failed: {e}")

    logger.info(f"Returning {len(results)} results for query: {req.query}")
    return RetrieveResponse(query=req.query, results=results)
