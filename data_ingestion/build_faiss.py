# data_ingestion/build_faiss.py

import os
import glob
import pickle

from sentence_transformers import SentenceTransformer
import faiss

def ingest_and_index(
    docs_folder: str,
    index_path: str,
    model_name: str = "all-MiniLM-L6-v2",
    chunk_size: int = 1000
):
    """
    1. Read all .txt files under docs_folder
    2. Chunk each into chunk_size‐character pieces
    3. Embed with SentenceTransformer
    4. Build a FAISS index and save it + metadata
    """
    # 1) Load embedder
    model = SentenceTransformer(model_name)

    texts = []
    metadatas = []
    # 2) Read & chunk
    for txt_file in glob.glob(os.path.join(docs_folder, "*.txt")):
        with open(txt_file, encoding="utf-8") as f:
            full = f.read()
        for i in range(0, len(full), chunk_size):
            chunk = full[i : i + chunk_size]
            texts.append(chunk)
            metadatas.append({
                "source": os.path.basename(txt_file),
                "offset": i,
                "text": chunk
            })

    if not texts:
        raise ValueError(f"No .txt files found in {docs_folder}")

    # 3) Embed
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    # 4) Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 5) Persist index + metadata
    faiss.write_index(index, index_path)
    with open(f"{index_path}.meta", "wb") as f:
        pickle.dump(metadatas, f)

    print(f"Indexed {len(texts)} chunks. Index saved to {index_path}")

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--docs_folder", required=True, help="Path to folder with .txt docs")
    p.add_argument("--index_path", required=True, help="Where to write the FAISS index file")
    args = p.parse_args()
    ingest_and_index(args.docs_folder, args.index_path)
