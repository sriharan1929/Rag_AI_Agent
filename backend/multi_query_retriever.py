import asyncio
import hashlib
import json
import re
from typing import List, Tuple, Optional

import httpx
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


# ─────────────────────────────────────────────
#  RRF (Reciprocal Rank Fusion)
# ─────────────────────────────────────────────
def _rrf_merge(
    ranked_lists: List[List[str]],
    doc_map: dict,
    k: int = 60,
    top_n: int = 15,
) -> List[Tuple[Document, float]]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    sorted_ids = sorted(scores, key=lambda d: scores[d], reverse=True)
    return [
        (doc_map[doc_id], scores[doc_id])
        for doc_id in sorted_ids[:top_n]
        if doc_id in doc_map
    ]


def _content_id(doc: Document) -> str:
    """Stable ID for a chunk based on its text content."""
    return hashlib.md5(doc.page_content.encode()).hexdigest()


# ─────────────────────────────────────────────
#  Query expansion via Ollama
# ─────────────────────────────────────────────

EXPANSION_PROMPT = """\
You are an expert at information retrieval. Your job is to generate {n} different \
search queries that would help find the answer to the following question.

Rules:
- Each query must approach the topic from a different angle or use different vocabulary.
- Queries should be specific and retrieval-focused — not conversational.
- Do NOT explain anything. Output ONLY a JSON array of strings.
- Do NOT include the original query in the list.

Original question: {query}

Output format (JSON array only, no markdown, no explanation):
["query one", "query two", "query three"]
"""


async def _expand_query_async(
    query: str,
    n: int,
    ollama_url: str,
    model: str,
    timeout: int,
) -> List[str]:
    """
    Ask Ollama to produce `n` rewritten query variants.
    """
    prompt = EXPANSION_PROMPT.format(n=n, query=query)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7},
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip()

        # Extract the JSON array
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if not match:
            print(f"[MultiQueryRetriever] Could not parse expansion: {raw[:200]}", flush=True)
            return [query]

        variants: List[str] = json.loads(match.group())
        variants = [v.strip() for v in variants if isinstance(v, str) and v.strip()]

        if not variants:
            return [query]

        print(f"  [EXPANSION] Expanded '{query[:60]}' → {len(variants)} variants:", flush=True)
        for v in variants:
            print(f"    - {v}", flush=True)
        return variants

    except Exception as e:
        print(f"[MultiQueryRetriever] Expansion failed ({e}), using original query only.", flush=True)
        return [query]


# ─────────────────────────────────────────────
#  Parallel FAISS search
# ─────────────────────────────────────────────

async def _faiss_search_async(
    faiss_db: FAISS,
    query: str,
    candidates: int,
) -> List[Tuple[Document, float]]:
    """
    Run a single FAISS similarity search in a thread pool.
    """
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: faiss_db.similarity_search_with_score(query, k=candidates),
    )
    return results


# ─────────────────────────────────────────────
#  MultiQueryRetriever
# ─────────────────────────────────────────────

