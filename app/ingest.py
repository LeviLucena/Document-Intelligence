import io
import re
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class Chunk:
    page: int
    text: str


def extract_pages(data: bytes) -> list[str]:
    reader = PdfReader(io.BytesIO(data))
    return [(page.extract_text() or "") for page in reader.pages]


def chunk_pages(pages: list[str], size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for number, raw in enumerate(pages, start=1):
        text = re.sub(r"\s+", " ", raw).strip()
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):  # evita cortar no meio de uma palavra
                cut = text.rfind(" ", start + size // 2, end)
                end = cut if cut != -1 else end
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(number, piece))
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
