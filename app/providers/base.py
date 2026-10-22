from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass
class Generation:
    text: str
    input_tokens: int
    output_tokens: int


@dataclass
class Passage:
    n: int  # número da citação [n]
    doc: str
    page: int
    text: str


class Provider(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray: ...

    def generate(self, question: str, passages: list[Passage]) -> Generation: ...


SYSTEM_PROMPT = (
    "Você responde perguntas usando SOMENTE os trechos numerados fornecidos. "
    "Cite a fonte de cada afirmação com [n]. Se os trechos não bastarem, diga que "
    "não encontrou a informação nos documentos. Responda no idioma da pergunta."
)


def build_user_prompt(question: str, passages: list[Passage]) -> str:
    ctx = "\n\n".join(f"[{p.n}] ({p.doc}, p. {p.page})\n{p.text}" for p in passages)
    return f"Trechos:\n{ctx}\n\nPergunta: {question}"
