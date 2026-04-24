STYLE_FEEDBACK_PROCESSING_PROMPT = """\
The author has left feedback on a generated outline or draft. Extract actionable style preferences \
from this feedback and return a JSON object with updated preferences.

Return this structure:
{
  "tone_adjustment": null | "more_casual" | "more_formal" | "more_technical" | "less_technical",
  "length_adjustment": null | "shorter" | "longer",
  "structure_notes": "any specific feedback about section structure or organization",
  "voice_notes": "feedback about the writing voice or persona",
  "content_type_preferences": {
    "wants_more": ["e.g. personal stories", "specific examples"],
    "wants_less": ["e.g. definitions", "caveats"]
  },
  "hook_preference": null | "personal_story" | "surprising_stat" | "provocative_question",
  "raw_feedback_summary": "one sentence summary of what the author said"
}
"""


def build_style_incorporation_prompt(current_preferences: dict) -> str:
    return f"""\
The author has accumulated the following writing style preferences from past feedback. \
Incorporate all of these into your generation:

Tone: {current_preferences.get('tone', 'conversational')}
Preferred length: {current_preferences.get('length', 'medium')}
Technical depth: {current_preferences.get('technical_depth', 'balanced')}
Preferred hook style: {current_preferences.get('preferred_hook', 'personal_story')}
Wants more of: {', '.join(current_preferences.get('wants_more', ['personal stories', 'concrete examples']))}
Wants less of: {', '.join(current_preferences.get('wants_less', ['generic AI hype', 'vague claims']))}
Phrases to avoid: {', '.join(current_preferences.get('phrases_to_avoid', []))}
Additional notes: {current_preferences.get('free_form_notes', 'none')}

Honor these preferences throughout your generation.
"""
