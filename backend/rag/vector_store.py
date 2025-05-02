from config import settings
import faiss
import os
import pickle
import numpy as np
from typing import List

VECTOR_DB_PATH = settings["rag"]["vector_store_path"] + "/index.faiss"
META_PATH = settings["rag"]["vector_store_path"] + "/meta.pkl"

class VectorStore:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatL2(dim)
        self.text_chunks = []

    def add(self, embeddings: list[list[float]], chunks: list[str]):
        self.index.add(np.array(embeddings).astype("float32"))
        self.text_chunks.extend(chunks)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[str]:
        D, I = self.index.search(np.array([query_embedding]).astype("float32"), top_k)
        return [self.text_chunks[i] for i in I[0] if i < len(self.text_chunks)]

    def add_embeddings(self, embeddings: np.ndarray, texts: List[str]):
        self.index.add(embeddings)
        self.text_chunks.extend(texts)

    def save(self):
        os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
        faiss.write_index(self.index, VECTOR_DB_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(self.text_chunks, f)

    def load(self):
        if os.path.exists(VECTOR_DB_PATH) and os.path.exists(META_PATH):
            self.index = faiss.read_index(VECTOR_DB_PATH)
            with open(META_PATH, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    self.text_chunks = data.get("text_chunks", [])
                else:
                    self.text_chunks = data  # for backward compatibility


    def search(self, query_emb: np.ndarray, top_k: int = 5) -> List[str]:
        _, indices = self.index.search(query_emb, top_k)
        return [self.text_chunks[i] for i in indices[0] if i != -1 and i < len(self.text_chunks)]

    


