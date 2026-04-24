"""Generates complete first-draft Substack posts from approved outlines."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from agent import orchestrator
from config.config import cfg
from memory import topic_memory, style_memory
from prompts.draft_prompts import build_draft_prompt


def write_draft(topic: dict, outline: dict) -> str:
    """
    Generate a complete first draft from a topic + outline.
    Returns the draft markdown string and saves it to storage/drafts/.
    """
    prefs = style_memory.get_preferences()
    prompt = build_draft_prompt(topic, outline, prefs)

    logger.info(f"Writing draft for: {topic.get('title')}")
    draft_markdown = orchestrator.call(prompt, max_tokens=6000, temperature=0.85)

    _save_draft(topic, draft_markdown)
    topic_memory.update_topic_status(topic.get("id", ""), "drafted")

    return draft_markdown


def write_draft_streaming(topic: dict, outline: dict):
    """Generator version — yields text chunks for Streamlit st.write_stream."""
    prefs = style_memory.get_preferences()
    prompt = build_draft_prompt(topic, outline, prefs)

    logger.info(f"Streaming draft for: {topic.get('title')}")
    full_text = []
    for chunk in orchestrator.stream(prompt, max_tokens=6000, temperature=0.85):
        full_text.append(chunk)
        yield chunk

    draft_markdown = "".join(full_text)
    _save_draft(topic, draft_markdown)
    topic_memory.update_topic_status(topic.get("id", ""), "drafted")


def _save_draft(topic: dict, markdown: str) -> Path:
    slug = _slugify(topic.get("title", "untitled"))
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{slug}.md"
    path = cfg.drafts_dir / filename
    path.write_text(markdown, encoding="utf-8")
    logger.info(f"Draft saved: {path}")
    return path


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60].strip("-")


def get_saved_drafts() -> list[dict]:
    """Return metadata for all saved drafts."""
    drafts = []
    for f in sorted(cfg.drafts_dir.glob("*.md"), reverse=True):
        try:
            content = f.read_text(encoding="utf-8")
            first_line = content.split("\n")[0].lstrip("# ").strip()
            drafts.append({
                "filename": f.name,
                "title": first_line or f.stem,
                "word_count": len(content.split()),
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
        except Exception:
            pass
    return drafts


def load_draft(filename: str) -> str | None:
    path = cfg.drafts_dir / filename
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def save_edited_draft(filename: str, content: str) -> None:
    path = cfg.drafts_dir / filename
    path.write_text(content, encoding="utf-8")
    logger.info(f"Draft edited and saved: {filename}")
