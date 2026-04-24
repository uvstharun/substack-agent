from typing import Optional

TOPIC_CATEGORY_DESCRIPTIONS = {
    "practical_tutorials": "Practical AI/ML Tutorials",
    "career_and_transition": "Career and Transition Content",
    "tools_and_frameworks": "AI Tools and Frameworks",
    "opinion_hot_takes": "Opinion and Hot Takes",
    "project_deep_dives": "Project Deep-Dives and Case Studies",
}

TOPIC_OUTPUT_SCHEMA = """\
Return a JSON array. Each topic object must have these exact keys:
{
  "title": "compelling, specific title",
  "why_now": "one paragraph explaining why this is worth writing right now",
  "target_reader": "specific description of who will resonate most",
  "estimated_read_time_minutes": <integer>,
  "virality_score": <1-10>,
  "virality_reasoning": "brief explanation",
  "career_positioning_score": <1-10>,
  "career_positioning_reasoning": "brief explanation",
  "suggested_series": "name of Substack section or series this belongs to",
  "seo_keywords": ["keyword1", "keyword2", "keyword3"],
  "similar_posts_to_differentiate_from": ["example title 1", "example title 2"],
  "recommended_format": "personal story | how-to guide | opinion piece | technical explainer | case study",
  "category": "practical_tutorials | career_and_transition | tools_and_frameworks | opinion_hot_takes | project_deep_dives"
}
"""


def build_practical_tutorials_prompt(trend_context: str = "", already_suggested: list[str] | None = None) -> str:
    avoid = f"\n\nAVOID these topics already suggested: {already_suggested}" if already_suggested else ""
    return f"""\
Generate exactly 3 Substack topic suggestions in the category: "Practical AI/ML Tutorials."

These are hands-on, step-by-step posts where the author walks readers through building or doing \
something real with AI or data science. The author's unique value is being a practitioner who has \
actually built these things — not just summarizing documentation.

Good angles: building a RAG pipeline from scratch, fine-tuning a small LLM, setting up an AI agent \
with tool use, time series forecasting with Python, NLP text extraction pipelines, anomaly detection \
systems, MLOps workflows, prompt engineering techniques that actually work, evaluating LLM outputs.

Every tutorial should teach something concrete the reader can replicate in an afternoon.

Current trend context (weave in where relevant):
{trend_context or "No trend data — rely on evergreen practical topics."}
{avoid}

{TOPIC_OUTPUT_SCHEMA}
"""


def build_career_transition_prompt(trend_context: str = "", already_suggested: list[str] | None = None) -> str:
    avoid = f"\n\nAVOID these topics already suggested: {already_suggested}" if already_suggested else ""
    return f"""\
Generate exactly 2 Substack topic suggestions in the category: "Career and Transition Content."

These topics speak to data scientists and developers who want to break into AI/ML, level up from \
traditional analytics to ML engineering, or navigate the rapidly changing AI job market.

The author has a specific vantage point: nearly 2 years in, actively transitioning from traditional \
data science work (SQL, dashboards, forecasting) to AI/agent development. This journey — learning \
LLMs while maintaining a day job — is exactly what many readers are living.

Topics should address: building an AI portfolio, how to learn LLMs practically, what hiring managers \
want now vs two years ago, the skills gap between data science and AI engineering, side project \
strategies, how to get your first ML role, or honest reflections on the transition journey.

Current trend context:
{trend_context or "No trend data — rely on evergreen career angles."}
{avoid}

{TOPIC_OUTPUT_SCHEMA}
"""


def build_tools_frameworks_prompt(trend_context: str = "", already_suggested: list[str] | None = None) -> str:
    avoid = f"\n\nAVOID these topics already suggested: {already_suggested}" if already_suggested else ""
    return f"""\
Generate exactly 2 Substack topic suggestions in the category: "AI Tools and Frameworks."

These posts review, compare, or deeply explore specific AI tools, libraries, and frameworks from \
a practitioner's perspective. The author has hands-on experience with: LangChain, LlamaIndex, \
Claude API, OpenAI API, Hugging Face, Pandas, scikit-learn, Azure ML, Streamlit, and more.

The key differentiator: the author shares honest opinions based on actually building with these tools — \
not just reading the docs. What breaks in production, what the tutorials don't tell you, which tool \
won a real comparison, what the hype misses.

Topics: framework comparisons (LangChain vs LlamaIndex, different vector DBs), deep dives into \
specific libraries, "what I learned after X weeks with Y tool", or reviews of new AI releases.

Current trend context (prioritize newly released tools or frameworks):
{trend_context or "No trend data — focus on tools the author has direct experience with."}
{avoid}

{TOPIC_OUTPUT_SCHEMA}
"""


def build_opinion_hot_takes_prompt(trend_context: str = "", already_suggested: list[str] | None = None) -> str:
    avoid = f"\n\nAVOID these topics already suggested: {already_suggested}" if already_suggested else ""
    return f"""\
Generate exactly 2 Substack topic suggestions in the category: "Opinion and Hot Takes."

These are contrarian, provocative, or strongly held opinions about AI, data science, or the tech \
industry that will spark genuine conversation. The author has seen real gaps between AI hype and \
on-the-ground reality as a practitioner building with these tools every day.

Good angles: why most AI tutorials are misleading, unpopular truths about working as a data scientist, \
what the AI hype cycle means for practitioners, why a specific popular framework is overrated, \
honest takes on AI job market claims, what "prompt engineering" actually is vs how it's sold, \
the gap between AI demos and production reality.

Takes must be specific and defensible — not vague complaints but argued positions with real evidence.

Current trend context:
{trend_context or "No trend data — draw from the author's direct practitioner experience."}
{avoid}

{TOPIC_OUTPUT_SCHEMA}
"""


def build_project_deep_dives_prompt(trend_context: str = "", already_suggested: list[str] | None = None) -> str:
    avoid = f"\n\nAVOID these topics already suggested: {already_suggested}" if already_suggested else ""
    return f"""\
Generate exactly 2 Substack topic suggestions in the category: "Project Deep-Dives and Case Studies."

These posts walk through a real project end-to-end: what was the problem, what was built, what went \
wrong, what worked, and what the author learned. The author's real projects include: time series \
forecasting models, NLP information extraction pipelines, AI agents with tool use, RAG pipelines, \
anomaly detection systems, and operational dashboards.

These posts should feel like insider post-mortems — the kind of honest project retrospective that \
practitioners actually want to read but rarely publish.

Topics: building and shipping a complete ML project, lessons from a failed experiment, \
architecture decisions and tradeoffs, debugging stories, performance optimization journeys, \
or anything that gives readers a detailed behind-the-scenes view of real ML work.

Current trend context:
{trend_context or "No trend data — draw from the author's real project experience."}
{avoid}

{TOPIC_OUTPUT_SCHEMA}
"""


TOPIC_SCORING_PROMPT = """\
You are scoring a set of Substack topic suggestions for a generalist AI and Data Science writer. \
Score each topic on:

1. audience_fit (1-10): How precisely does this match the target audience?
2. originality (1-10): Can this author bring a unique angle nobody else has?
3. timeliness (1-10): Is this relevant right now or evergreen and durable?
4. career_positioning (1-10): Does writing this build the author's brand as a practical AI practitioner?
5. effort_estimate: "low" | "medium" | "high" — realistic writing effort required

Return a JSON array with the same topics, each augmented with a "scores" object containing these fields \
and a "composite_score" (average of the four numeric scores, rounded to 1 decimal).
"""
