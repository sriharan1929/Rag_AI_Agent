import asyncio
import time
from duckduckgo_search import DDGS
from web_search import WebSearchTool

async def final_verify():
    tool = WebSearchTool()
    
    # Wait a bit to clear any temp blocks
    print("Waiting 2 seconds...")
    await asyncio.sleep(2)
    
    print("Testing text search with 'GitHub'...")
    try:
        res = await tool.search_async("GitHub", max_results=2)
        print(f"Text results count: {len(res)}")
        for d in res:
            print(f"- {d.metadata['title']}")
    except Exception as e:
        print(f"Text search failed: {e}")

    await asyncio.sleep(2)
    
    print("\nTesting image search with 'GitHub logo'...")
    try:
        img_res = await tool.search_images_async("GitHub logo", max_results=2)
        print(f"Image results count: {len(img_res)}")
        for img in img_res:
            print(f"- {img['title']} ({img['url']})")
    except Exception as e:
        print(f"Image search failed: {e}")

if __name__ == "__main__":
    asyncio.run(final_verify())
