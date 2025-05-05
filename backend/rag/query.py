import os
import logging
import datetime
import numpy as np
from backend.rag.vector_store import VectorStore
from backend.rag.embedder import get_embeddings
from backend.llm_engine import get_response_from_llm
from backend.rag.logger import log_query
from pymongo import MongoClient
from config import settings


# Initialize MongoDB client (if available)
client = None
logs_collection = None
if settings.get("app", {}).get("mongo_uri"):
    try:
        client = MongoClient(settings["app"]["mongo_uri"])
        db = client[settings["app"]["database_name"]]
        logs_collection = db["logs"]
    except Exception as e:
        print(f"Warning: MongoDB not available. Using local log file instead: {str(e)}")

# Fallback to log file
log_file_path = settings["app"].get("log_file_path", "./logs/rag_queries.log")
max_log_size_mb = settings["app"].get("max_log_size_mb", 2)

# Setup file logging if MongoDB is not available
if logs_collection is None:
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))

    # Configure file logging
    logging.basicConfig(
        filename=log_file_path, level=logging.INFO, format="%(asctime)s - %(message)s"
    )


def log_interaction(query: str, context: list[str], response: str):
    """
    Log the interaction into MongoDB or a log file based on the configuration.
    """
    log_entry = {
        "query": query,
        "context": context,
        "response": response,
        "timestamp": datetime.datetime.now(),
    }

    if logs_collection:
        # Log to MongoDB
        logs_collection.insert_one(log_entry)
    else:
        # Log to file with size constraint
        file_size = os.path.getsize(log_file_path) / (1024 * 1024)  # size in MB
        if file_size >= max_log_size_mb:
            # Rotate the log file (move to backup)
            os.rename(log_file_path, f"{log_file_path}.backup")
            with open(log_file_path, "w"):
                pass  # Create a new empty log file

        # Log to the file
        logging.info(f"Query: {query}\nContext: {context}\nResponse: {response}")


def query_rag_system(query: str, top_k: int = 5, source: str = "all") -> str:
    # Step 1: Get query embedding
    query_embedding = get_embeddings([query])[0]

    # Step 1.5: Infer dim from query_eokmbedding
    dim = len(query_embedding)

    # Step 2: Load vector store
    vectorstore = VectorStore(dim)
    vectorstore.load()

    relevant_chunks = vectorstore.search(
        np.array([query_embedding]), top_k=top_k, filter_by=source
    )

    # Step 4: Build context
    context = "\n".join(relevant_chunks)
    full_prompt = f"Context:\n{context}\n\nQuestion: {query}"

    # Step 5: Get response
    response = get_response_from_llm(full_prompt)

    # Step 6: Log
    log_query(query, context, response)

    return response
