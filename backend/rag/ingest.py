# backend/rag/ingest.py
from backend.rag.processor import extract_text, chunk_text
from backend.rag.embedder import get_embeddings
from backend.rag.vector_store import VectorStore
from config import settings
import numpy as np


def ingest_document(file_path: str):
    print(f"🧾 Ingesting document: {file_path}")

    # Step 1: Extract
    raw_text = extract_text(file_path)
    print(f"✅ Extracted {len(raw_text)} characters")

    # Step 2: Chunk
    chunks = chunk_text(raw_text)
    print(f"✅ Chunked into {len(chunks)} pieces")

    # Step 3: Embed
    embeddings = get_embeddings(chunks)
    print(f"✅ Created embeddings of shape {embeddings.shape}")

    # Step 4: Store
    dim = embeddings.shape[1]
    store = VectorStore(dim)
    store.load()  # Load existing index if present
    store.add_embeddings(embeddings, chunks)
    store.save()
    print(f"✅ Stored {len(chunks)} chunks in vector store")

    return True
