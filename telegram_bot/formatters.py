"""Format agent output into clean Telegram HTML messages."""
from __future__ import annotations

_CATEGORY_EMOJI = {
    "practical_tutorials": "🛠",
    "career_and_transition": "🚀",
    "tools_and_frameworks": "⚙️",
    "opinion_hot_takes": "🔥",
    "project_deep_dives": "🔬",
}

_FORMAT_EMOJI = {
    "personal story": "📖",
    "how-to guide": "📋",
    "opinion piece": "💬",
    "technical explainer": "🧠",
    "case study": "📊",
}


def _h(text: str) -> str:
    """Escape text for Telegram HTML parse mode."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_topic_card(index: int, topic: dict) -> str:
    cat = topic.get("category", "")
    cat_emoji = _CATEGORY_EMOJI.get(cat, "📝")
    fmt = topic.get("recommended_format", "")
    fmt_emoji = _FORMAT_EMOJI.get(fmt, "📝")
    scores = topic.get("scores", {})
    composite = scores.get("composite_score", topic.get("virality_score", "—"))
    virality = topic.get("virality_score", "—")
    career = topic.get("career_positioning_score", "—")
    read_time = topic.get("estimated_read_time_minutes", "—")
    keywords = ", ".join(topic.get("seo_keywords", [])[:3])
    why_now = topic.get("why_now", "")[:280]

    return (
        f"{cat_emoji} <b>{index}. {_h(topic.get('title', ''))}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Score: <code>{composite}/10</code> | 🔥 Viral: <code>{virality}</code> | 🎯 Career: <code>{career}</code>\n"
        f"{fmt_emoji} {_h(fmt)} | ⏱ {_h(read_time)} min read\n"
        f"\n"
        f"<i>{_h(why_now)}</i>\n"
        f"\n"
        f"🏷 <code>{_h(keywords)}</code>"
    )


def format_topics_batch(topics: list[dict], start_index: int = 1) -> list[str]:
    """Return list of formatted topic card strings, one per topic."""
    return [format_topic_card(i + start_index, t) for i, t in enumerate(topics)]


def format_outline_summary(outline: dict) -> str:
    title = outline.get("topic_title", "Untitled")
    total_words = outline.get("total_estimated_word_count", "—")
    read_time = outline.get("estimated_read_time_minutes", "—")

    headlines = outline.get("headline_options", [])
    headline_lines = "\n".join(
        f"  • <b>{_h(h.get('angle','').title())}:</b> {_h(h.get('title',''))}"
        for h in headlines
    )

    hooks = outline.get("hook_options", [])
    hook_preview = hooks[0].get("text", "")[:200] if hooks else ""

    sections = outline.get("sections", [])
    section_lines = "\n".join(
        f"  {i+1}. {_h(s.get('title',''))} (~{s.get('estimated_word_count','')}w)"
        for i, s in enumerate(sections)
    )

    return (
        f"📋 <b>Outline: {_h(title)}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📏 {_h(str(total_words))} words | ⏱ {_h(str(read_time))} min read\n\n"
        f"<b>Headline options:</b>\n{headline_lines}\n\n"
        f"<b>Opening hook preview:</b>\n<i>{_h(hook_preview)}…</i>\n\n"
        f"<b>Post sections:</b>\n{section_lines}\n\n"
        f"Send /draft to write the full first draft."
    )


def format_pipeline_status(topics: list[dict]) -> str:
    from collections import Counter
    counts = Counter(t.get("status", "unknown") for t in topics)
    lines = "\n".join(
        f"  • {status.title()}: {count}"
        for status, count in sorted(counts.items())
    )
    return (
        f"📊 <b>Pipeline Status</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{lines or '  No topics yet'}\n\n"
        f"Send /topics to generate fresh suggestions."
    )
