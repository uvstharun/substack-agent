"""Tests for topic generation logic."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_topic(category: str, title: str = "Test Topic") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "why_now": "This is why this topic matters right now in healthcare AI.",
        "target_reader": "Healthcare data scientists",
        "estimated_read_time_minutes": 7,
        "virality_score": 7,
        "virality_reasoning": "Practical and timely",
        "career_positioning_score": 8,
        "career_positioning_reasoning": "Builds brand as Healthcare AI specialist",
        "suggested_series": "Healthcare AI in Practice",
        "seo_keywords": ["healthcare ai", "data science", "clinical ml"],
        "similar_posts_to_differentiate_from": ["Example post A"],
        "recommended_format": "personal story",
        "category": category,
        "status": "suggested",
    }


# ── Scoring tests ─────────────────────────────────────────────────────────────

class TestContentScorer:
    def test_score_returns_values_in_range(self):
        from tools.content_scorer import score_topic
        topic = _make_topic("lessons_from_work")
        score = score_topic(topic)
        assert 1 <= score.audience_fit <= 10
        assert 1 <= score.originality <= 10
        assert 1 <= score.timeliness <= 10
        assert 1 <= score.career_positioning <= 10

    def test_composite_score_is_average(self):
        from tools.content_scorer import score_topic
        topic = _make_topic("healthcare_ai_explainers")
        score = score_topic(topic)
        expected = round(
            (score.audience_fit + score.originality + score.timeliness + score.career_positioning) / 4, 1
        )
        assert score.composite_score == expected

    def test_effort_estimate_is_valid(self):
        from tools.content_scorer import score_topic
        for cat in ["lessons_from_work", "healthcare_ai_explainers", "career_and_transition",
                    "trending_through_healthcare", "opinion_hot_takes"]:
            score = score_topic(_make_topic(cat))
            assert score.effort_estimate in ("low", "medium", "high")

    def test_score_topics_returns_sorted_list(self):
        from tools.content_scorer import score_topics
        topics = [_make_topic("opinion_hot_takes"), _make_topic("lessons_from_work")]
        scored = score_topics(topics)
        scores = [t["scores"]["composite_score"] for t in scored]
        assert scores == sorted(scores, reverse=True)

    def test_topic_has_all_required_score_fields(self):
        from tools.content_scorer import score_topics
        topics = [_make_topic("career_and_transition")]
        scored = score_topics(topics)
        for field in ("audience_fit", "originality", "timeliness", "career_positioning",
                      "effort_estimate", "composite_score"):
            assert field in scored[0]["scores"]


# ── Duplicate detection tests ─────────────────────────────────────────────────

class TestTopicMemory:
    def test_duplicate_detection_high_overlap(self):
        from memory.topic_memory import is_duplicate
        # Title has 5+ non-stop-word matches with itself
        title = "SARIMAX Forecasting Hospital Bed Utilization Clinical Model"
        with patch("memory.topic_memory.get_all_titles", return_value=[title]):
            result = is_duplicate(title)
            assert result is True

    def test_duplicate_detection_no_overlap(self):
        from memory.topic_memory import is_duplicate
        with patch("memory.topic_memory.get_all_titles",
                   return_value=["Completely Unrelated Title About Cooking"]):
            result = is_duplicate("LLM RAG Pipelines for Clinical Documentation")
            assert result is False

    def test_category_distribution_counts(self):
        from memory.topic_memory import category_distribution
        mock_topics = [
            _make_topic("lessons_from_work"),
            _make_topic("lessons_from_work"),
            _make_topic("opinion_hot_takes"),
        ]
        with patch("memory.topic_memory._load", return_value=mock_topics):
            dist = category_distribution()
            assert dist["lessons_from_work"] == 2
            assert dist["opinion_hot_takes"] == 1


# ── Prompt construction tests ─────────────────────────────────────────────────

class TestTopicPrompts:
    def test_tutorials_prompt_contains_required_context(self):
        from prompts.topic_generation_prompts import build_practical_tutorials_prompt
        prompt = build_practical_tutorials_prompt()
        assert "3" in prompt  # "Generate exactly 3"
        assert "tutorial" in prompt.lower()

    def test_career_prompt_generates_2(self):
        from prompts.topic_generation_prompts import build_career_transition_prompt
        prompt = build_career_transition_prompt()
        assert "2" in prompt  # "Generate exactly 2"

    def test_opinion_prompt_generates_2(self):
        from prompts.topic_generation_prompts import build_opinion_hot_takes_prompt
        prompt = build_opinion_hot_takes_prompt()
        assert "2" in prompt

    def test_avoid_list_injected_in_prompt(self):
        from prompts.topic_generation_prompts import build_practical_tutorials_prompt
        already = ["My Old Topic", "Another Old Topic"]
        prompt = build_practical_tutorials_prompt(already_suggested=already)
        assert "My Old Topic" in prompt
