# agents/retriever_agent/main.py

import os
import pickle

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Config
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data_ingestion/faiss_index")
META_PATH = INDEX_PATH + ".meta"
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# Load FAISS index
if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
    raise RuntimeError(f"Index or metadata missing at {INDEX_PATH}")

index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "rb") as f:
    metadatas = pickle.load(f)

# Load embedder
embedder = SentenceTransformer(EMBED_MODEL)

# FastAPI setup
app = FastAPI(title="Retriever Agent – FAISS")

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5

class Chunk(BaseModel):
    text: str
    source: str
    offset: int
    score: float

class RetrieveResponse(BaseModel):
    query: str
    results: list[Chunk]

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    # 1) Embed the query
    q_emb = embedder.encode([req.query], convert_to_numpy=True)
    # 2) Search FAISS
    distances, indices = index.search(q_emb, req.top_k)
    distances = distances[0]
    indices = indices[0]

    results = []
    for idx, dist in zip(indices, distances):
        if idx < 0 or idx >= len(metadatas):
            continue
        meta = metadatas[idx]
        # You need to re-load the chunk texts if you didn’t store them:
        # For simplicity here, assume metadatas also contains 'text'.
        text = meta.get("text", None)
        if text is None:
            raise HTTPException(500, "Metadata missing text field")
        results.append(Chunk(
            text=text,
            source=meta["source"],
            offset=meta["offset"],
            score=float(dist),
        ))

    return RetrieveResponse(query=req.query, results=results)
