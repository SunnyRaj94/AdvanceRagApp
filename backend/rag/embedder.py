from sentence_transformers import SentenceTransformer
from config import settings
import openai
import os

model = None


def get_model():
    global model
    if model is not None:
        return model

    embedder_type = settings["embedding"]["type"]
    model_name = settings["embedding"]["model_name"]

    if embedder_type in ["huggingface", "local"]:
        if not os.path.exists(model_name):
            raise FileNotFoundError(f"Local model path does not exist: {model_name}")
        model = SentenceTransformer(model_name)
    elif embedder_type == "openai":
        openai.api_key = settings["embedding"]["api_key"]
    else:
        raise ValueError(f"Unknown embedding type: {embedder_type}")

    return model


def get_embeddings(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embedder_type = settings["embedding"]["type"]

    if embedder_type in ["huggingface", "local"]:
        return model.encode(texts, convert_to_numpy=True).tolist()
    elif embedder_type == "openai":
        return [
            openai.Embedding.create(input=t, model=settings["embedding"]["model_name"])[
                "data"
            ][0]["embedding"]
            for t in texts
        ]
