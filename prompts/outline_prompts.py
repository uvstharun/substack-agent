OUTLINE_SCHEMA = """\
Return a single JSON object with this structure:
{
  "topic_title": "original approved title",
  "headline_options": [
    {"angle": "curiosity-driven", "title": "...", "subtitle_options": ["...", "..."]},
    {"angle": "benefit-driven",   "title": "...", "subtitle_options": ["...", "..."]},
    {"angle": "story-driven",     "title": "...", "subtitle_options": ["...", "..."]}
  ],
  "hook_options": [
    {"type": "personal_story", "text": "full opening paragraph (~100 words)"},
    {"type": "surprising_stat", "text": "full opening paragraph (~100 words)"},
    {"type": "provocative_question", "text": "full opening paragraph (~100 words)"}
  ],
  "sections": [
    {
      "title": "section title",
      "bullet_points": ["point 1", "point 2", "point 3"],
      "personal_anecdotes_to_include": ["prompt for specific story or detail from author's work"],
      "estimated_word_count": <integer>
    }
  ],
  "key_arguments": ["argument 1", "argument 2"],
  "data_points_to_research": ["specific stat or source to look up"],
  "analogies_and_metaphors": ["analogy 1", "analogy 2"],
  "call_to_action_options": ["cta 1", "cta 2", "cta 3"],
  "total_estimated_word_count": <integer>,
  "estimated_read_time_minutes": <integer>
}
"""


def build_outline_prompt(topic: dict, style_preferences: dict | None = None) -> str:
    style_note = ""
    if style_preferences:
        tone = style_preferences.get("tone", "conversational")
        length = style_preferences.get("length", "medium")
        technical_depth = style_preferences.get("technical_depth", "balanced")
        notes = style_preferences.get("free_form_notes", "")
        style_note = f"""
Style preferences to incorporate:
- Tone: {tone}
- Length preference: {length} (short=800w, medium=1400w, long=2200w)
- Technical depth: {technical_depth}
- Additional notes: {notes}
"""

    return f"""\
Generate a complete, publication-ready outline for the following Substack post topic.

Topic: {topic.get('title')}
Category: {topic.get('category')}
Recommended format: {topic.get('recommended_format')}
Target reader: {topic.get('target_reader')}
SEO keywords to weave in naturally: {', '.join(topic.get('seo_keywords', []))}

The author's background to draw from when prompting personal anecdotes:
- Nearly 2 years as Data Scientist at a large public health system
- Projects: inpatient bed utilization forecasting (SARIMAX), radiology KPI dashboard (Vertica/Tableau),
  SDOH extraction from clinical notes (NLP), readmission prevention AI agents
- Skills: Python, SQL/Vertica, Azure Synapse, time series, anomaly detection, LLMs/RAG

For each section, include specific prompts asking the author to fill in real details from their work. \
For example: "INSERT: What was the actual error rate you observed in your SARIMAX model before the fix?"

{style_note}

{OUTLINE_SCHEMA}
"""
