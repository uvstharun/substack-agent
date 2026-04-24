"""Generates short daily Substack posts: AI news, job tips, learning logs, first post."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from agent import orchestrator
from agent.trend_researcher import get_trend_summary
from config.config import cfg
from prompts.daily_prompts import (
    build_ai_news_prompt,
    build_job_tip_prompt,
    build_daily_learning_prompt,
)
from prompts.onboarding_prompts import FIRST_POST_COACHING


# ── Storage helpers ───────────────────────────────────────────────────────────

def _daily_dir() -> Path:
    d = cfg.storage_path / "daily"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _log_path() -> Path:
    return cfg.storage_path / "daily_log.json"


def _load_log() -> list[dict]:
    path = _log_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _append_log(entry: dict) -> None:
    log = _load_log()
    log.append(entry)
    _log_path().write_text(json.dumps(log, indent=2, default=str))


def _slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text)
    return text[:50].strip("-") or "post"


def _save_post(kind: str, markdown: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    first_line = markdown.strip().split("\n")[0].lstrip("# ").strip()
    slug = _slugify(first_line or kind)
    filename = f"{date_str}_{kind}_{slug}.md"
    path = _daily_dir() / filename
    path.write_text(markdown, encoding="utf-8")
    _append_log({
        "timestamp": datetime.now().isoformat(),
        "kind": kind,
        "title": first_line,
        "filename": filename,
    })
    logger.info(f"Daily post saved: {filename}")
    return path


def _recent_titles_by_kind(kind: str, limit: int = 7) -> list[str]:
    log = _load_log()
    titles = [e.get("title", "") for e in log if e.get("kind") == kind]
    return titles[-limit:]


# ── Content generators ────────────────────────────────────────────────────────

def generate_ai_news_post() -> str:
    logger.info("Generating daily AI news post...")
    trend = get_trend_summary()
    prompt = build_ai_news_prompt(trend)
    post = orchestrator.call(prompt, max_tokens=1200, temperature=0.85)
    _save_post("ai_news", post)
    return post


def generate_job_tip_post() -> str:
    logger.info("Generating daily job tip post...")
    recent = _recent_titles_by_kind("job_tip")
    prompt = build_job_tip_prompt(recent_tips=recent)
    post = orchestrator.call(prompt, max_tokens=1200, temperature=0.85)
    _save_post("job_tip", post)
    return post


def generate_learning_post(raw_learning: str) -> str:
    logger.info("Generating daily learning post from user note...")
    recent = _recent_titles_by_kind("learning")
    prompt = build_daily_learning_prompt(raw_learning, recent_learnings=recent)
    post = orchestrator.call(prompt, max_tokens=1000, temperature=0.8)
    _save_post("learning", post)
    return post


def generate_first_post() -> str:
    logger.info("Generating first-ever Substack post with coaching...")
    post = orchestrator.call(
        FIRST_POST_COACHING,
        max_tokens=2500,
        temperature=0.75,
    )
    _save_post("first_post", post)
    return post


def generate_daily_pack() -> dict:
    """Run all three daily generators and return the results."""
    return {
        "ai_news": generate_ai_news_post(),
        "job_tip": generate_job_tip_post(),
        "learning_prompt": (
            "🎓 <b>Daily learning prompt</b>\n\n"
            "What did you learn or debug today? Reply with /learned &lt;your rough notes&gt; "
            "and I'll turn it into a polished short post."
        ),
    }


def recent_daily_posts(limit: int = 10) -> list[dict]:
    return _load_log()[-limit:]
