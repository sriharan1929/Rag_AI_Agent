import asyncio
from duckduckgo_search import DDGS

async def test_ddgs():
    print("Testing DDGS text search with 'python'...")
    try:
        with DDGS() as ddgs:
            gen = ddgs.text("python", max_results=5)
            print(f"Generator type: {type(gen)}")
            results = list(gen)
            print(f"Results list: {results}")
            print(f"Results found count: {len(results)}")
            for r in results:
                print(f"- {r.get('title')}")
    except Exception as e:
        print(f"Error in text search: {e}")
        import traceback
        traceback.print_exc()

    print("\nTesting DDGS image search with 'python'...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images("python", max_results=5))
            print(f"Images found count: {len(results)}")
            for r in results:
                print(f"- {r.get('title')}: {r.get('image')}")
    except Exception as e:
        print(f"Error in image search: {e}")

if __name__ == "__main__":
    asyncio.run(test_ddgs())
