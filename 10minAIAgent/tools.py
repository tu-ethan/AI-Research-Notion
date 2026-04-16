from langchain_core.tools import tool
from ddgs import DDGS
import requests

# taking took out of commission because its very complex, the query doesn't always line up with a webpage
@tool
def wikipedia_search(query: str) -> str:
    """
    Search Wikipedia for a given query and return the summary of the top result.
    """
    print("start wiki search")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("end wiki search")
        return data.get("extract", "No summary available.")
    else:
        print("wiki serach failed")
        return "Error fetching data from Wikipedia."
    
@tool
def duckduckgo_search(query: str) -> str:
    """Search the web using DuckDuckGo and return the top 3 results"""

    try:
        print("start search")
        results = DDGS().text(query, max_results=3)
        print("end search")

        if not results:
            print("SEARCH FAILED: no results found")
            return {
                "text": "SEARCH_FAILED: no results found",
                "results": []
            }
        
        clean_results = [
            {
                "title": r["title"],
                "url": r["href"],
                "summary": r["body"]
            }
            for r in results
        ]

        return {
            "text": "\n".join(
                f"{r['title']}: {r['url']}: {r['summary']}"
                for r in clean_results
            ),
            "results": clean_results
        }
    except Exception as e:
        print("SEARCH_FAILED: {str(e)}")
        return {
                "text": f"SEARCH_FAILED: {str(e)}",
                "results": []
            }