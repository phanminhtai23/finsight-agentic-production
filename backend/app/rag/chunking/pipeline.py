"""Chunking pipeline — composes the advanced chunking techniques.

  1. structure-aware split + parent-child (small-to-big)   [StructureSplitter]
  2. optional contextual-retrieval enrichment              [Contextualizer]

Semantic chunking ([SemanticChunker]) is available as an alternative child splitter and can
be wired in where embeddings are cheap; it is kept optional to bound ingestion cost/latency.
"""

from dataclasses import dataclass

from app.rag.chunking.contextualizer import Contextualizer
from app.rag.chunking.models import ChunkData, ParsedDocument
from app.rag.chunking.splitter import StructureSplitter
from app.rag.ports import TextGenerator


@dataclass
class ChunkingConfig:
    parent_chars: int = 2400
    child_chars: int = 800
    overlap: int = 120
    contextualize: bool = True


class ChunkingPipeline:
    def __init__(
        self,
        config: ChunkingConfig | None = None,
        *,
        generator: TextGenerator | None = None,
    ) -> None:
        self.config = config or ChunkingConfig()
        self._generator = generator
        self._splitter = StructureSplitter(
            parent_chars=self.config.parent_chars,
            child_chars=self.config.child_chars,
            overlap=self.config.overlap,
        )

    async def run(self, doc: ParsedDocument) -> list[ChunkData]:
        chunks = self._splitter.split(doc)
        if self.config.contextualize and self._generator is not None:
            await Contextualizer(self._generator, doc_title=doc.title).contextualize(chunks)
        return chunks
