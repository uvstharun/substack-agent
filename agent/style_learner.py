"""Processes author feedback and updates accumulated style preferences."""
from __future__ import annotations

from loguru import logger

from agent import orchestrator
from memory import style_memory
from prompts.style_prompts import STYLE_FEEDBACK_PROCESSING_PROMPT


def process_feedback(
    feedback_text: str,
    rating: int | None = None,
    content_type: str = "draft",
) -> dict:
    """
    Parse free-form feedback text using Claude, then apply structured adjustments
    to the style memory. Returns the parsed adjustments dict.
    """
    prompt = f"""\
{STYLE_FEEDBACK_PROCESSING_PROMPT}

Author feedback:
\"\"\"{feedback_text}\"\"\"

Current style preferences:
{style_memory.get_preferences()}
"""
    try:
        adjustments = orchestrator.call_json(prompt, max_tokens=800, temperature=0.3)
    except Exception as e:
        logger.error(f"Failed to parse style feedback: {e}")
        adjustments = {}

    style_memory.apply_feedback(
        feedback_text=feedback_text,
        rating=rating,
        content_type=content_type,
        parsed_adjustments=adjustments if isinstance(adjustments, dict) else {},
    )

    logger.info(f"Style feedback processed (rating={rating}): {adjustments}")
    return adjustments


def get_current_preferences() -> dict:
    return style_memory.get_preferences()


def manually_update_preference(key: str, value) -> None:
    """Direct update for slider/toggle controls in the UI."""
    style_memory.update_preference(key, value)
    logger.info(f"Style preference updated: {key} = {value}")


def get_feedback_history() -> list[dict]:
    return style_memory.get_feedback_history()