class MultiQueryRetriever:
    def __init__(
        self,
        faiss_db: FAISS,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
        n_variants: int = 4,
        candidates: int = 10,
        timeout: int = 30,
    ):
        self.faiss_db = faiss_db
        self.ollama_url = ollama_url
        self.model = model
        self.n_variants = n_variants
        self.candidates = candidates
        self.timeout = timeout
        self.web_search_tool = None

    def _get_web_tool(self):
        if self.web_search_tool is None:
            from services.web_search.web_search import WebSearchTool
            self.web_search_tool = WebSearchTool()
        return self.web_search_tool

    async def search(
        self,
        query: str,
        k: int = 15,
        n_variants: Optional[int] = None,
        include_original: bool = True,
        rrf_k: int = 60,
        include_web: bool = False,
        include_images: bool = False,
    ) -> dict:
        # Step 1: Generate variants
        nv = n_variants if n_variants is not None else self.n_variants
        if nv > 0:
            variants = await _expand_query_async(
                query=query,
                n=nv,
                ollama_url=self.ollama_url,
                model=self.model,
                timeout=self.timeout,
            )
        else:
            variants = []

        all_queries = ([query] if include_original else []) + variants

        # Step 2: Parallel search
        tasks = [
            _faiss_search_async(self.faiss_db, q, self.candidates)
            for q in all_queries
        ]
        
        if include_web:
            print(f"  [Web] Adding DuckDuckGo search for: {query}", flush=True)
            web_task = self._get_web_tool().search_async(query)
            tasks.append(web_task)
            
            if include_images:
                print(f"  [Web] Adding DuckDuckGo image search for: {query}", flush=True)
                image_task = self._get_web_tool().search_images_async(query)
                tasks.append(image_task)

        print(f"  [RAG] Performing parallel search for {len(tasks)} tasks...", flush=True)
        # Explicitly cast to list to avoid lint issues and ensure mutability
        all_results = list(await asyncio.gather(*tasks))
        
        # If we included web images, the last result is the images list
        web_images = []
        if include_web and include_images:
            web_images = all_results.pop()

        # If we included web text, the (potentially) last result is the web result
        web_snapshots = []
        if include_web:
            web_res = all_results.pop()
            # If it's a dict (new format), extract docs and raw_results
            if isinstance(web_res, dict):
                web_docs = web_res.get("docs", [])
                web_snapshots = web_res.get("raw_results", [])
            else:
                # Fallback for old list-only format
                web_docs = web_res
            
            web_results = [(doc, 0.1) for doc in web_docs]
            all_results.append(web_results)
        
        # Log branch
        total_retrieved = sum(len(res) for res in all_results)
        print(f"  [RAG] Retrieved {total_retrieved} total candidate chunks.", flush=True)

        # Step 3: Deduplicate
        doc_map: dict[str, Document] = {}
        for result_list in all_results:
            for doc, _score in result_list:
                cid = _content_id(doc)
                if cid not in doc_map:
                    doc_map[cid] = doc
        
        print(f"  [RAG] {len(doc_map)} unique chunks after deduplication.", flush=True)

        # Step 4: Ranked lists
        ranked_lists: List[List[str]] = []
        for result_list in all_results:
            ranked_list = [_content_id(doc) for doc, _score in result_list]
            ranked_lists.append(ranked_list)

        # Step 5: RRF fusion
        merged = _rrf_merge(
            ranked_lists=ranked_lists,
            doc_map=doc_map,
            k=rrf_k,
            top_n=k,
        )

        return {"docs": merged, "images": web_images, "web_results": web_snapshots}

    async def identify_topic(self, query: str) -> Optional[str]:
        """
        Ask Ollama to identify a short (1-3 words) topic for the query.
        Used to label the conversation/answer in the UI.
        """
        # We use a very strict prompt to get just the topic name
        prompt = f"Identify a very short (1-3 words) topic name for this question: '{query}'. Output ONLY the topic name without any punctuation or preamble."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                topic = response.json().get("response", "").strip().strip('"').strip("'")
                
                # Basic sanitization
                topic = re.sub(r'[^\w\s-]', '', topic)
                return topic if topic else None
                
        except Exception as e:
            print(f"[MultiQueryRetriever] Topic identification failed: {e}", flush=True)
            return None

    def search_sync(
        self,
        query: str,
        k: int = 15,
        n_variants: Optional[int] = None,
        include_original: bool = True,
        rrf_k: int = 60,
        include_web: bool = False,
        include_images: bool = False,
    ) -> dict:
        """
        Synchronous wrapper for search().
        """
        import concurrent.futures
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.search(query, k, n_variants, include_original, rrf_k, include_web, include_images),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.search(query, k, n_variants, include_original, rrf_k, include_web, include_images)
                )
        except RuntimeError:
            return asyncio.run(self.search(query, k, n_variants, include_original, rrf_k, include_web, include_images))
