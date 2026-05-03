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


def _collect(queries: list[str], max_items: int, recency: str | None) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        results = search(query, max_results=5, recency=recency)
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


def fetch_news_snippets(max_items: int = 30, min_required: int = 5) -> list[dict]:
    """
    Fetch recent AI news snippets for topic ideation.

    Tries with the 'past month' DDG date filter first; if the result count
    is below `min_required`, retries without any date filter so the agent
    never silently runs out of context to work with.
    """
    logger.info("Fetching recent AI news (past month filter)...")
    items = _collect(_NEWS_QUERIES, max_items=max_items, recency="m")

    if len(items) < min_required:
        logger.warning(
            f"Only {len(items)} items with date filter; retrying without it"
        )
        items = _collect(_NEWS_QUERIES, max_items=max_items, recency=None)

    logger.info(f"News fetch complete: {len(items)} items")
    return items


def _collect_trend_snippets(recency: str | None) -> tuple[list[str], list[dict]]:
    snippets: list[str] = []
    sources: list[dict] = []
    for query in _SEARCH_QUERIES:
        results = search(query, max_results=5, recency=recency)
        for r in results:
            snippet = r.get("snippet", "").strip()
            if snippet and len(snippet) > 40:
                snippets.append(snippet)
                sources.append({"title": r.get("title", ""), "url": r.get("url", "")})
    return snippets, sources


def fetch_trend_report(min_required: int = 8) -> dict:
    """
    Run searches across the generalist AI/DS landscape. Tries with the past-month
    date filter first; if the result count is below `min_required`, retries with
    no date filter so the agent never has to fall back to "no fresh trend data".
    """
    logger.info("Starting trend research (past month filter)...")
    all_snippets, sources = _collect_trend_snippets(recency="m")

    if len(all_snippets) < min_required:
        logger.warning(
            f"Only {len(all_snippets)} trend snippets with date filter; retrying without it"
        )
        all_snippets, sources = _collect_trend_snippets(recency=None)

    # Deduplicate loosely by snippet start
    seen: set[str] = set()
    unique_snippets: list[str] = []
    for s in all_snippets:
        key = s[:60]
        if key not in seen:
            seen.add(key)
            unique_snippets.append(s)

    trend_text = "\n\n".join(unique_snippets[:40])
    logger.info(f"Trend research complete: {len(unique_snippets)} unique snippets")

    return {
        "summary": trend_text,
        "source_count": len(sources),
        "queries_run": _SEARCH_QUERIES,
    }
