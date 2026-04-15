from langchain_core.tools import tool
from ddgs import DDGS
import requests

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
            print("no results found")
            return "SEARCH_FAILED: no results found"
        return "\n".join([
            f"{result['title']}: {result['href']}: {result['body']}"
            for result in results
        ])
    except Exception as e:
        print("search failed")
        return f"SEARCH_FAILED: {str(e)}"