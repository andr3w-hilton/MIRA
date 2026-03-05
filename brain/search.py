"""
Mira's internet access - Wikipedia and web search.
"""
import requests
from typing import Optional

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "Mira-LearningBot/1.0 (self-teaching AI; github.com/andr3w-hilton/AI_Tools)"}


def _find_page_title(query: str) -> Optional[str]:
    """Use Wikipedia's search to find the best matching page title for a query."""
    params = {
        "action": "opensearch",
        "format": "json",
        "search": query,
        "limit": 1,
        "redirects": "resolve",
    }
    try:
        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        results = response.json()
        titles = results[1] if len(results) > 1 else []
        return titles[0] if titles else None
    except Exception as e:
        print(f"[Search] Wikipedia title search failed: {e}")
        return None


def _fetch_extract(title: str, max_chars: int = 5000) -> Optional[str]:
    """Fetch a plain-text Wikipedia extract by exact page title."""
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "redirects": True,
    }
    try:
        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id != "-1":
                extract = page.get("extract", "")
                return extract[:max_chars] if extract else None
        return None
    except Exception as e:
        print(f"[Search] Wikipedia fetch failed: {e}")
        return None


def research(topic: str) -> str:
    """
    Primary research function. Searches Wikipedia for the topic and returns an extract.
    Two-step: find best matching title, then fetch its content.
    TODO: add DuckDuckGo / Brave Search API for broader web access.
    """
    title = _find_page_title(topic)
    if title:
        result = _fetch_extract(title)
        if result:
            return result
    return f"No information found for: {topic}"
