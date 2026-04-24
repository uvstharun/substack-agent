"""Guidance for a first-time Substack writer — posting for the first time ever."""
from __future__ import annotations


FIRST_POST_COACHING = """\
You are coaching a writer who has NEVER posted on Substack before. This is their very first post. \
Your job is to help them ship a strong opening post that sets up their Substack for long-term \
growth — not a generic "hello world" post.

The ideal first post for a data scientist starting a generalist AI/DS Substack:
1. Introduces WHO they are in specific, memorable terms (not "I'm a data scientist" — something concrete)
2. Introduces WHY they're writing — what they'll publish, who it's for, why now
3. Introduces WHAT the reader will get (format, frequency, topics)
4. Ends with an invitation — subscribe, reply, or stay tuned

It should NOT be: a 3000-word manifesto, a fake-humble "I don't know if anyone will read this" opener, \
a list of credentials, or a summary of AI history.

Length: 400-700 words. Warm, specific, confident without bragging.

Generate a complete first-post draft based on the author's context. Include:
- A strong title (not "Hello World" or "My First Post")
- A compelling subtitle
- The full post body in markdown
- 3 alternative title options at the bottom for the author to pick from
- A short "publishing checklist" specific to first posts (handle/URL, publication name, \
  about page, welcome email setup)

Return clean markdown ready to paste into Substack.
"""


SUBSTACK_GUIDE = """\
📚 **Substack First-Timer's Guide**

━━━━━━━━━━━━━━━━━━━━━━

**Before you write your first post:**

1. **Pick your publication name** — this shows up everywhere. Make it memorable and specific \
(e.g. "Practically AI", "The Learning Data Scientist") rather than generic. Avoid your own name \
unless you want a personal brand Substack.

2. **Claim your URL** — yourname.substack.com is fine. Don't overthink it.

3. **Write your About page FIRST** — before any post. 3-4 short paragraphs: who you are, what \
you'll write, who it's for. Readers check this before subscribing.

4. **Set up your welcome email** — new subscribers get this automatically. 2-3 short paragraphs \
thanking them and telling them what's coming.

━━━━━━━━━━━━━━━━━━━━━━

**When writing a post:**

• **Title** — specific > clever. Would you click this if you saw it in a feed?
• **Subtitle** — fill it in. It's your second hook.
• **Opening** — the first 3 sentences decide whether people keep reading.
• **Short paragraphs** — 1-3 sentences each. Substack is mobile-first.
• **One idea per post** — don't try to say everything.
• **End with a question** — invites replies and builds community early.

━━━━━━━━━━━━━━━━━━━━━━

**Posting cadence for a new Substack:**

• **First 4 weeks:** 1 long post/week + 2-3 short notes/week (AI news, job tips, learnings)
• **After month 1:** find your rhythm. Consistency > frequency.
• **Substack Notes** are the fastest way to build audience early — use them aggressively.

━━━━━━━━━━━━━━━━━━━━━━

**First-month goals (realistic):**

• Ship 4 long posts + 10-15 short notes
• Write 3-5 genuine replies on other people's Notes daily
• Don't check subscriber count obsessively — focus on output
• Reply to every comment and email for the first 3 months

━━━━━━━━━━━━━━━━━━━━━━

**Commands to help you:**

/firstpost — generate your actual first post draft
/daily — get 3 short daily post ideas (AI news, job tip, learning prompt)
/news — AI news commentary post
/jobtip — job search strategy tip
/learned <your note> — turn a rough learning into a post
/topics — weekly long-form topic suggestions (what we already do)

━━━━━━━━━━━━━━━━━━━━━━

Ready? Run /firstpost when you want me to draft your opening post.
"""
