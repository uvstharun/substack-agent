"""Generates complete, structured post outlines from approved topics."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from agent import orchestrator
from config.config import cfg
from memory import topic_memory, style_memory
from prompts.outline_prompts import build_outline_prompt


def generate_outline(topic: dict) -> dict:
    """
    Generate a full outline for an approved topic.
    Returns the parsed outline dict and saves it to storage/outlines/.
    """
    prefs = style_memory.get_preferences()
    prompt = build_outline_prompt(topic, prefs)

    logger.info(f"Generating outline for: {topic.get('title')}")
    outline = orchestrator.call_json(prompt, max_tokens=4000, temperature=0.75)
    outline["topic_id"] = topic.get("id", "")
    outline["generated_at"] = datetime.now().isoformat()

    _save_outline(topic, outline)
    topic_memory.update_topic_status(topic["id"], "outlined")

    return outline


def _save_outline(topic: dict, outline: dict) -> Path:
    slug = _slugify(topic.get("title", "untitled"))
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{slug}.json"
    path = cfg.outlines_dir / filename
    path.write_text(json.dumps(outline, indent=2, default=str))
    logger.info(f"Outline saved: {path}")
    return path


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].strip("-")


def get_saved_outlines() -> list[dict]:
    """Load all saved outline JSON files from storage."""
    outlines = []
    for f in sorted(cfg.outlines_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            data["_filename"] = f.name
            outlines.append(data)
        except Exception:
            pass
    return outlines


def load_outline_by_filename(filename: str) -> dict | None:
    path = cfg.outlines_dir / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None
