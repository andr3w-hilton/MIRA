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
    """Search Wikipedia for a single topic. Returns extract or empty string."""
    title = _find_page_title(topic)
    if title:
        result = _fetch_extract(title)
        if result:
            return result
    return ""


def research_multi(queries: list[str]) -> str:
    """
    Research multiple search queries and combine results.
    Used when a topic has been decomposed into concrete searchable terms.
    """
    results = []
    seen_titles: set[str] = set()

    for query in queries:
        title = _find_page_title(query)
        if title and title not in seen_titles:
            seen_titles.add(title)
            extract = _fetch_extract(title, max_chars=3000)
            if extract:
                results.append(f"### {title}\n\n{extract}")
                print(f"[Search] Found: {title}")

    if results:
        return "\n\n---\n\n".join(results)

    return ""
