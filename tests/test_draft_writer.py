"""Tests for outline and draft generation logic."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_topic(title: str = "How I Built a SARIMAX Model for Bed Utilization") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "category": "lessons_from_work",
        "recommended_format": "personal story",
        "target_reader": "Healthcare data scientists",
        "seo_keywords": ["healthcare forecasting", "SARIMAX", "time series"],
        "why_now": "Time series forecasting in healthcare is underexplored.",
        "virality_score": 7,
        "career_positioning_score": 9,
        "status": "approved",
    }


def _make_outline() -> dict:
    return {
        "topic_title": "How I Built a SARIMAX Model for Bed Utilization",
        "topic_id": str(uuid.uuid4()),
        "headline_options": [
            {
                "angle": "curiosity-driven",
                "title": "What Nobody Tells You About Forecasting in Healthcare",
                "subtitle_options": ["The lessons from 18 months of trial and error"],
            },
            {
                "angle": "benefit-driven",
                "title": "How to Build a Hospital Bed Utilization Forecast",
                "subtitle_options": ["A practical guide from someone who did it"],
            },
            {
                "angle": "story-driven",
                "title": "The Day My SARIMAX Model Was Wrong in the Best Possible Way",
                "subtitle_options": ["And what it taught me about healthcare forecasting"],
            },
        ],
        "hook_options": [
            {
                "type": "personal_story",
                "text": "It was a Tuesday morning when my model predicted 140% bed occupancy...",
            },
            {
                "type": "surprising_stat",
                "text": "Most hospitals don't forecast bed utilization more than 48 hours out...",
            },
            {
                "type": "provocative_question",
                "text": "What would you do if your forecast was off by 30 beds on a Monday morning?",
            },
        ],
        "sections": [
            {
                "title": "The Problem Nobody Could Solve",
                "bullet_points": ["Why bed utilization forecasting is hard", "What existing solutions miss"],
                "personal_anecdotes_to_include": ["Describe the first time you saw the bed management team struggle"],
                "estimated_word_count": 300,
            },
            {
                "title": "Building the Model",
                "bullet_points": ["Data sources", "SARIMAX setup", "Feature engineering"],
                "personal_anecdotes_to_include": ["INSERT: the specific challenge you faced with seasonality"],
                "estimated_word_count": 500,
            },
        ],
        "key_arguments": ["Clinical context matters more than model sophistication", "Simple beats complex when data is limited"],
        "data_points_to_research": ["Average hospital bed occupancy rates"],
        "analogies_and_metaphors": ["Forecasting beds is like forecasting weather in a desert"],
        "call_to_action_options": ["What forecasting challenges are you working on?"],
        "total_estimated_word_count": 1400,
        "estimated_read_time_minutes": 7,
    }


# ── Outline prompt tests ──────────────────────────────────────────────────────

class TestOutlinePrompts:
    def test_outline_prompt_includes_topic_title(self):
        from prompts.outline_prompts import build_outline_prompt
        topic = _make_topic()
        prompt = build_outline_prompt(topic)
        assert topic["title"] in prompt

    def test_outline_prompt_includes_seo_keywords(self):
        from prompts.outline_prompts import build_outline_prompt
        topic = _make_topic()
        prompt = build_outline_prompt(topic)
        assert "SARIMAX" in prompt

    def test_outline_prompt_includes_style_prefs(self):
        from prompts.outline_prompts import build_outline_prompt
        topic = _make_topic()
        prefs = {"tone": "casual", "length": "short", "technical_depth": "accessible"}
        prompt = build_outline_prompt(topic, prefs)
        assert "casual" in prompt
        assert "short" in prompt


# ── Draft prompt tests ────────────────────────────────────────────────────────

class TestDraftPrompts:
    def test_draft_prompt_includes_topic_title(self):
        from prompts.draft_prompts import build_draft_prompt
        topic = _make_topic()
        outline = _make_outline()
        prompt = build_draft_prompt(topic, outline)
        assert topic["title"] in prompt

    def test_draft_prompt_includes_first_person_instruction(self):
        from prompts.draft_prompts import build_draft_prompt
        topic = _make_topic()
        outline = _make_outline()
        prompt = build_draft_prompt(topic, outline)
        assert "first person" in prompt.lower()

    def test_draft_prompt_includes_hook(self):
        from prompts.draft_prompts import build_draft_prompt
        topic = _make_topic()
        outline = _make_outline()
        prompt = build_draft_prompt(topic, outline)
        assert "personal_story" in prompt or "Tuesday" in prompt  # hook text injected


# ── Draft storage tests ───────────────────────────────────────────────────────

class TestDraftStorage:
    def test_draft_saved_to_disk(self, tmp_path):
        from agent import draft_writer
        topic = _make_topic()
        fake_content = "# My Draft\n\nThis is a test draft."

        mock_cfg = MagicMock()
        mock_cfg.drafts_dir = tmp_path
        with patch("agent.draft_writer.cfg", mock_cfg):
            with patch("agent.draft_writer.orchestrator.call", return_value=fake_content):
                with patch("agent.draft_writer.topic_memory.update_topic_status"):
                    with patch("agent.draft_writer.style_memory.get_preferences", return_value={}):
                        result = draft_writer.write_draft(topic, _make_outline())

        saved_files = list(tmp_path.glob("*.md"))
        assert len(saved_files) == 1
        assert "My Draft" in saved_files[0].read_text()

    def test_load_draft_returns_content(self, tmp_path):
        from agent import draft_writer
        test_file = tmp_path / "2025-01-01_test-post.md"
        test_file.write_text("# Test Post\n\nContent here.")

        mock_cfg = MagicMock()
        mock_cfg.drafts_dir = tmp_path
        with patch("agent.draft_writer.cfg", mock_cfg):
            content = draft_writer.load_draft("2025-01-01_test-post.md")

        assert content is not None
        assert "Content here" in content

    def test_get_saved_drafts_returns_list(self, tmp_path):
        from agent import draft_writer
        (tmp_path / "2025-01-01_test.md").write_text("# Post One\n\nWords here.")
        (tmp_path / "2025-01-02_test2.md").write_text("# Post Two\n\nMore words.")

        mock_cfg = MagicMock()
        mock_cfg.drafts_dir = tmp_path
        with patch("agent.draft_writer.cfg", mock_cfg):
            drafts = draft_writer.get_saved_drafts()

        assert len(drafts) == 2
        assert all("filename" in d and "word_count" in d for d in drafts)

    def test_draft_content_is_non_empty(self, tmp_path):
        from agent import draft_writer
        topic = _make_topic()
        fake_content = "# Real Draft\n\n" + "Word " * 500

        mock_cfg = MagicMock()
        mock_cfg.drafts_dir = tmp_path
        with patch("agent.draft_writer.cfg", mock_cfg):
            with patch("agent.draft_writer.orchestrator.call", return_value=fake_content):
                with patch("agent.draft_writer.topic_memory.update_topic_status"):
                    with patch("agent.draft_writer.style_memory.get_preferences", return_value={}):
                        result = draft_writer.write_draft(topic, _make_outline())

        assert len(result) > 100
