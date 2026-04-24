"""Stores and retrieves the author's accumulated writing style preferences."""
from __future__ import annotations

import json
from datetime import datetime

from config.config import cfg
from loguru import logger

_DEFAULTS: dict = {
    "tone": "conversational",
    "length": "medium",
    "technical_depth": "balanced",
    "preferred_hook": "personal_story",
    "wants_more": ["personal stories", "concrete examples", "specific numbers"],
    "wants_less": ["generic AI hype", "vague claims", "lengthy definitions"],
    "phrases_to_avoid": [],
    "free_form_notes": "",
    "feedback_history": [],
    "updated_at": None,
}


def _load() -> dict:
    path = cfg.style_memory_path
    if not path.exists():
        return dict(_DEFAULTS)
    try:
        data = json.loads(path.read_text())
        return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


def _save(data: dict) -> None:
    cfg.style_memory_path.write_text(json.dumps(data, indent=2, default=str))


def get_preferences() -> dict:
    prefs = _load()
    prefs.pop("feedback_history", None)
    return prefs


def get_full_memory() -> dict:
    return _load()


def apply_feedback(
    feedback_text: str,
    rating: int | None = None,
    content_type: str = "draft",
    parsed_adjustments: dict | None = None,
) -> None:
    memory = _load()

    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "content_type": content_type,
        "rating": rating,
        "feedback_text": feedback_text,
        "adjustments_applied": parsed_adjustments or {},
    }
    memory.setdefault("feedback_history", []).append(feedback_entry)

    if parsed_adjustments:
        adj = parsed_adjustments

        tone_map = {
            "more_casual": "casual",
            "more_formal": "formal",
            "more_technical": "technical",
            "less_technical": "accessible",
        }
        if adj.get("tone_adjustment") and adj["tone_adjustment"] in tone_map:
            memory["tone"] = tone_map[adj["tone_adjustment"]]

        if adj.get("length_adjustment") == "shorter":
            length_step = {"long": "medium", "medium": "short"}.get(memory["length"], "short")
            memory["length"] = length_step
        elif adj.get("length_adjustment") == "longer":
            length_step = {"short": "medium", "medium": "long"}.get(memory["length"], "long")
            memory["length"] = length_step

        if adj.get("hook_preference"):
            memory["preferred_hook"] = adj["hook_preference"]

        cp = adj.get("content_type_preferences", {})
        for item in cp.get("wants_more", []):
            if item not in memory["wants_more"]:
                memory["wants_more"].append(item)
        for item in cp.get("wants_less", []):
            if item not in memory["wants_less"]:
                memory["wants_less"].append(item)

        if adj.get("structure_notes"):
            existing = memory.get("free_form_notes", "")
            memory["free_form_notes"] = f"{existing}\n{adj['structure_notes']}".strip()

    memory["updated_at"] = datetime.now().isoformat()
    _save(memory)
    logger.info(f"Style memory updated from feedback (rating={rating})")


def update_preference(key: str, value) -> None:
    memory = _load()
    memory[key] = value
    memory["updated_at"] = datetime.now().isoformat()
    _save(memory)


def get_feedback_history() -> list[dict]:
    return _load().get("feedback_history", [])
