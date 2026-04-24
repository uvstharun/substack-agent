"""Tracks posts the author actually publishes to Substack."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from config.config import cfg
from loguru import logger


def _load() -> list[dict]:
    path = cfg.topics_published_path
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    cfg.topics_published_path.write_text(json.dumps(data, indent=2, default=str))


def mark_published(
    topic_id: str,
    title: str,
    substack_url: str = "",
    performance_notes: str = "",
    category: str = "",
) -> dict:
    existing = _load()
    record = {
        "id": str(uuid.uuid4()),
        "topic_id": topic_id,
        "title": title,
        "substack_url": substack_url,
        "published_at": datetime.now().isoformat(),
        "performance_notes": performance_notes,
        "category": category,
    }
    existing.append(record)
    _save(existing)
    logger.info(f"Marked '{title}' as published")
    return record


def get_all_published() -> list[dict]:
    return _load()


def update_performance_notes(record_id: str, notes: str) -> bool:
    records = _load()
    for r in records:
        if r.get("id") == record_id:
            r["performance_notes"] = notes
            _save(records)
            return True
    return False


def publishing_cadence() -> dict:
    records = _load()
    if not records:
        return {"total_published": 0, "posts_per_month": {}}

    monthly: dict[str, int] = {}
    for r in records:
        published_at = r.get("published_at", "")
        if published_at:
            month_key = published_at[:7]  # YYYY-MM
            monthly[month_key] = monthly.get(month_key, 0) + 1

    return {
        "total_published": len(records),
        "posts_per_month": monthly,
        "category_breakdown": _category_breakdown(records),
    }


def _category_breakdown(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        cat = r.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts
