"""Tracks all suggested topics to prevent repetition and enable pattern analysis."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from config.config import cfg
from loguru import logger


def _load() -> list[dict]:
    path = cfg.topics_suggested_path
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    cfg.topics_suggested_path.write_text(json.dumps(data, indent=2, default=str))


def add_topics(topics: list[dict]) -> list[dict]:
    """Persist a batch of suggested topics. Returns them with IDs and timestamps."""
    existing = _load()
    stamped = []
    for t in topics:
        record = {
            **t,
            "id": str(uuid.uuid4()),
            "suggested_at": datetime.now().isoformat(),
            "status": "suggested",  # suggested | approved | dismissed | drafted | published
        }
        existing.append(record)
        stamped.append(record)
    _save(existing)
    logger.info(f"Saved {len(stamped)} topics to memory")
    return stamped


def get_all_topics() -> list[dict]:
    return _load()


def get_topics_by_status(status: str) -> list[dict]:
    return [t for t in _load() if t.get("status") == status]


def update_topic_status(topic_id: str, status: str, **extra_fields) -> bool:
    topics = _load()
    for t in topics:
        if t.get("id") == topic_id:
            t["status"] = status
            t.update(extra_fields)
            _save(topics)
            return True
    return False


def get_all_titles() -> list[str]:
    return [t.get("title", "") for t in _load()]


def is_duplicate(candidate_title: str, threshold: int = 5) -> bool:
    """Rough duplicate check using word overlap (stop-words not filtered)."""
    _STOP = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "is", "are", "how", "why", "what"}
    cand_words = set(candidate_title.lower().split()) - _STOP
    for title in get_all_titles():
        existing_words = set(title.lower().split()) - _STOP
        overlap = cand_words & existing_words
        if len(overlap) >= threshold:
            return True
    return False


def category_distribution() -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in _load():
        cat = t.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def get_series_candidates() -> list[dict]:
    """Identify groups of related topics that could form a series."""
    all_topics = _load()
    keyword_buckets: dict[str, list[dict]] = {}
    for t in all_topics:
        for kw in t.get("seo_keywords", []):
            keyword_buckets.setdefault(kw, []).append(t)

    series = []
    for kw, group in keyword_buckets.items():
        if len(group) >= 3:
            series.append({"keyword": kw, "topic_count": len(group), "topics": group[:5]})
    return sorted(series, key=lambda x: x["topic_count"], reverse=True)
