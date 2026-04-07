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

    print("start google search")
    results = DDGS().text(query, max_results=3)
    print("end google search")
    return "\n".join([
        f"{result['title']}: {result['href']}: {result['body']}"
        for result in results
    ])