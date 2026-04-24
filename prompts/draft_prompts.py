def build_draft_prompt(topic: dict, outline: dict, style_preferences: dict | None = None) -> str:
    style_note = ""
    if style_preferences:
        tone = style_preferences.get("tone", "conversational")
        length = style_preferences.get("length", "medium")
        depth = style_preferences.get("technical_depth", "balanced")
        avoid = style_preferences.get("phrases_to_avoid", [])
        style_note = f"""
Writing style instructions:
- Tone: {tone} (conversational = write like explaining to a smart colleague over coffee)
- Target length: {length} (short=~800 words, medium=~1400 words, long=~2200 words)
- Technical depth: {depth}
- Phrases to avoid: {', '.join(avoid) if avoid else 'none specified'}
"""

    selected_hook = outline.get("hook_options", [{}])[0].get("text", "")
    sections = outline.get("sections", [])

    section_instructions = "\n".join(
        f"Section: {s.get('title', '')}\nCover: {'; '.join(s.get('bullet_points', []))}\n"
        f"Prompt for personal detail: {'; '.join(s.get('personal_anecdotes_to_include', []))}\n"
        for s in sections
    )

    return f"""\
Write a complete first draft of a Substack post for a Data Scientist at a large public health system.

TOPIC: {topic.get('title')}
FORMAT: {topic.get('recommended_format')}
TARGET READER: {topic.get('target_reader')}

APPROVED OPENING HOOK (use this or closely adapt it):
{selected_hook}

OUTLINE TO FOLLOW:
{section_instructions}

KEY ARGUMENTS TO MAKE:
{chr(10).join('- ' + a for a in outline.get('key_arguments', []))}

CALL TO ACTION (choose the most natural one):
{chr(10).join('- ' + c for c in outline.get('call_to_action_options', []))}

{style_note}

CRITICAL VOICE REQUIREMENTS:
1. Write entirely in first person. This is a personal essay by a healthcare data scientist.
2. Include specific technical details that only a practitioner with this background would know.
3. Where real personal details are needed that the AI cannot know, insert a clear placeholder like:
   [INSERT: describe the specific moment when X happened in your project]
   [ADD: the actual number/metric from your Vertica query]
   [EXPAND: your personal reaction when you discovered Y]
4. Use short paragraphs — 3 sentences maximum for readability on Substack.
5. Vary sentence length. Short punchy sentences after complex ones.
6. Avoid: buzzwords, passive voice, hedging everything ("it could be argued that"), corporate speak.
7. Include at least 2-3 moments of genuine honesty — what went wrong, what you don't know, what surprised you.
8. The opening 3 sentences must hook the reader without being clickbait.

Return the full draft in clean markdown, ready to paste into Substack. \
Include the post title as a level-1 heading at the top.
"""


SECTION_EXPANSION_PROMPT = """\
Expand the following outline section into prose for a Substack post written by a healthcare data scientist.

Keep the voice: first-person, conversational, honest, technically grounded, accessible to semi-technical readers.
Insert [PLACEHOLDER] markers where the author must add their own real details.
Write 150-400 words for this section.
"""


HOOK_WRITING_PROMPT = """\
Write 3 alternative opening paragraphs for a Substack post. Each must hook the reader within the first \
3 sentences and feel like it was written by a real person with domain expertise — not an AI assistant.

Styles:
1. Personal story: Start mid-scene in a specific moment from the author's work
2. Surprising insight: Lead with something counterintuitive about healthcare AI or data science
3. Direct address: Speak directly to the reader's exact frustration or aspiration
"""


CLOSING_PROMPT = """\
Write a closing paragraph and engagement prompt for a Substack post by a healthcare data scientist. \
The closing should:
- Distill the core takeaway in 1-2 sentences (not a listicle summary)
- End with a genuine question that invites readers to share their experience
- Feel like the author genuinely wants to hear from readers — not a formulaic CTA
- Be 80-120 words total
"""
