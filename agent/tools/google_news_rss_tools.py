"""google_news_rss_tools.py
Utility functions decorated as ADK @tool helpers to fetch and parse Google News RSS
feeds.  Designed for use inside an Agent Development Kit (ADK) project.

Usage example inside an Agent:

    from google_news_rss_tools import google_news_search, google_news_top_headlines

    search_agent = Agent(
        model=LiteLlm(model="groq/llama3-70b-8192"),
        tools=[google_news_search, google_news_top_headlines],
        instruction="Use google_news_search to fetch recent items …"
    )

These tools return lists of plain dicts (title, link, published, source), easy to
feed into later steps such as deduplication, BERTopic clustering, or RAG.
"""
from __future__ import annotations

import datetime as _dt
import urllib.parse as _ulib
from typing import List, Dict

import feedparser  # type: ignore

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
_GOOGLE_NEWS_BASE = "https://news.google.com/rss"


def _build_search_url(query: str, *, language: str = "en", country: str = "US") -> str:
    """Craft a Google News *search* RSS URL.

    Google News requires three parameters:
    - **hl**: UI language (e.g. "en-US").
    - **gl**: Geographical edition (country code, e.g. "US").
    - **ceid**: A compound of country & language ("US:en").

    A *search* feed takes the form::
        https://news.google.com/rss/search?q=<QUERY>&hl=en-US&gl=US&ceid=US:en
    """
    q = _ulib.quote_plus(query)
    hl = f"{language}-{country}" if "-" not in language else language
    ceid = f"{country}:{language.split("-")[0]}"
    return f"{_GOOGLE_NEWS_BASE}/search?q={q}&hl={hl}&gl={country}&ceid={ceid}"


def _build_top_headlines_url(*, language: str = "en", country: str = "US") -> str:
    """Return the URL for Google News *Top stories* feed for `country` / `language`."""
    hl = f"{language}-{country}" if "-" not in language else language
    ceid = f"{country}:{language.split("-")[0]}"
    return f"{_GOOGLE_NEWS_BASE}?hl={hl}&gl={country}&ceid={ceid}"


# ---------------------------------------------------------------------------
#   ADK tools
# ---------------------------------------------------------------------------

def google_news_search(
    query: str,
    hours_back: int = 6,
    language: str = "en",
    country: str = "US"
) -> List[Dict[str, str]]:
    """Fetch Google News search feed articles from the last specified hours.
    
    Parameters:
    - query (str): Search phrase (e.g. "artificial intelligence")
    - hours_back (int): Look-back window in hours (default: 6)
    - language (str): Language code (ISO-639-1), default "en"
    - country (str): Country code (ISO-3166-1 alpha-2), default "US"
    
    Returns:
    List[Dict[str, str]]: List of articles, each with 'title', 'link', 'published', and 'source' keys
    
    Example:
        articles = google_news_search("artificial intelligence", hours_back=3)
    "
    """
    url = _build_search_url(query, language=language, country=country)
    feed = feedparser.parse(url)
    cutoff = _dt.datetime.utcnow() - _dt.timedelta(hours=hours_back)

    results: List[Dict] = []
    for entry in feed.entries:
        # Google returns published_parsed as time.struct_time
        pub_dt = _dt.datetime(*entry.published_parsed[:6]) if "published_parsed" in entry else None
        if pub_dt and pub_dt < cutoff:
            continue
        results.append(
            {
                "title": entry.title,
                "link": entry.link,
                "published": pub_dt.isoformat() if pub_dt else None,
                "source": entry.get("source", {}).get("title") if "source" in entry else None,
            }
        )
    return results


def google_news_top_headlines(
    language: str = "en",
    country: str = "US",
    max_items: int = 100
) -> List[Dict[str, str]]:
    """Fetch top headlines from Google News for a specific country and language.
    
    Parameters:
    - language (str): Language code (ISO-639-1), default "en"
    - country (str): Country code (ISO-3166-1 alpha-2), default "US"
    - max_items (int): Maximum number of headlines to return (default: 100, max: 100)
    
    Returns:
    List[Dict[str, str]]: List of articles, each with 'title', 'link', 'published', and 'source' keys
    
    Example:
        headlines = google_news_top_headlines(language="en", country="US", max_items=5)
    "
    """
    url = _build_top_headlines_url(language=language, country=country)
    feed = feedparser.parse(url)
    items = feed.entries[:max_items]
    return [
        {
            "title": e.title,
            "link": e.link,
            "published": _dt.datetime(*e.published_parsed[:6]).isoformat() if "published_parsed" in e else None,
            "source": e.get("source", {}).get("title") if "source" in e else None,
        }
        for e in items
    ]


# ---------------------------------------------------------------------------
# Standalone test ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, sys

    q = sys.argv[1] if len(sys.argv) > 1 else "technology"
    articles = google_news_search(q, hours_back=3)
    print(json.dumps(articles[:5], ensure_ascii=False, indent=2))
