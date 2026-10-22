"""Índice vetorial em memória (NumPy), persistido em disco."""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


class VectorStore:
    def __init__(self, directory: Path):
        self.dir = directory
        self.dir.mkdir(parents=True, exist_ok=True)
        self._meta = self.dir / "index.json"
        self._vecs = self.dir / "vectors.npy"
        self._lock = threading.Lock()
        self.items: list[dict] = []
        self.vectors = np.zeros((0, 0), dtype=np.float32)
        self._load()

    def _load(self) -> None:
        if self._meta.exists() and self._vecs.exists():
            self.items = json.loads(self._meta.read_text(encoding="utf-8"))
            self.vectors = np.load(self._vecs)

    def _save(self) -> None:
        self._meta.write_text(json.dumps(self.items, ensure_ascii=False), encoding="utf-8")
        np.save(self._vecs, self.vectors)

    def add(self, doc: str, chunks: list[tuple[int, str]], vectors: np.ndarray) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.remove(doc, save=False)
            self.items += [{"doc": doc, "page": p, "text": t, "added": now} for p, t in chunks]
            self.vectors = vectors if not len(self.vectors) else np.vstack([self.vectors, vectors])
            self._save()

    def remove(self, doc: str, save: bool = True) -> bool:
        keep = [i for i, it in enumerate(self.items) if it["doc"] != doc]
        if len(keep) == len(self.items):
            return False
        self.items = [self.items[i] for i in keep]
        self.vectors = self.vectors[keep] if keep else np.zeros((0, 0), dtype=np.float32)
        if save:
            self._save()
        return True

    def search(self, qvec: np.ndarray, k: int) -> list[tuple[float, dict]]:
        if not len(self.items):
            return []
        scores = self.vectors @ qvec  # vetores já normalizados → cosseno
        top = np.argsort(-scores)[:k]
        return [(float(scores[i]), self.items[i]) for i in top if scores[i] > 0]

    def documents(self) -> list[dict]:
        docs: dict[str, dict] = {}
        for it in self.items:
            d = docs.setdefault(it["doc"], {"name": it["doc"], "chunks": 0, "pages": 0, "added": it["added"]})
            d["chunks"] += 1
            d["pages"] = max(d["pages"], it["page"])
        return list(docs.values())
