"""Benchmark FinSight on the sample dataset: RAG vs a no-RAG baseline.

Run inside the api container (has env + reaches the API):
    docker compose exec api python -m evals.run_eval

Metrics: expected-answer recall (RAG and baseline), citation coverage, and LLM-judge
groundedness. With LANGSMITH_TRACING=true, every call is also traced in LangSmith.
"""

import asyncio
import os

import httpx

from app.core.llm import get_text_generator
from evals.dataset import EVAL_SET
from evals.evaluators import expected_recall, groundedness, has_citations

API = os.getenv("EVAL_API", "http://localhost:8000")


async def _baseline(generator, question: str) -> str:
    return await generator.generate(f"Answer the question concisely:\n{question}")


async def main() -> None:
    generator = get_text_generator()
    rag_recall, base_recall, citation, ground = [], [], [], []

    async with httpx.AsyncClient(timeout=180) as client:
        print(f"{'Question':54} RAG  BASE CIT")
        print("-" * 70)
        for item in EVAL_SET:
            q, expected = item["question"], item["expected"]
            resp = await client.post(f"{API}/api/v1/ask", json={"question": q})
            data = resp.json()
            answer = data.get("answer", "")
            evidence = "\n".join(c.get("snippet", "") for c in data.get("citations", []))

            rr = expected_recall(answer, expected)
            br = expected_recall(await _baseline(generator, q), expected)
            cit = has_citations(answer)
            g = (
                await groundedness(generator, question=q, answer=answer, evidence=evidence)
                if evidence
                else 0.0
            )
            rag_recall.append(rr)
            base_recall.append(br)
            citation.append(1.0 if cit else 0.0)
            ground.append(g)
            print(f"{q[:52]:54} {rr:.2f} {br:.2f} {'Y' if cit else 'N'}")

    n = len(EVAL_SET)
    print("\n=== Averages ===")
    print(f"RAG expected-recall:       {sum(rag_recall) / n:.0%}")
    print(f"Baseline (no-RAG) recall:  {sum(base_recall) / n:.0%}")
    print(f"Citation coverage:         {sum(citation) / n:.0%}")
    print(f"Groundedness (LLM judge):  {sum(ground) / n:.2f}")
    print("\nFull traces in LangSmith when LANGSMITH_TRACING=true.")


if __name__ == "__main__":
    asyncio.run(main())
