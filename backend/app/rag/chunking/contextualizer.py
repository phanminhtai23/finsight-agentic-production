"""Contextual retrieval (Anthropic): prepend an LLM-written context line to each chunk.

Embedding the contextualized form markedly improves recall on dense, repetitive corpora
such as financial statements (e.g. disambiguating which company / period a figure belongs to).
"""

import asyncio

from app.rag.chunking.models import ChunkData
from app.rag.ports import TextGenerator

_PROMPT = """You are indexing a document titled "{title}".
Section: {section}

Write ONE short sentence (max 25 words) that situates the chunk below within the document,
so it can be retrieved on its own. State the company and period if identifiable.
Return ONLY the sentence, no preamble.

<chunk>
{chunk}
</chunk>"""


class Contextualizer:
    def __init__(self, generator: TextGenerator, *, doc_title: str, concurrency: int = 5) -> None:
        self._gen = generator
        self._title = doc_title
        self._sem = asyncio.Semaphore(concurrency)

    async def _one(self, chunk: ChunkData) -> None:
        prompt = _PROMPT.format(
            title=self._title,
            section=chunk.section_title or "—",
            chunk=chunk.content,
        )
        async with self._sem:
            try:
                context = (await self._gen.generate(prompt)).strip()
            except Exception:
                context = ""
        if context:
            chunk.contextualized_content = f"{context}\n\n{chunk.content}"

    async def contextualize(self, chunks: list[ChunkData]) -> list[ChunkData]:
        """Add a context line to every chunk that will be embedded (in place)."""
        await asyncio.gather(*(self._one(c) for c in chunks if c.embed))
        return chunks
