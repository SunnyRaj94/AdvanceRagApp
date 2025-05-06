import os
import json
from config import settings
from datetime import datetime
from collections import OrderedDict
from typing import Dict

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
        "response": response,
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
            os.rename(
                LOG_FILE_PATH,
                LOG_FILE_PATH.replace(
                    ".json", f"_{int(datetime.utcnow().timestamp())}.bak"
                ),
            )

    # Append entry
    with open(LOG_FILE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


class MetadataStore:
    def __init__(self, filepath: str, max_size_mb: float = 2.0):
        self.filepath = filepath
        self.max_bytes = int(max_size_mb * 1024 * 1024)
        self._load()

    def _load(self):
        print("trying to make metadatastore")
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.store = OrderedDict(json.load(f))
                print("metadatastore made")
            except json.JSONDecodeError:
                print("error in making metadatastore")
                self.store = OrderedDict()
        else:
            self.store = OrderedDict()

    def _save(self):
        # Enforce max size by removing oldest entries
        while True:
            json_str = json.dumps(self.store, indent=2)
            if len(json_str.encode("utf-8")) <= self.max_bytes:
                break
            if self.store:
                self.store.popitem(last=False)  # Remove the oldest item
            else:
                break

        with open(self.filepath, "w") as f:
            json.dump(self.store, f, indent=2)

    def add(self, item_id: str, data: Dict):
        data["timestamp"] = datetime.utcnow().isoformat()
        self.store[item_id] = data
        self._save()

    def list(self) -> Dict:
        return dict(self.store)

    def delete(self, source_type: str, context_id: str):
        self.store = OrderedDict(
            (k, v) for k, v in self.store.items() if k != context_id
        )
        self._save()
