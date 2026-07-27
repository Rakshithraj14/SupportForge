import io

from pypdf import PdfReader


def load_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_markdown(content: bytes) -> str:
    return content.decode("utf-8")


def load_document(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        return load_pdf(content)
    if filename.lower().endswith((".md", ".markdown", ".txt")):
        return load_markdown(content)
    raise ValueError(f"Unsupported file type: {filename}")
