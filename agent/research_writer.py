"""Research-grounded Substack post writer.

Given a user-supplied topic, this module:
1. Searches the web for relevant articles (no date filter, but biased toward recency).
2. Hands the raw snippets to Claude with a strict "ground every claim in these sources" rule.
3. Returns the post markdown plus the structured source list.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger

from agent import orchestrator
from config.config import cfg
from prompts.research_prompts import build_research_post_prompt
from tools.web_search_tool import search


# How many distinct queries to fan out per topic. Higher = broader coverage.
_QUERY_COUNT_PER_TOPIC = 4

# Min number of usable snippets we want before calling the model.
_MIN_SOURCES_OK = 4
_LIMITED_SOURCES_THRESHOLD = 6  # below this, we flag the post as exploratory


def _expand_queries(topic: str) -> list[str]:
    """Generate a small set of related search queries for broader coverage."""
    base = topic.strip()
    return [
        base,
        f"{base} 2026",
        f"{base} news",
        f"{base} research",
    ][:_QUERY_COUNT_PER_TOPIC]


def _fetch_sources(topic: str, max_total: int = 20) -> list[dict]:
    """Run multiple searches, dedupe, and return up to max_total source dicts."""
    items: list[dict] = []
    seen: set[str] = set()

    for query in _expand_queries(topic):
        # First try with no date filter (any timeframe).
        results = search(query, max_results=6)
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
            if len(items) >= max_total:
                return items
    return items


def _format_sources_for_prompt(items: list[dict]) -> str:
    """Format source items into a readable block for the prompt."""
    if not items:
        return "(No sources fetched. Do not invent facts. Tell the user the search returned nothing usable.)"
    lines: list[str] = []
    for i, it in enumerate(items, 1):
        lines.append(
            f"[{i}] {it['title']}\n    URL: {it.get('url') or '(no url)'}\n    Snippet: {it['snippet']}"
        )
    return "\n\n".join(lines)


def _save_post(topic: str, markdown: str) -> Path:
    """Save the post under storage/research/ for local reference."""
    out_dir = cfg.storage_path / "research"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = "".join(c if c.isalnum() else "-" for c in topic.lower()).strip("-")[:50] or "post"
    path = out_dir / f"{date_str}_{slug}.md"
    path.write_text(markdown, encoding="utf-8")
    logger.info(f"Research post saved: {path}")
    return path


def research_and_write(topic: str) -> dict:
    """Search the web for `topic`, then write a 700-1000 word grounded Substack post.

    Returns:
        {
          "post": str,            # markdown
          "sources": list[dict],  # the raw source list used
          "path": Path | None,    # saved file path
          "sufficient": bool,     # whether enough sources were available
        }
    """
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Empty topic")

    logger.info(f"Research+write: topic='{topic}'")

    sources = _fetch_sources(topic)
    sufficient = len(sources) >= _MIN_SOURCES_OK
    limited = len(sources) < _LIMITED_SOURCES_THRESHOLD

    if not sources:
        msg = (
            f"# {topic}\n\n"
            "_The web search returned no usable sources for this topic. "
            "Try rephrasing or breaking it into a narrower question, then run /research again._\n"
        )
        return {"post": msg, "sources": [], "path": None, "sufficient": False}

    sources_text = _format_sources_for_prompt(sources)
    prompt = build_research_post_prompt(
        topic=topic,
        sources_text=sources_text,
        limited_sources=limited,
    )

    post = orchestrator.call(prompt, max_tokens=3500, temperature=0.75)

    path = _save_post(topic, post)

    return {
        "post": post,
        "sources": sources,
        "path": path,
        "sufficient": sufficient,
    }
