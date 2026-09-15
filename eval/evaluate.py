"""Оценка retrieval на golden-сете (Hit@k, MRR).

Запуск (после ingestion документов под тем же user-id):
    cd backend && uv run python ../eval/evaluate.py --user-id <uid> [--top-k 5] [--compare]

Метрики retrieval-side, без LLM-судьи: попадание ожидаемых ключевых
слов в топ-k и MRR по первому хиту. LLM-метрики RAGAS (faithfulness,
answer_relevancy) — следующий шаг: нужен ключ провайдера и эталонные
ответы в golden-сете.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).with_name("golden.jsonl")


def load_golden(path: Path = GOLDEN_PATH) -> list[dict]:
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def rank_of_first_hit(contents: list[str], keywords: list[str]) -> int | None:
    """Чистая функция: позиция первого чанка с ключевым словом (1-based)."""
    lowered = [c.lower() for c in contents]
    wants = [k.lower() for k in keywords]
    for i, content in enumerate(lowered, start=1):
        if any(w in content for w in wants):
            return i
    return None


def summarize(ranks: list[int | None]) -> dict:
    hits = [r for r in ranks if r is not None]
    n = len(ranks)
    mrr = sum(1.0 / r for r in hits) / n if n else 0.0
    return {
        "n": n,
        "hit_at_k": len(hits) / n if n else 0.0,
        "mrr": round(mrr, 3),
    }


async def evaluate(
    user_id: str, top_k: int = 5, use_reranker: bool = True
) -> dict:
    from app.adapters.embeddings.bge_m3 import BgeM3EmbeddingProvider
    from app.adapters.reranker.bge_reranker import BgeReranker
    from app.adapters.vector_store.qdrant_store import QdrantVectorStore
    from app.application.retrieve import RetrieveUseCase
    from app.core.config import settings

    usecase = RetrieveUseCase(
        vectors=QdrantVectorStore(
            url=settings.QDRANT_URL,
            collection=settings.COLLECTION_NAME,
        ),
        embeddings=BgeM3EmbeddingProvider(settings.EMBEDDING_MODEL),
        reranker=BgeReranker() if use_reranker else None,
    )
    ranks = []
    for item in load_golden():
        scored = await usecase.execute(item["question"], user_id, top_k=top_k)
        rank = rank_of_first_hit(
            [s.chunk.content for s in scored], item["keywords"]
        )
        ranks.append(rank)
        mark = f"rank={rank}" if rank else "MISS"
        print(f"[{mark}] {item['question']}")
    return summarize(ranks)


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG retrieval eval")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Сравнить с реранкингом и без (до/после)",
    )
    args = parser.parse_args()
    print("== with rerank ==")
    with_r = asyncio.run(
        evaluate(args.user_id, top_k=args.top_k, use_reranker=True)
    )
    print(with_r)
    if args.compare:
        print("== without rerank (dense+sparse RRF only) ==")
        without = asyncio.run(
            evaluate(args.user_id, top_k=args.top_k, use_reranker=False)
        )
        print(without)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
