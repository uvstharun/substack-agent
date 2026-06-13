"""Post-process generated content to remove AI writing patterns before delivery."""
from __future__ import annotations

from loguru import logger
from agent import orchestrator

_HUMANIZER_PROMPT = """\
You are a writing editor. Clean up the text below so it sounds like a real human data scientist wrote it, not a language model.

REMOVE these patterns:
- AI vocabulary: "delve", "leverage", "pivotal", "underscore", "highlight" (as verb), "tapestry", "landscape" (abstract noun), "testament", "crucial", "vibrant", "robust", "showcase", "align with", "foster", "garner", "elevate", "empower", "cutting-edge", "seamless", "paradigm", "revolutionize", "transformative"
- Em dashes (—) and en dashes (–). Replace with a period, comma, or parentheses instead.
- "Not X, but Y" / "It's not just X, it's Y" constructions.
- Forced rule-of-three groupings when only two examples are needed.
- Vague attributions: "experts say", "industry observers note", "many believe", "some argue".
- Inflated significance: "marks a pivotal moment", "reflects broader trends", "sets the stage for", "represents a shift".
- Filler phrases: "In order to", "It is important to note that", "Due to the fact that", "At this point in time", "With that in mind".
- Generic positive endings: "exciting times ahead", "the future looks bright", "only time will tell", "in conclusion".
- Excessive bold decoration (bold is fine for headers, not for random emphasis mid-sentence).
- Chatbot artifacts: "Great question!", "Certainly!", "I hope this helps", "Let me know if".
- "serves as" / "stands as" — replace with "is".

KEEP:
- Contractions (I'm, don't, it's, we're, hasn't).
- Natural sentence length variation. Short punchy sentences are good. Longer ones are fine too.
- Strong opinions — don't sand them down into neutral reporting.
- First person voice.
- Specific details, numbers, tool names, real examples.
- All markdown structure: headers, bullets, code blocks, bold for section titles.
- The closing question — but make it feel genuine, not "Thoughts?" or "What do you think?".

Return ONLY the edited text. No preamble, no "Here is the revised version:", no explanation.

Text to edit:
{text}
"""


def humanize(text: str) -> str:
    """Run generated content through the humanizer before delivery to Telegram."""
    if not text or len(text.strip()) < 50:
        return text
    try:
        prompt = _HUMANIZER_PROMPT.format(text=text[:6000])
        result = orchestrator.call(prompt, max_tokens=2000, temperature=0.3)
        logger.info("Humanizer pass complete")
        return result
    except Exception as e:
        logger.warning(f"Humanizer failed, returning original: {e}")
        return text
