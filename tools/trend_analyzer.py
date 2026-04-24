"""Trend research tool — queries healthcare AI / data science trends via web search."""
from __future__ import annotations

from loguru import logger
from tools.web_search_tool import search


_SEARCH_QUERIES = [
    "AI news this week",
    "latest LLM model release",
    "new AI agent framework release",
    "OpenAI Anthropic Google DeepMind announcement this week",
    "AI research paper breakthrough recent",
    "AI industry news last 72 hours",
    "data science machine learning news this week",
    "AI developer tools release",
    "RAG vector database news",
    "multi-agent system release news",
]


_NEWS_QUERIES = [
    "AI news today",
    "AI announcement this week",
    "new LLM release",
    "AI model launched",
    "AI startup news recent",
    "Anthropic OpenAI Google AI news",
    "AI research paper viral recent",
    "AI developer tool launch",
]


def fetch_news_snippets(max_items: int = 30) -> list[dict]:
    """Fetch recent AI news snippets with titles and urls for topic ideation."""
    logger.info("Fetching recent AI news...")
    items: list[dict] = []
    seen: set[str] = set()

    for query in _NEWS_QUERIES:
        results = search(query, max_results=5)
        for r in results:
            title = r.get("title", "").strip()
            snippet = r.get("snippet", "").strip()
            url = r.get("url", "").strip()
            if not title or len(snippet) < 40:
                continue
            key = title[:60].lower()
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": title, "snippet": snippet, "url": url})
            if len(items) >= max_items:
                return items
    return items


def fetch_trend_report() -> dict:
    """
    Run searches across healthcare AI / data science topics and return a structured
    trend report consumed by the topic generator.
    """
    logger.info("Starting trend research...")
    all_snippets: list[str] = []
    sources: list[dict] = []

    for query in _SEARCH_QUERIES:
        results = search(query, max_results=5)
        for r in results:
            snippet = r.get("snippet", "").strip()
            if snippet and len(snippet) > 40:
                all_snippets.append(snippet)
                sources.append({"title": r.get("title", ""), "url": r.get("url", "")})

    # Deduplicate loosely by snippet start
    seen: set[str] = set()
    unique_snippets: list[str] = []
    for s in all_snippets:
        key = s[:60]
        if key not in seen:
            seen.add(key)
            unique_snippets.append(s)

    trend_text = "\n\n".join(unique_snippets[:40])

    logger.info(f"Trend research complete — {len(unique_snippets)} unique snippets collected")

    return {
        "summary": trend_text,
        "source_count": len(sources),
        "queries_run": _SEARCH_QUERIES,
    }
