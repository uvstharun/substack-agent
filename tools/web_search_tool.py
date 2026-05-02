"""Lightweight web search wrapper using DuckDuckGo's HTML interface (no API key required)."""
from __future__ import annotations

import time
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

_DDG_URL = "https://html.duckduckgo.com/html/"


def search(
    query: str,
    max_results: int = 8,
    sleep_secs: float = 1.0,
    recency: str | None = None,
) -> list[dict]:
    """Search DuckDuckGo and return a list of {title, url, snippet} dicts.

    recency: optional date filter. One of: 'd' (past day), 'w' (past week),
    'm' (past month), 'y' (past year). None = no date filter.
    """
    try:
        time.sleep(sleep_secs)
        data = {"q": query, "b": "", "kl": "us-en"}
        if recency in {"d", "w", "m", "y"}:
            data["df"] = recency
        resp = httpx.post(
            _DDG_URL,
            data=data,
            headers=_HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.warning(f"Web search failed for '{query}': {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[dict] = []

    for result in soup.select(".result__body")[:max_results]:
        title_tag = result.select_one(".result__title")
        snippet_tag = result.select_one(".result__snippet")
        link_tag = result.select_one(".result__url")

        title = title_tag.get_text(strip=True) if title_tag else ""
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        url = link_tag.get_text(strip=True) if link_tag else ""

        if title or snippet:
            results.append({"title": title, "url": url, "snippet": snippet})

    logger.info(f"Web search '{query}' → {len(results)} results")
    return results


def fetch_page_text(url: str, max_chars: int = 4000) -> str:
    """Fetch and extract plain text from a URL."""
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception as exc:
        logger.warning(f"Page fetch failed for '{url}': {exc}")
        return ""
