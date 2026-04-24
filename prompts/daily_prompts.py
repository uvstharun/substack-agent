"""Prompts for short daily Substack content (100-400 words per piece)."""
from __future__ import annotations


_SHARED_VOICE_RULES = """\
VOICE RULES (strict):
- First person. Short paragraphs (1-3 sentences each).
- Conversational, like a tweet thread or a text to a peer.
- One clear idea per piece. Do not cram multiple takes.
- No corporate filler: avoid "delve into", "leverage", "synergy", "game-changer", "revolutionize",
  "seamless", "robust", "unlock", "elevate", "harness", "empower", "cutting-edge", "paradigm".
- No throat-clearing intros ("In today's rapidly evolving AI landscape..."). Start with the point.
- End with a genuine question or call-to-engage that invites a reply.
- Output clean markdown, ready to paste into Substack Notes or a short post.

SOUND HUMAN, NOT AI (strict):
- NO em-dashes (—) or en-dashes (–). Ever. Use a period, comma, or parentheses instead.
- Hyphens only inside compound words ("open-source", "real-time"). Never as dramatic pauses.
- NO "not X, but Y" or "it's not just X, it's Y" constructions. Dead AI giveaway.
- Use contractions (I'm, don't, it's). Vary sentence length. Fragments are fine.
- Include real specifics, not smooth generalities. Small imperfections, honest asides, opinions.
- If a sentence sounds like LinkedIn thought-leadership, rewrite it.
"""


def build_ai_news_prompt(trend_context: str) -> str:
    return f"""\
Write a SHORT daily Substack post (200-350 words) commenting on a recent AI development.

Pick ONE thing from the trend context below that a practitioner would actually care about — \
a new model release, a framework update, an interesting paper, a deployment story, a controversy. \
Do not summarize multiple things.

Your angle should be a practitioner's take: what this means for people actually building with AI, \
not abstract industry commentary.

Structure:
- Title (punchy, 6-10 words)
- Opening line: state the fact plainly in one sentence
- 2-3 short paragraphs: why this matters, what practitioners should notice, your honest take
- Closing: a question or prompt that invites the reader to share their experience

{_SHARED_VOICE_RULES}

Trend context to draw from:
{trend_context or "(No trend data available — pick an evergreen recent AI development you can speak to credibly.)"}

Return ONLY the markdown post. No preamble, no JSON, no explanation.
"""


def build_job_tip_prompt(recent_tips: list[str] | None = None) -> str:
    avoid = ""
    if recent_tips:
        avoid = f"\n\nAvoid repeating these topics from recent posts:\n" + "\n".join(f"- {t}" for t in recent_tips)

    return f"""\
Write a SHORT daily Substack post (200-350 words) with one specific, actionable job search \
or career strategy tip for data scientists and aspiring AI/ML engineers.

The tip must be:
- SPECIFIC (not "network more" — something like "reach out to three data scientists who joined your target company in the last 90 days with this exact message template")
- GROUNDED in reality of the current AI/ML job market (tight, competitive, LLM skills in demand)
- ACTIONABLE today (reader can do it this week)
- Based on the practitioner's perspective — someone ~2 years in, navigating this themselves

Good angles: resume framing, portfolio projects that actually impress, interview prep tactics, \
LinkedIn strategy, how to show LLM skills without formal experience, negotiating offers, \
cold outreach templates, how to get past ATS, picking a niche, building in public.

Structure:
- Title (direct, benefit-driven)
- Opening: the tip in one plain sentence
- 2-3 short paragraphs: how to do it, why it works, a concrete example
- Closing: a question that invites reader to share their situation

{_SHARED_VOICE_RULES}
{avoid}

Return ONLY the markdown post. No preamble.
"""


def build_daily_learning_prompt(raw_learning: str, recent_learnings: list[str] | None = None) -> str:
    recent_note = ""
    if recent_learnings:
        recent_note = "\n\nRecent learning posts (for context, don't repeat):\n" + "\n".join(
            f"- {r}" for r in recent_learnings[-5:]
        )

    return f"""\
The author just learned something and wrote this rough note:

\"\"\"{raw_learning}\"\"\"

Turn this into a polished short Substack post (150-300 words) in the "today I learned" format. \
The post should feel authentic — like the author is genuinely processing what they learned, \
not performing expertise.

Structure:
- Title: "TIL: <specific thing>" OR a curiosity-driven hook, 6-10 words
- Opening: the learning in one clean sentence
- 2-3 short paragraphs: context (why you were looking into this), what you learned, why it \
  surprised you OR what it unlocks
- Closing: a genuine question — either asking others if they've hit the same thing, or \
  what they'd want to learn next

Keep the author's voice. Don't over-polish. Keep the honesty of the original note.
If the note is vague, ASK A CLARIFYING QUESTION at the top of your output as \
`[QUESTION FOR AUTHOR: ...]` and still write a best-effort draft.

{_SHARED_VOICE_RULES}
{recent_note}

Return ONLY the markdown post. No preamble.
"""
