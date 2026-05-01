"""Suggests human-feeling comments for tech / AI Substack posts and Notes."""
from __future__ import annotations

from loguru import logger

from agent import orchestrator
from prompts.comment_prompts import build_comment_suggester_prompt


_AUTHOR_CONTEXT = """\
You are a data scientist with about 2 years of experience, learning to build with LLMs and
agents. You write a generalist AI/Data Science Substack. When you comment, speak from real
practitioner experience: SARIMAX models, NLP pipelines, RAG, Claude/agent experiments,
debugging production ML at a public health system. Be honest, never name-drop your employer,
never self-promote.
"""


def suggest_comments(post_text: str) -> str:
    """Return a numbered list of 3 comment suggestions."""
    logger.info(f"Suggesting comments for post of length {len(post_text)} chars")
    prompt = build_comment_suggester_prompt(post_text, author_context=_AUTHOR_CONTEXT)
    response = orchestrator.call(prompt, max_tokens=800, temperature=0.85)
    return response.strip()
