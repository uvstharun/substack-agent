"""Prompt for the research-grounded Substack post writer."""
from __future__ import annotations


_VOICE_RULES = """\
VOICE RULES (strict):
- First person where natural. Conversational. Short paragraphs (2-5 sentences).
- NO em-dashes (—) or en-dashes (–). Ever. Use periods, commas, or parentheses.
- Hyphens only inside compound words ("open-source", "real-time"). Never as pauses.
- NO "not X, but Y" or "it's not just X, it's Y" constructions.
- AVOID: delve, leverage, seamless, robust, navigate the landscape, game-changer,
  revolutionize, unlock, elevate, pivotal, tapestry, underscore, crucial, myriad,
  plethora, intricate, realm, harness, empower, dive into, journey, foster,
  streamline, cutting-edge, paradigm, ecosystem (when metaphorical).
- NO throat-clearing intros ("In today's rapidly evolving AI landscape...").
- Use contractions naturally. Vary sentence length. Fragments OK.
- Real specifics over smooth generalities.
- If a sentence sounds like LinkedIn thought-leadership, rewrite it.
"""


def build_research_post_prompt(topic: str, sources_text: str, limited_sources: bool = False) -> str:
    """Build the prompt for a research-grounded Substack post.

    Returns a prompt that asks Claude to:
    - Pick the best voice for the topic itself
    - Ground every claim in the sources provided
    - Add a "Sources I used" list at the bottom
    - Add a top note with word count (and limited-sources warning if applicable)
    """
    limited_note = (
        "\nIMPORTANT: The web search returned only a small number of sources for this "
        "topic. Acknowledge this with a brief honest note at the top of the post (under "
        "the word-count note) so the reader knows the post is exploratory, not definitive. "
        "Do NOT invent facts to compensate.\n"
        if limited_sources else ""
    )

    return f"""\
You are writing a research-grounded Substack post about a topic the author chose.
Topic: "{topic}"

═══════════════════════════════════════════
SOURCES (real web search results — use ONLY these for any factual claim)
═══════════════════════════════════════════

{sources_text}

═══════════════════════════════════════════
HARD RULES
═══════════════════════════════════════════

1. GROUND EVERY FACTUAL CLAIM in the sources above. Do NOT invent statistics, dates,
   model versions, company quotes, study results, or product features that are not
   present in the sources. If you are not sure, leave it out.

2. Prioritize the NEWEST sources. If the snippets reference a date, prefer recent items.
   Older background context is fine for foundation, but the angle should feel current.

3. Pick the right VOICE for this topic:
   - If the topic is technical and the audience benefits from a neutral explainer,
     write in a clear journalistic voice with a small amount of practitioner perspective.
   - If the topic is opinion-shaped or experiential, write in first person, learning-in-
     public, honest about what the author does and does not know.
   - You decide. Pick the voice that serves the topic.

4. The author is Vishnu Sai, a Data Scientist with about 2 years of experience working
   in healthcare data at LA DHS, currently learning AI engineering. Do NOT invent
   credentials beyond this. Do NOT pretend to be a senior expert.

5. Length target: 700-1000 words for the BODY (not counting title, top note, or sources).

═══════════════════════════════════════════
STRUCTURE
═══════════════════════════════════════════

# <Title — clear, specific, 6-12 words. Not clickbait, not generic>

> _Word count: <approximate count of the body, not counting this note or sources>_
{limited_note}
<Subtitle / dek — one sentence that hooks the reader with the angle, NOT a summary.>

<Body, 700-1000 words, organized into 3-5 sections with H2 (##) subheadings if helpful.
Use short paragraphs. Use real specifics from the sources. The author can offer
opinions, but factual claims must trace back to the sources list.>

## Sources I used

1. <Source title> — <url>
2. <Source title> — <url>
...

═══════════════════════════════════════════
{_VOICE_RULES}
═══════════════════════════════════════════

Return ONLY the markdown post. No preamble, no explanation, no JSON.
"""
