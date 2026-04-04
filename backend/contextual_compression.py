import asyncio
import concurrent.futures
from dataclasses import dataclass
from typing import List, Optional, Tuple

import httpx
from langchain_core.documents import Document


# ─────────────────────────────────────────────
#  Result dataclass
# ─────────────────────────────────────────────

@dataclass
class CompressedChunk:
    """
    A chunk after compression.

    Attributes
    ----------
    content         : the compressed text (only relevant sentences)
    source          : original source filename / metadata
    original_length : character count before compression
    compressed_length: character count after compression
    compression_ratio: 0.0–1.0, lower = more aggressively compressed
    retrieval_score : the FAISS / RRF score from the upstream retriever
    was_compressed  : False if the compressor returned the original unchanged
    """
    content: str
    source: str
    original_length: int
    compressed_length: int
    compression_ratio: float
    retrieval_score: float
    was_compressed: bool


# ─────────────────────────────────────────────
#  Compression prompt
# ─────────────────────────────────────────────

COMPRESSION_PROMPT = """\
You are a precise information extraction assistant.

Given a DOCUMENT CHUNK and a QUESTION, extract ONLY the sentences or phrases \
from the chunk that are directly relevant to answering the question.

Rules:
- Copy relevant text verbatim — do NOT paraphrase or summarise.
- Include only what is needed to answer the question.
- If the chunk contains NO relevant information, respond with exactly: NO_RELEVANT_CONTENT
- Do NOT add any explanation, preamble, or commentary.
- Do NOT include sentences that are only tangentially related.

QUESTION: {query}

DOCUMENT CHUNK:
{chunk}

Relevant extracted text:"""


# ─────────────────────────────────────────────
#  Single-chunk compression via Ollama
# ─────────────────────────────────────────────

async def _compress_chunk_async(
    query: str,
    doc: Document,
    score: float,
    ollama_url: str,
    model: str,
    timeout: int,
    max_chunk_chars: int,
) -> Optional[CompressedChunk]:
    """
    Compress a single chunk by asking Ollama to extract only
    the sentences relevant to `query`.

    Returns None if the chunk is completely irrelevant.
    """
    original_text = doc.page_content
    source = doc.metadata.get("source", "unknown")

    # Truncate very long chunks to avoid overwhelming the compressor
    chunk_text = original_text[:max_chunk_chars]

    prompt = COMPRESSION_PROMPT.format(query=query, chunk=chunk_text)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,   # deterministic — we want faithful extraction
            "num_predict": 512,   # compressed output should be short
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            compressed_text = response.json().get("response", "").strip()

    except Exception as e:
        # On failure, pass the original chunk through unchanged
        print(f"[Compressor] Failed on chunk from '{source}': {e}", flush=True)
        return CompressedChunk(
            content=original_text,
            source=source,
            original_length=len(original_text),
            compressed_length=len(original_text),
            compression_ratio=1.0,
            retrieval_score=score,
            was_compressed=False,
        )

    # Filter out explicitly irrelevant chunks
    if "NO_RELEVANT_CONTENT" in compressed_text or len(compressed_text.strip()) < 10:
        return None

    ratio = len(compressed_text) / max(len(original_text), 1)

    return CompressedChunk(
        content=compressed_text,
        source=source,
        original_length=len(original_text),
        compressed_length=len(compressed_text),
        compression_ratio=ratio,
        retrieval_score=score,
        was_compressed=True,
    )


# ─────────────────────────────────────────────
#  ContextualCompressor
# ─────────────────────────────────────────────

class ContextualCompressor:
    """
    Compresses retrieved chunks to only their query-relevant content.

    Parameters
    ----------
    ollama_url      : Ollama base URL
    model           : model used for compression (use a fast small model)
    timeout         : seconds per compression call
    max_chunk_chars : truncate input chunks longer than this before compressing
    max_concurrency : max parallel compression calls (throttle for CPU/RAM)
    min_ratio       : drop chunks compressed to less than this ratio of original
                      (prevents the compressor from over-compressing into nonsense)
    """

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
        timeout: int = 60,
        max_chunk_chars: int = 4000,
        max_concurrency: int = 4,
        min_ratio: float = 0.02,
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        self.max_chunk_chars = max_chunk_chars
        self.max_concurrency = max_concurrency
        self.min_ratio = min_ratio

    async def compress(
        self,
        query: str,
        retrieved_docs: List[Tuple[Document, float]],
    ) -> List[CompressedChunk]:
        """
        Compress all retrieved chunks in parallel, then filter irrelevant ones.

        Parameters
        ----------
        query          : the original user question
        retrieved_docs : List[Tuple[Document, score]] from FAISS / HybridRetriever

        Returns
        -------
        List[CompressedChunk] sorted by retrieval_score descending.
        Chunks with NO_RELEVANT_CONTENT are excluded.
        """
        if not retrieved_docs:
            return []

        # Semaphore throttles concurrency to avoid OOM on large retrieval sets
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def compress_with_limit(doc: Document, score: float):
            async with semaphore:
                return await _compress_chunk_async(
                    query=query,
                    doc=doc,
                    score=score,
                    ollama_url=self.ollama_url,
                    model=self.model,
                    timeout=self.timeout,
                    max_chunk_chars=self.max_chunk_chars,
                )

        tasks = [compress_with_limit(doc, score) for doc, score in retrieved_docs]
        results = await asyncio.gather(*tasks)

        # Filter None (irrelevant) and over-compressed chunks
        compressed = [
            r for r in results
            if r is not None and r.compression_ratio >= self.min_ratio
        ]

        # Sort by original retrieval score so the best chunks stay on top
        compressed.sort(key=lambda c: c.retrieval_score, reverse=True)

        # Log compression stats
        if compressed:
            total_before = sum(c.original_length for c in compressed)
            total_after = sum(c.compressed_length for c in compressed)
            dropped = len(retrieved_docs) - len(compressed)
            print(
                f"[Compressor] {len(retrieved_docs)} chunks → "
                f"{len(compressed)} relevant "
                f"({dropped} dropped as irrelevant) · "
                f"context: {total_before:,} → {total_after:,} chars "
                f"({100 * total_after // max(total_before, 1)}% of original)",
                flush=True
            )

        return compressed

    def compress_sync(
        self,
        query: str,
        retrieved_docs: List[Tuple[Document, float]],
    ) -> List[CompressedChunk]:
        """
        Synchronous wrapper — use this from your existing sync FastAPI endpoints.
        Switch to `await compress()` if you convert /ask to async def.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.compress(query, retrieved_docs),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.compress(query, retrieved_docs)
                )
        except RuntimeError:
            return asyncio.run(self.compress(query, retrieved_docs))

    def build_context_string(
        self,
        compressed_chunks: List[CompressedChunk],
        max_total_chars: int = 8000,
    ) -> str:
        """
        Build the context string to inject into your prompt.

        Replaces the manual chunk concatenation you currently do in /ask.
        Respects a total character budget so you never blow the LLM context window.

        Parameters
        ----------
        compressed_chunks : output of compress() or compress_sync()
        max_total_chars   : hard cap on total context length

        Returns
        -------
        A formatted string ready to embed in your prompt template.
        """
        parts = []
        total = 0

        for chunk in compressed_chunks:
            header = f"[Source: {chunk.source}]"
            block = f"{header}\n{chunk.content}\n"

            if total + len(block) > max_total_chars:
                # Truncate the last chunk to fit within budget
                remaining = max_total_chars - total
                if remaining > len(header) + 50:
                    block = block[:remaining] + "..."
                    parts.append(block)
                break

            parts.append(block)
            total += len(block)

        return "\n---\n".join(parts)
