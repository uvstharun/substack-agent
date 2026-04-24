"""Scores topics on audience fit, originality, timeliness, and career positioning."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TopicScore:
    audience_fit: float
    originality: float
    timeliness: float
    career_positioning: float
    effort_estimate: str  # low | medium | high
    composite_score: float

    def as_dict(self) -> dict:
        return {
            "audience_fit": self.audience_fit,
            "originality": self.originality,
            "timeliness": self.timeliness,
            "career_positioning": self.career_positioning,
            "effort_estimate": self.effort_estimate,
            "composite_score": self.composite_score,
        }


_HEALTHCARE_SIGNALS = [
    "hospital", "clinical", "healthcare", "health system", "patient",
    "radiology", "inpatient", "sdoh", "readmission", "ehr", "emr",
    "bed utilization", "care coordination", "public health",
]

_AI_SIGNALS = [
    "ai", "machine learning", "llm", "rag", "agent", "nlp", "forecast",
    "anomaly detection", "time series", "sarimax", "neural", "model",
]

_CAREER_SIGNALS = [
    "career", "transition", "portfolio", "skill", "job", "hire", "interview",
    "level up", "data scientist", "engineer",
]


def _signal_score(text: str, signals: list[str]) -> float:
    text_lower = text.lower()
    hits = sum(1 for s in signals if s in text_lower)
    return min(10.0, 4.0 + hits * 1.5)


def score_topic(topic: dict) -> TopicScore:
    title = topic.get("title", "")
    why_now = topic.get("why_now", "")
    category = topic.get("category", "")
    combined = f"{title} {why_now}"

    audience_fit = _signal_score(combined, _HEALTHCARE_SIGNALS + _AI_SIGNALS)
    originality = 8.5 if category == "lessons_from_work" else (
        7.5 if category == "opinion_hot_takes" else 6.5
    )
    timeliness = topic.get("virality_score", 6) * 1.0  # proxy from AI-generated field
    career_positioning = _signal_score(combined, _CAREER_SIGNALS + _AI_SIGNALS)
    career_positioning = max(career_positioning, topic.get("career_positioning_score", 6) * 1.0)

    # Effort heuristic by category
    effort_map = {
        "practical_tutorials": "high",
        "career_and_transition": "medium",
        "tools_and_frameworks": "medium",
        "opinion_hot_takes": "low",
        "project_deep_dives": "high",
    }
    effort = effort_map.get(category, "medium")

    composite = round(
        (audience_fit + originality + timeliness + career_positioning) / 4, 1
    )

    return TopicScore(
        audience_fit=round(audience_fit, 1),
        originality=round(originality, 1),
        timeliness=round(timeliness, 1),
        career_positioning=round(career_positioning, 1),
        effort_estimate=effort,
        composite_score=composite,
    )


def score_topics(topics: list[dict]) -> list[dict]:
    """Add scores to a list of topic dicts and sort by composite score descending."""
    scored = []
    for t in topics:
        s = score_topic(t)
        scored.append({**t, "scores": s.as_dict()})
    scored.sort(key=lambda x: x["scores"]["composite_score"], reverse=True)
    return scored
