"""Provider sem custo: embeddings por hash de palavras e resposta extrativa.

Serve para desenvolver e demonstrar o fluxo inteiro sem conta AWS.
"""
import hashlib
import re

import numpy as np

from .base import Generation, Passage

DIM = 512
_WORD = re.compile(r"\w{3,}", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


class LocalProvider:
    name = "local"

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in _tokens(t):
                h = int.from_bytes(hashlib.md5(w.encode()).digest()[:4], "little")
                out[i, h % DIM] += 1.0
            n = np.linalg.norm(out[i])
            if n:
                out[i] /= n
        return out

    def generate(self, question: str, passages: list[Passage]) -> Generation:
        if not passages:
            return Generation("Não encontrei a informação nos documentos.", 0, 0)
        q = set(_tokens(question))
        best: list[tuple[int, str]] = []
        for p in passages:
            for s in re.split(r"(?<=[.!?])\s+", p.text):
                score = len(q & set(_tokens(s)))
                if score and len(s) > 20:
                    best.append((score * 10 - p.n, f"{s.strip()} [{p.n}]"))
        best.sort(reverse=True)
        picked = [s for _, s in best[:3]] or [f"{passages[0].text[:240].strip()} [{passages[0].n}]"]
        text = "Com base nas fontes recuperadas: " + " ".join(picked)
        return Generation(text, len(question.split()), len(text.split()))
