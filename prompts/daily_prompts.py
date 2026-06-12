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
Write a SHORT daily Substack post (200-350 words) about ONE recent AI or data science development.

THIS IS A NEWS POST, NOT A PERSONAL LEARNING POST.
The subject is what is happening in the AI and data science world right now. The author
is the reporter and commentator, NOT the subject. Do not turn this into "what I learned
this week" or "here is my journey". Stay focused on the news itself.

Pick ONE thing from the trend context below that a practitioner would actually care about:
a new model release, a framework or library update, an interesting paper, a deployment
story, a controversy, a benchmark result, a tool launch, a data engineering development,
an MLOps or infrastructure shift, or a healthcare AI story. Do not summarize multiple things.

Angle:
- Lead with the news. State what happened, plainly.
- Add a brief practitioner perspective on why it matters and who should pay attention.
- A short opinion is fine. A long personal story is not.
- Do NOT reference the author's job, employer, side projects, or learning journey
  unless the news is DIRECTLY about that exact topic.

Structure:
- Title (punchy, 6-10 words, about the news, not about the author)
- Opening line: the fact, plain, one sentence
- 2-3 short paragraphs: what happened, why it matters, what changes for practitioners
- Closing: a question that invites the reader to share THEIR take on the news

{_SHARED_VOICE_RULES}

Trend context to draw from:
{trend_context or "(No trend data available. Pick a recent real AI or data science development you can speak to credibly. Do not invent specifics.)"}

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


def build_ai_notes_prompt(news_context: str, count: int = 5) -> str:
    has_news = bool(news_context and news_context.strip()) and "No fresh trend data" not in news_context

    if has_news:
        ground_rule = (
            "Mix the notes across AI and data science. When a note touches a specific "
            "news item, reference a real one from the context below (model release, "
            "framework, paper, controversy, tool launch). Do not invent companies, "
            "model names, or events that are not in the context. For broader data "
            "science notes (stats, ML practice, tooling, career, data work) you may "
            "write from general practitioner knowledge, but never fabricate specific "
            "releases, version numbers, or dates. Stay focused on the TOPIC, not on a "
            "personal journey. The author is the commentator, not the subject."
        )
        context_block = f"Recent AI news to draw from (for the news-flavored notes):\n{news_context}"
    else:
        ground_rule = (
            "EVERGREEN MODE: No fresh news fetched this round. Write notes about what is "
            "happening across AI and data science right now at a topic level: ongoing "
            "debates and shifts the practitioner audience is actively discussing. "
            "AI angles: prompt engineering tradeoffs, RAG vs fine-tuning, agent "
            "reliability, evaluation pain, cost vs quality, open vs closed models, "
            "when not to use an LLM. Data science angles: feature engineering vs more "
            "data, when a simple model beats a complex one, dirty data realities, "
            "experiment design, dashboards nobody reads, SQL vs pandas, forecasting "
            "pitfalls, stakeholder communication, MLOps basics. "
            "Do NOT invent specific model releases, version numbers, dates, or company "
            "announcements. Stay focused on the field, not on the author."
        )
        context_block = "(No fresh news context. Use evergreen mode per the rule above.)"

    return f"""\
Generate {count} VERY SHORT Substack Notes (30-40 words EACH, hard cap) about AI AND
DATA SCIENCE. These are quick engagement posts, like tweets. Each one should hook the
reader and END WITH A SHARP QUESTION that invites a reply.

Aim for a MIX: not every note should be about a new AI model. Include data science
notes too (stats, ML practice, data work, tooling, the realities of the job). Variety
keeps the feed interesting.

{ground_rule}

Each note must:
- Be 30-40 words. Count them. No more.
- State the hook in ONE plain sentence (no hype).
- Add ONE sentence of practitioner reaction, curiosity, or opinion.
- End with a genuine question (not rhetorical, not "thoughts?").

{_SHARED_VOICE_RULES}

Format your output as a numbered list:

1. <note text 30-40 words>

2. <note text 30-40 words>

(etc.)

{context_block}

Return ONLY the numbered notes. No preamble, no headers, no explanations.
"""


def build_take_prompt(topic: str) -> str:
    return f"""\
Write a SHORT spicy opinion post (100-150 words) for a data scientist's Substack Notes.

Topic: {topic}

This is a hot take — the author's practitioner opinion. Be direct and specific.
No hedging, no "it depends", no balanced pros-and-cons. Take a side.

Structure:
- One opening sentence that states the opinion plainly.
- 2-3 sentences explaining the real-world reasoning behind it.
- End with a sharp question that invites genuine debate (not "Thoughts?" or "Do you agree?").

{_SHARED_VOICE_RULES}

Return ONLY the note text. No title, no markdown headers. Plain paragraphs only.
"""


def build_warstory_prompt(notes: str) -> str:
    return f"""\
Turn these rough notes into a short story-format Substack post (200-350 words) about a
real data science or engineering experience — a debugging session, a project that went
sideways, a lesson learned the hard way.

Raw notes from the author:
\"\"\"{notes}\"\"\"

Structure:
- Title: something specific and slightly self-deprecating (not "Lessons Learned")
- Opening: drop the reader into the moment, one sentence
- The middle: what happened, what you tried, what broke, the moment it clicked
- The ending: what you'd do differently, or just the honest takeaway
- Closing question: ask if others have hit the same thing

Keep the author's messy honesty from the notes. Don't clean it up too much.
If the notes are vague, write a best-effort version and flag with [QUESTION: ...] at top.

{_SHARED_VOICE_RULES}

Return ONLY the markdown post. No preamble.
"""


def build_contrast_prompt(topic: str) -> str:
    return f"""\
Write a "what they say vs what it actually is" Substack post (200-300 words) aimed at
data scientists and ML practitioners.

Topic: {topic}

Format: contrast the popular perception, tutorial version, or job-posting language with
what practitioners actually experience on the ground. Be specific and funny if it fits.

Structure:
- Title: something like "What [topic] looks like in interviews vs in practice" or similar
- 2-4 contrast pairs, each short and punchy (not a table — flowing prose or tight bullets)
- A closing line that's honest and non-generic

Do NOT:
- Make it a listicle of generic complaints
- Add fake balance ("but there are upsides too!")
- Be vague — every contrast should be something real

{_SHARED_VOICE_RULES}

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
