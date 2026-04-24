"""Keyword research — identifies SEO-relevant keywords for healthcare AI topics."""
from __future__ import annotations

from tools.web_search_tool import search
from loguru import logger


_SEED_KEYWORDS = [
    "healthcare data science",
    "healthcare AI",
    "clinical machine learning",
    "health informatics",
    "hospital analytics",
    "medical AI",
    "clinical NLP",
    "healthcare LLM",
    "AI in healthcare",
    "SDOH machine learning",
    "readmission prediction",
    "healthcare forecasting",
]


def get_related_keywords(topic_title: str) -> list[str]:
    """Find related search terms for a topic using DuckDuckGo autocomplete signals."""
    results = search(f"{topic_title} healthcare data science", max_results=10)
    keywords: set[str] = set()

    for r in results:
        snippet = r.get("snippet", "").lower()
        for seed in _SEED_KEYWORDS:
            if seed in snippet:
                keywords.add(seed)

    # Add the seeds themselves that are topically relevant
    title_lower = topic_title.lower()
    for seed in _SEED_KEYWORDS:
        if any(word in title_lower for word in seed.split()):
            keywords.add(seed)

    keyword_list = list(keywords)[:8]
    logger.debug(f"Keywords for '{topic_title}': {keyword_list}")
    return keyword_list
