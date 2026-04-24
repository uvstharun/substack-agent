"""Core topic generation agent — produces 11 personalized Substack topic suggestions per week."""
from __future__ import annotations

from loguru import logger

from agent import orchestrator
from memory import topic_memory, style_memory
from tools.content_scorer import score_topics
from prompts.topic_generation_prompts import (
    build_practical_tutorials_prompt,
    build_career_transition_prompt,
    build_tools_frameworks_prompt,
    build_opinion_hot_takes_prompt,
    build_project_deep_dives_prompt,
)


def _generate_category(prompt: str, category_name: str) -> list[dict]:
    logger.info(f"Generating topics: {category_name}")
    try:
        result = orchestrator.call_json(prompt, max_tokens=3000, temperature=0.9)
        if isinstance(result, dict):
            result = [result]
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Failed to generate {category_name}: {e}")
        return []


def generate_weekly_topics(trend_summary: str = "") -> list[dict]:
    """
    Generate a full week's worth of topic suggestions across all 5 categories.
    Returns a scored, ranked list of topics ready for display.
    """
    already_suggested = topic_memory.get_all_titles()

    prompts = [
        (build_practical_tutorials_prompt(trend_summary, already_suggested), "Practical Tutorials"),
        (build_career_transition_prompt(trend_summary, already_suggested), "Career & Transition"),
        (build_tools_frameworks_prompt(trend_summary, already_suggested), "Tools & Frameworks"),
        (build_opinion_hot_takes_prompt(trend_summary, already_suggested), "Opinion & Hot Takes"),
        (build_project_deep_dives_prompt(trend_summary, already_suggested), "Project Deep-Dives"),
    ]

    all_topics: list[dict] = []
    for prompt, name in prompts:
        topics = _generate_category(prompt, name)
        all_topics.extend(topics)

    logger.info(f"Raw topics generated: {len(all_topics)}")

    scored = score_topics(all_topics)
    saved = topic_memory.add_topics(scored)

    logger.info(f"Weekly topic generation complete — {len(saved)} topics saved")
    return saved


def get_pending_topics() -> list[dict]:
    return topic_memory.get_topics_by_status("suggested")


def get_approved_topics() -> list[dict]:
    return topic_memory.get_topics_by_status("approved")


def approve_topic(topic_id: str) -> bool:
    return topic_memory.update_topic_status(topic_id, "approved")


def dismiss_topic(topic_id: str, reason: str = "") -> bool:
    return topic_memory.update_topic_status(topic_id, "dismissed", dismiss_reason=reason)
