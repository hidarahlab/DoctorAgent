from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from config import CANDIDATES, CHUNKS_PATH, EMBED_CACHE, EMBED_MODEL, INDEX_DIR, RRF_K, TOP_K

_STOP = set(
    "a an and are as at be by can do does for from has have how i in is it its of on or "
    "that the this to was what when where which who why will with you your about my me".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP]


def chunk_to_passage(c: dict) -> str:
    return f"{c['entry']} - {c['section']}: {c['text']}"


@dataclass
class Hit:
    chunk: dict
    score: float
    dense_sim: float


class HybridRetriever:
    def __init__(self, chunks: list[dict], aliases: dict[str, str], index: faiss.Index, embedder):
        self.chunks = chunks
        self.aliases = {k.lower(): v for k, v in aliases.items()}
        self.entries = {c["entry"].lower(): c["entry"] for c in chunks}
        self.index = index
        self.embedder = embedder
        self.bm25 = BM25Okapi([tokenize(chunk_to_passage(c)) for c in chunks])

    @staticmethod
    def _embedder():
        from fastembed import TextEmbedding
        return TextEmbedding(model_name=EMBED_MODEL, cache_dir=str(EMBED_CACHE))

    @classmethod
    def build(cls) -> "HybridRetriever":
        data = json.loads(CHUNKS_PATH.read_text())
        chunks, aliases = data["chunks"], data["aliases"]
        embedder = cls._embedder()
        vecs = np.array(list(embedder.passage_embed([chunk_to_passage(c) for c in chunks])), dtype="float32")
        faiss.normalize_L2(vecs)
        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs)
        INDEX_DIR.mkdir(exist_ok=True)
        faiss.write_index(index, str(INDEX_DIR / "chunks.faiss"))
        return cls(chunks, aliases, index, embedder)

    @classmethod
    def load(cls) -> "HybridRetriever":
        path = INDEX_DIR / "chunks.faiss"
        if not path.exists():
            return cls.build()
        data = json.loads(CHUNKS_PATH.read_text())
        return cls(data["chunks"], data["aliases"], faiss.read_index(str(path)), cls._embedder())

    def _expand(self, query: str) -> str:
        q = query.lower()
        extra = [target for alias, target in self.aliases.items() if re.search(rf"\b{re.escape(alias)}\b", q)]
        return query + (" " + " ".join(extra) if extra else "")

    def search(self, query: str, k: int = TOP_K, mode: str = "hybrid") -> list[Hit]:
        query = self._expand(query)

        qv = np.array(list(self.embedder.query_embed(query)), dtype="float32")
        faiss.normalize_L2(qv)
        sims, ids = self.index.search(qv, CANDIDATES)
        dense = {int(i): float(s) for i, s in zip(ids[0], sims[0]) if i >= 0}

        bm = self.bm25.get_scores(tokenize(query))
        sparse = [int(i) for i in np.argsort(bm)[::-1][:CANDIDATES] if bm[i] > 0]

        fused: dict[int, float] = {}
        if mode in ("hybrid", "dense"):
            for rank, i in enumerate(dense):
                fused[i] = fused.get(i, 0) + 1 / (RRF_K + rank + 1)
        if mode in ("hybrid", "sparse"):
            for rank, i in enumerate(sparse):
                fused[i] = fused.get(i, 0) + 1 / (RRF_K + rank + 1)

        ql = query.lower()
        for i in (fused if mode == "hybrid" else []):
            entry = self.chunks[i]["entry"].lower()
            if len(entry) > 3 and re.search(rf"\b{re.escape(entry)}\b", ql):
                fused[i] += 1 / RRF_K

        best = sorted(fused, key=fused.get, reverse=True)[:k]
        missing = [i for i in best if i not in dense]
        if missing:
            vecs = np.vstack([self.index.reconstruct(i) for i in missing])
            for i, s in zip(missing, (vecs @ qv[0]).tolist()):
                dense[i] = s
        return [Hit(self.chunks[i], fused[i], dense[i]) for i in best]


def main() -> None:
    r = HybridRetriever.build()
    print(f"indexed {r.index.ntotal} chunks -> {INDEX_DIR}", file=sys.stderr)
    for q in ["What causes acne?", "treatment for bronchitis", "abdominal hernia"]:
        hits = r.search(q, 3)
        print(q, "->", [(h.chunk["entry"], h.chunk["section"], round(h.dense_sim, 2)) for h in hits])


if __name__ == "__main__":
    main()
