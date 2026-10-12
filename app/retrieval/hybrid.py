"""FAISS index plus SQLite FTS, with canon and timeline filters."""

from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.canon import canon_rank
from app.core.text import tokens
from app.db.models import Segment
from app.retrieval.embeddings import Embedder


@dataclass
class Hit:
    segment_id: str
    text: str
    score: float
    canon_level: str
    timeline: str
    source_id: str
    lexical: float = 0.0
    semantic: float = 0.0


class VectorIndex:
    def __init__(self, dim: int, path: Path):
        self.dim = dim
        self.path = path
        self.ids: list[str] = []
        self.known: set[str] = set()
        self.index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        if path.exists():
            self._load()

    def _load(self) -> None:
        self.index = faiss.read_index(str(self.path))
        sidecar = self.path.with_suffix(".ids")
        if sidecar.exists():
            self.ids = [line.strip() for line in sidecar.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.known = set(self.ids)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.path))
        self.path.with_suffix(".ids").write_text("\n".join(self.ids), encoding="utf-8")

    def add(self, ids: list[str], vectors: np.ndarray) -> None:
        keep = [index for index, item in enumerate(ids) if item not in self.known]
        if not keep:
            return
        vectors = vectors[keep]
        ids = [ids[index] for index in keep]
        faiss.normalize_L2(vectors)
        numeric = np.arange(len(self.ids), len(self.ids) + len(ids), dtype="int64")
        self.index.add_with_ids(np.ascontiguousarray(vectors), numeric)
        self.ids.extend(ids)
        self.known.update(ids)
        self.save()

    def search(self, vector: np.ndarray, k: int) -> list[tuple[str, float]]:
        if not self.ids or k <= 0:
            return []
        query = vector.reshape(1, -1).astype("float32")
        faiss.normalize_L2(query)
        scores, indexes = self.index.search(query, min(k, len(self.ids)))
        found = []
        for score, index in zip(scores[0], indexes[0]):
            if index < 0 or index >= len(self.ids):
                continue
            found.append((self.ids[int(index)], float(score)))
        return found


def _fts_query(query: str) -> str:
    parts = []
    for token in tokens(query):
        safe = token.replace('"', "")
        if safe:
            parts.append(f'"{safe}"')
    return " OR ".join(parts)


def lexical_search(session: Session, query: str, limit: int = 20) -> list[tuple[str, float]]:
    match = _fts_query(query)
    if not match:
        return []
    try:
        rows = session.execute(
            text(
                """
                SELECT segment_id, bm25(segment_fts) AS rank
                FROM segment_fts
                WHERE segment_fts MATCH :match
                ORDER BY rank
                LIMIT :limit
                """
            ),
            {"match": match, "limit": limit},
        ).all()
    except Exception:
        return []
    hits = []
    for segment_id, rank in rows:
        # bm25 in FTS5 is negative; closer to zero is better.
        hits.append((segment_id, 1.0 / (1.0 + abs(float(rank)))))
    return hits


def overlap_rerank(query: str, hits: list[Hit]) -> list[Hit]:
    query_tokens = set(tokens(query))
    if not query_tokens:
        return hits
    for hit in hits:
        overlap = len(query_tokens & set(tokens(hit.text))) / len(query_tokens)
        hit.score = 0.75 * hit.score + 0.25 * overlap
    hits.sort(key=lambda item: item.score, reverse=True)
    return hits


def hybrid_search(
    session: Session,
    embedder: Embedder,
    index: VectorIndex,
    query: str,
    *,
    limit: int = 6,
    timeline: str | None = "main",
    min_canon_rank: int = 0,
    exclude_alternate: bool = True,
    rerank: bool = True,
) -> list[Hit]:
    lexical = dict(lexical_search(session, query, 30))
    semantic = dict(index.search(embedder.embed([query], is_query=True)[0], 30))
    ids = set(lexical) | set(semantic)
    if not ids:
        return []
    rows = session.query(Segment).filter(Segment.id.in_(ids)).all()
    hits: list[Hit] = []
    for row in rows:
        if timeline and row.timeline != timeline:
            continue
        if exclude_alternate and row.timeline == "alternate":
            continue
        if canon_rank(row.canon_level) < min_canon_rank:
            continue
        lex = lexical.get(row.id, 0.0)
        sem = max(0.0, semantic.get(row.id, 0.0))
        canon_bonus = canon_rank(row.canon_level) / 100
        score = 0.4 * lex + 0.45 * sem + 0.15 * canon_bonus
        hits.append(
            Hit(
                segment_id=row.id,
                text=row.text,
                score=score,
                canon_level=row.canon_level,
                timeline=row.timeline,
                source_id=row.source_id,
                lexical=lex,
                semantic=sem,
            )
        )
    hits.sort(key=lambda item: item.score, reverse=True)
    if rerank:
        hits = overlap_rerank(query, hits)
    return hits[:limit]
