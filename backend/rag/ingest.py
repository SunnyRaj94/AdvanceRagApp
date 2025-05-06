from backend.rag.processor import extract_text, chunk_text
from backend.rag.embedder import get_embeddings
from backend.rag.vector_store import VectorStore
from backend.rag.logger import MetadataStore
import uuid
from config import settings
import numpy as np


META_DATA_JSON_FILE = settings["app"].get("meta_data_file_path", "./logs/metadata.json")
MAX_LOG_FILE_SIZE_MB = settings["app"].get("max_log_size_mb", 2)
# Track metadata
file_metadata_store = MetadataStore(META_DATA_JSON_FILE, MAX_LOG_FILE_SIZE_MB)


def ingest_data(
    source_path_or_url: str, source_type: str = "file", user: str = "anonymous"
) -> str:
    print(f"📥 Ingesting source: {source_path_or_url} (type: {source_type})")
    item_id = str(uuid.uuid4())

    # Step 1: Extract
    raw_text = extract_text(source_path_or_url)
    print(f"Preview:\n{raw_text[:1000]}")  # Add this line
    print(f"✅ Extracted {len(raw_text)} characters")

    # Step 2: Chunk
    chunks = chunk_text(raw_text)
    print(f"✅ Chunked into {len(chunks)} pieces")

    # Step 3: Embed
    embeddings = get_embeddings(chunks)
    # Convert to NumPy array to access .shape
    embeddings = np.array(embeddings).astype("float32")
    print(f"✅ Created embeddings of shape {embeddings.shape}")

    # Step 4: Store
    dim = embeddings.shape[1]
    store = VectorStore(dim)
    store.load()
    # store.add_embeddings(embeddings, chunks)
    store.add_embeddings(
        embeddings,
        chunks,
        source_type=source_type,
        file_id=item_id if source_type == "file" else None,
        link_id=item_id if source_type == "url" else None,
    )

    store.save()
    print(f"✅ Stored {len(chunks)} chunks in vector store")

    # Step 5: Save metadata
    metadata = {
        "source": source_path_or_url,
        "type": source_type,
        "user": user,
        "chunks": len(chunks),
    }
    file_metadata_store.add(item_id, metadata)
    return item_id
