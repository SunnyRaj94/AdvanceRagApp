import os
from config import settings

model_type = settings["llm"]["model_type"]

# Load keys from config or environment
openai_api_key = settings["llm"].get("openai", {}).get("api_key", os.getenv("OPENAI_API_KEY"))
hf_api_key = settings["llm"].get("huggingface", {}).get("api_key", os.getenv("HUGGINGFACE_API_KEY"))

# Optional: cache model instance
llama_model = None

def get_response_from_llm(prompt: str, context: str = "") -> str:
    full_prompt = f"{context}\n\n{prompt}" if context else prompt

    if model_type == "llama-cpp":
        return run_llama_cpp(full_prompt)
    elif model_type == "openai":
        return run_openai(full_prompt)
    elif model_type == "huggingface":
        return run_huggingface(full_prompt)
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")


def run_llama_cpp(prompt: str) -> str:
    global llama_model
    from llama_cpp import Llama

    if llama_model is None:
        llama_model = Llama(
            model_path=settings["llm"]["model_path"],
            n_ctx=settings["llm"]["context_window"],
            n_threads=4,
            verbose=False,
        )
    max_tokens = settings["llm"].get("max_tokens", 512)


    response = llama_model(
        prompt,
        temperature=settings["llm"]["temperature"],
        max_tokens=max_tokens,  # adjust as needed
        stop=[],         # let it run freely
    )

    return response["choices"][0]["text"].strip() if "choices" in response else "No response"


def run_openai(prompt: str) -> str:
    import openai
    openai.api_key = openai_api_key
    model = settings["llm"]["openai"]["model"]

    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings["llm"]["temperature"]
    )
    return response.choices[0].message.content.strip()


def run_huggingface(prompt: str) -> str:
    import requests

    model = settings["llm"]["huggingface"]["model"]
    headers = {
        "Authorization": f"Bearer {hf_api_key}"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": settings["llm"]["temperature"]
        }
    }
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model}",
        headers=headers,
        json=payload
    )
    data = response.json()
    return data[0]["generated_text"].strip() if isinstance(data, list) else str(data)
