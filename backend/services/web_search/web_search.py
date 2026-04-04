import asyncio
from duckduckgo_search import DDGS
from langchain_core.documents import Document

class WebSearchTool:
    def __init__(self):
        # We don't need to initialize anything early for DDGS
        pass

    async def search_async(self, query: str, max_results: int = 5):
        """
        Run DuckDuckGo search using the native DDGS library in a thread pool.
        Includes a fallback for text searches to improve reliability in case
        the default backend (Bing) is being rate-limited or blocked.
        """
        loop = asyncio.get_event_loop()
        try:
            def _sync_search():
                with DDGS() as ddgs:
                    # Try the standard text search first
                    # In v8.1.1, this is currently hardcoded to use only Bing.
                    try:
                        results = ddgs.text(query, max_results=max_results)
                    except Exception as e:
                        print(f"[WebSearch] Warning: Standard search failed: {e}")
                        results = []

                    # Fallback chain: if 'bing' fails, try 'html', then 'lite'
                    if not results:
                        try:
                            print(f"[WebSearch] Trying HTML fallback...")
                            results = ddgs._text_html(query, max_results=max_results)
                        except Exception as e:
                            print(f"[WebSearch] Warning: HTML fallback failed: {e}")
                    
                    if not results:
                        try:
                            print(f"[WebSearch] Trying Lite fallback...")
                            results = ddgs._text_lite(query, max_results=max_results)
                        except Exception as e:
                            print(f"[WebSearch] Warning: Lite fallback failed: {e}")
                    
                    return results if results else []

            raw_results = await loop.run_in_executor(None, _sync_search)
            
            # Format results as Documents
            docs = []
            for r in raw_results:
                source = r.get("href", "DuckDuckGo")
                title = r.get("title", "")
                body = r.get("body", "")
                
                content = f"{title}\n{body}" if body else title
                
                docs.append(Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "title": title,
                        "snippet": body,
                        "query": query
                    }
                ))
            
            return docs
        except Exception as e:
            print(f"[WebSearch] Error: {e}")
            return []

    async def search_images_async(self, query: str, max_results: int = 8):
        """
        Run DuckDuckGo image search using the native DDGS library in a thread pool.
        """
        loop = asyncio.get_event_loop()
        try:
            def _sync_image_search():
                with DDGS() as ddgs:
                    return ddgs.images(query, max_results=max_results)

            raw_results = await loop.run_in_executor(None, _sync_image_search)
            
            # Extract just the image URLs and titles
            images = []
            for r in raw_results:
                images.append({
                    "url": r.get("image"),
                    "title": r.get("title"),
                    "source": r.get("source"),
                    "thumbnail": r.get("thumbnail")
                })
            
            return images
        except Exception as e:
            print(f"[WebImageSearch] Error: {e}")
            return []

if __name__ == "__main__":
    # Quick test
    tool = WebSearchTool()
    
    print("Testing text search...")
    res = asyncio.run(tool.search_async("Python programming"))
    print(f"Results: {len(res)}")
    for d in res[:2]:
        print(f"- {d.metadata['title']} ({d.metadata['source']})")

    print("\nTesting image search...")
    img_res = asyncio.run(tool.search_images_async("Python logo"))
    print(f"Results: {len(img_res)}")
    for img in img_res[:2]:
        print(f"- {img['title']} ({img['url']})")
