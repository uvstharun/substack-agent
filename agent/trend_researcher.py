"""Fetches and summarizes trend data before topic generation."""
from __future__ import annotations

from loguru import logger
from tools.trend_analyzer import fetch_trend_report, fetch_news_snippets
from agent import orchestrator


_SUMMARIZE_PROMPT = """\
Below are raw snippets from recent web searches about AI, LLMs, data science, agents,
and ML tooling (the generalist AI/DS landscape).

HARD RULE: Only include items from the LAST 2 WEEKS. Skip anything older than 14 days
even if it appears in the snippets.

Your task: summarize the most important and actionable trends in 400-600 words.
Focus on:
1. Major model releases, framework launches, tooling updates in the last few weeks
2. What practitioners are debating or struggling with right now
3. Career and skills trends for data scientists moving into AI/ML engineering
4. Backlash, failures, or cautionary stories worth noting
5. Emerging use cases a practical AI/DS writer could cover

Raw snippets:
{snippets}

Write the summary in plain prose (no bullet lists) as if briefing a smart colleague
before a content planning session.
"""


_NEWS_TOPICS_PROMPT = """\
You are helping a generalist AI/Data Science Substack writer find post ideas based
on fresh AI news from the LAST 2 WEEKS ONLY. Below are real news items scraped from
the web just now.

HARD RULE: Skip anything older than 2 weeks. If a snippet references a date or event
older than 14 days from today, DO NOT include it. Prefer items that explicitly mention
"this week", "yesterday", "today", or a date within the last 14 days.

Your job: pick the 6-8 MOST POST-WORTHY items and for each give a sharp, specific
post angle the author could take. Skip generic "AI will change everything" items.
Prefer concrete news: model releases, tool launches, research papers, notable
failures or controversies, benchmark results, acquisitions, policy moves.

For each idea, output in this exact format:

<NUMBER>. <SHORT TITLE>
What happened: <one sentence, specific>
Post angle: <one or two sentences. The practitioner's take the author could write.>
Format: <news_reaction | quick_explainer | hot_take | lessons_learned | tutorial_hook>
Source: <url if available, otherwise "-">

Rules:
- Use real items from the snippets, do not invent.
- Do NOT use em-dashes or en-dashes. Hyphens only inside compound words.
- No filler phrases ("in today's rapidly evolving landscape" etc).
- Keep each angle under 40 words, specific and opinionated.

News items:
{items}

Return only the numbered list. No preamble.
"""


def get_trend_summary() -> str:
    """Run trend research and return a prose summary for use in topic generation."""
    logger.info("Fetching trend data...")
    report = fetch_trend_report()
    snippets = report.get("summary", "")

    if not snippets.strip():
        logger.warning("No trend data fetched — using fallback message")
        return "No fresh trend data available. Rely on evergreen angles and the author's current projects."

    prompt = _SUMMARIZE_PROMPT.format(snippets=snippets[:8000])
    summary = orchestrator.call(prompt, max_tokens=800, temperature=0.4)
    logger.info("Trend summary generated")
    return summary


def get_ai_news_topics() -> dict:
    """
    Fetch fresh AI news from the web and return a list of post-worthy topic ideas
    (not a written post). Returns {"text": str, "items": list[dict]}.
    """
    logger.info("Fetching fresh AI news for topic ideation...")
    items = fetch_news_snippets(max_items=30)

    if not items:
        return {
            "text": "No fresh AI news found right now. Try again in a bit, or run /topics for evergreen ideas.",
            "items": [],
        }

    # Build a compact context of the items for Claude
    lines: list[str] = []
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it['title']}\n   {it['snippet']}\n   URL: {it.get('url','-')}")
    items_text = "\n\n".join(lines)[:9000]

    prompt = _NEWS_TOPICS_PROMPT.format(items=items_text)
    ideas = orchestrator.call(prompt, max_tokens=1500, temperature=0.5)
    logger.info("AI news topic ideas generated")
    return {"text": ideas, "items": items}
