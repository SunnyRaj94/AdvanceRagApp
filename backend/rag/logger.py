# backend/rag/logger.py

import os
import json
import logging
from config import settings
from datetime import datetime

try:
    from backend.db.mongo import get_logs_collection
    logs_collection = get_logs_collection()
except Exception:
    logs_collection = None


# Fallback to log file
LOG_FILE_PATH = settings["app"].get("log_file_path", "./logs/rag_queries.log")
MAX_LOG_FILE_SIZE_MB = settings["app"].get("max_log_size_mb", 2)



def log_query(query: str, context: str, response: str) -> None:
    """
    Log the query, context, and response to MongoDB or fallback to file.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "context": context,
        "response": response
    }

    if logs_collection is not None:
        try:
            logs_collection.insert_one(log_entry)
            return
        except Exception as e:
            print(f"[Logger] Failed to log to MongoDB: {e}")

    _log_to_file(log_entry)


def _log_to_file(entry: dict) -> None:
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # Check if file size exceeds 2MB
    if os.path.exists(LOG_FILE_PATH):
        size_mb = os.path.getsize(LOG_FILE_PATH) / (1024 * 1024)
        if size_mb > MAX_LOG_FILE_SIZE_MB:
            os.rename(LOG_FILE_PATH, LOG_FILE_PATH.replace(".json", f"_{int(datetime.utcnow().timestamp())}.bak"))

    # Append entry
    with open(LOG_FILE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
