import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import docx2txt


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path: str) -> str:
    return docx2txt.process(file_path)


def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        raise ValueError(f"Failed to extract text from URL: {url} — {e}")


def extract_text(source: str) -> str:
    source_lower = source.lower()

    if source_lower.startswith("http://") or source_lower.startswith("https://"):
        return extract_text_from_url(source)
    elif source_lower.endswith(".pdf"):
        return extract_text_from_pdf(source)
    elif source_lower.endswith(".docx"):
        return extract_text_from_docx(source)
    elif source_lower.endswith(".txt"):
        with open(source, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format or input source: {source}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Splits text into overlapping chunks for embedding.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
