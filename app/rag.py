import logging
import time

from .config import settings
from .providers.base import Passage, Provider
from .store import VectorStore

log = logging.getLogger("docintel")


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    return round(tokens_in / 1000 * settings.price_in_per_1k + tokens_out / 1000 * settings.price_out_per_1k, 6)


def answer(question: str, store: VectorStore, provider: Provider, top_k: int | None = None) -> dict:
    t0 = time.perf_counter()
    qvec = provider.embed([question])[0]
    hits = store.search(qvec, top_k or settings.top_k)
    t_retrieve = time.perf_counter()

    passages = [Passage(n=i, doc=h["doc"], page=h["page"], text=h["text"]) for i, (_, h) in enumerate(hits, 1)]
    gen = provider.generate(question, passages)
    t_end = time.perf_counter()

    metrics = {
        "provider": provider.name,
        "retrieval_ms": round((t_retrieve - t0) * 1000, 1),
        "generation_ms": round((t_end - t_retrieve) * 1000, 1),
        "total_ms": round((t_end - t0) * 1000, 1),
        "input_tokens": gen.input_tokens,
        "output_tokens": gen.output_tokens,
        "estimated_cost_usd": estimate_cost(gen.input_tokens, gen.output_tokens),
    }
    log.info("ask %s", metrics)
    return {
        "question": question,
        "answer": gen.text,
        "citations": [
            {"n": p.n, "doc": p.doc, "page": p.page, "score": round(s, 3), "text": p.text}
            for p, (s, _) in zip(passages, hits)
        ],
        "metrics": metrics,
    }
