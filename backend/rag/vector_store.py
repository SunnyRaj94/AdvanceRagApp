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
        self.embeddings = []  # New: store embeddings per chunk

    def add_embeddings(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        source_type="file",
        file_id=None,
        link_id=None,
    ):
        self.index.add(embeddings)
        for i, text in enumerate(texts):
            emb = embeddings[i]
            self.embeddings.append(emb)
            self.text_chunks.append(
                {
                    "text": text,
                    "source_type": source_type,
                    "file_id": file_id,
                    "link_id": link_id,
                }
            )

    def save(self):
        os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
        faiss.write_index(self.index, VECTOR_DB_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(
                {"text_chunks": self.text_chunks, "embeddings": self.embeddings}, f
            )

    def load(self):
        if os.path.exists(VECTOR_DB_PATH) and os.path.exists(META_PATH):
            self.index = faiss.read_index(VECTOR_DB_PATH)
            with open(META_PATH, "rb") as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    self.text_chunks = data.get("text_chunks", [])
                    self.embeddings = data.get("embeddings", [])
                elif isinstance(data, list):  # backward compatibility
                    # self.text_chunks = data
                    self.text_chunks = [
                        {
                            "text": txt,
                            "source_type": "file",
                            "file_id": None,
                            "link_id": None,
                        }
                        for txt in data
                    ]

                    self.embeddings = []

    def search(
        self,
        query_emb: np.ndarray,
        top_k: int = 5,
        filter_by: str = None,
        context_id: str = None,
    ) -> List[str]:
        if filter_by or context_id:
            filtered = [
                (i, chunk)
                for i, chunk in enumerate(self.text_chunks)
                if (not filter_by or chunk.get("source_type") == filter_by)
                and (
                    not context_id
                    or chunk.get("file_id") == context_id
                    or chunk.get("link_id") == context_id
                )
            ]
            if not filtered:
                return []

            filtered_embeddings = np.array([self.embeddings[i] for i, _ in filtered])
            texts = [chunk["text"] for _, chunk in filtered]

            query_vector = query_emb[0]  # shape (dim,)
            query_norm = np.linalg.norm(query_vector)
            emb_norms = np.linalg.norm(filtered_embeddings, axis=1)
            similarities = np.dot(filtered_embeddings, query_vector.T) / (
                emb_norms * query_norm + 1e-8
            )

            top_indices = similarities.argsort()[-top_k:][::-1]
            return [texts[i] for i in top_indices]
        else:
            _, indices = self.index.search(query_emb, top_k)
            return [
                self.text_chunks[i]["text"]
                for i in indices[0]
                if i != -1 and i < len(self.text_chunks)
            ]

    def delete(self, source_type: str, context_id: str):
        new_chunks = []
        new_embeddings = []
        for i, chunk in enumerate(self.text_chunks):
            if chunk.get("source_type") == source_type and (
                chunk.get("file_id") == context_id or chunk.get("link_id") == context_id
            ):
                continue
            new_chunks.append(chunk)
            new_embeddings.append(self.embeddings[i])

        self.text_chunks = new_chunks
        self.embeddings = new_embeddings
        self.index = faiss.IndexFlatL2(self.index.d)  # reset index
        if new_embeddings:
            self.index.add(np.array(new_embeddings))
        self.save()
