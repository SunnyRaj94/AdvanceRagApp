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

    def add(self, embeddings: list[list[float]], chunks: list[str], source_type="file"):
        self.index.add(np.array(embeddings).astype("float32"))
        self.text_chunks.extend(
            [{"text": chunk, "source_type": source_type} for chunk in chunks]
        )

    def add_embeddings(
        self, embeddings: np.ndarray, texts: List[str], source_type="file"
    ):
        self.index.add(embeddings)
        self.text_chunks.extend(
            [{"text": text, "source_type": source_type} for text in texts]
        )

    def save(self):
        os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
        faiss.write_index(self.index, VECTOR_DB_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump({"text_chunks": self.text_chunks}, f)

    def load(self):
        if os.path.exists(VECTOR_DB_PATH) and os.path.exists(META_PATH):
            self.index = faiss.read_index(VECTOR_DB_PATH)
            with open(META_PATH, "rb") as f:
                data = pickle.load(f)
                self.text_chunks = data.get("text_chunks", [])

    def search(
        self, query_emb: np.ndarray, top_k: int = 5, filter_by: str = None
    ) -> List[str]:
        if filter_by:
            # Filter the chunks and build a new temporary index
            filtered = [
                (i, d)
                for i, d in enumerate(self.text_chunks)
                if d.get("source_type") == filter_by
            ]
            if not filtered:
                return []
            indices, texts = zip(*filtered)
            tmp_index = faiss.IndexFlatL2(self.index.d)
            tmp_index.add(
                self.index.reconstruct_n(np.array(indices, dtype="int64"), len(indices))
            )
            _, top_idx = tmp_index.search(query_emb, top_k)
            return [texts[i]["text"] for i in top_idx[0] if i < len(texts)]
        else:
            _, indices = self.index.search(query_emb, top_k)
            return [
                self.text_chunks[i]["text"]
                for i in indices[0]
                if i != -1 and i < len(self.text_chunks)
            ]
