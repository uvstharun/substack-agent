"""
Telegram bot — full agent control from Telegram.

Commands:
  /start    — welcome message
  /help     — list all commands
  /guide    — first-timer's guide to Substack
  /firstpost — draft your very first Substack post (with coaching)

  DAILY SHORT CONTENT (for engagement, ~250 words each):
  /daily    — generate today's full daily pack (news + job tip + learning prompt)
  /news     — single AI-news short post
  /jobtip   — single job-search tip post
  /learned <your rough notes> — turn your learning into a polished short post

  WEEKLY LONG CONTENT:
  /topics   — generate weekly long-form topic suggestions
  /pending  — show topics waiting for approval
  /approve N / /dismiss N — act on pending topics
  /approved — list approved topics ready for outline
  /outline N — generate outline for approved topic N
  /draft N  — generate full draft (sent as .md file)
  /status   — pipeline overview
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from config.config import cfg
from agent.trend_researcher import get_trend_summary, get_ai_news_topics
from agent import topic_generator, outline_generator, draft_writer, daily_content, orchestrator, comment_suggester
from memory import topic_memory
from prompts.onboarding_prompts import SUBSTACK_GUIDE
from telegram_bot.formatters import (
    format_topics_batch,
    format_outline_summary,
    format_pipeline_status,
    _h,
)

# ── Session state (in-memory, resets on bot restart) ─────────────────────────
_last_topic_batch: dict[int, list[dict]] = {}
_last_approved_batch: dict[int, list[dict]] = {}
_last_outlined_batch: dict[int, list[dict]] = {}

PM = ParseMode.HTML


# ── Auth guard ────────────────────────────────────────────────────────────────

def _authorized(update: Update) -> bool:
    if not cfg.telegram_chat_id:
        return True
    return str(update.effective_chat.id) == str(cfg.telegram_chat_id)


async def _deny(update: Update) -> None:
    await update.message.reply_text("⛔ Unauthorized.")


async def _safe_send(update: Update, text: str) -> None:
    """Send with HTML, fall back to plain text on parse errors."""
    try:
        await update.message.reply_text(text, parse_mode=PM)
    except Exception as e:
        logger.warning(f"HTML send failed, falling back to plain: {e}")
        # Strip basic HTML tags before plain-text send
        import re
        plain = re.sub(r"<[^>]+>", "", text)
        await update.message.reply_text(plain, parse_mode=None)


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    text = (
        "👋 <b>Substack Content Agent</b>\n\n"
        "I'm your AI writing partner and coach.\n\n"
        "🆕 <b>First time on Substack?</b>\n"
        "/guide — read the first-timer's guide\n"
        "/firstpost — draft your very first post\n\n"
        "📝 <b>Daily short content (for engagement):</b>\n"
        "/daily — generate today's full daily pack\n"
        "/news — fresh AI news (list of post ideas from the web)\n"
        "/newspost N — write a post about news item N (or a short description)\n"
        "/notes [N] — generate N short 30-40 word AI Notes (default 5)\n"
        "/comment &lt;paste post&gt; — suggest 3 human-feeling comments\n"
        "  (or just paste a post into chat — I'll detect it automatically)\n"
        "/jobtip — job search strategy tip\n"
        "/learned &lt;your note&gt; — polish your learning into a post\n\n"
        "📚 <b>Weekly long-form content:</b>\n"
        "/topics — generate weekly topic suggestions\n"
        "/pending /approved /approve N /dismiss N\n"
        "/outline N /draft N\n\n"
        "📊 <b>Other:</b>\n"
        "/status — pipeline overview\n"
        "/help — show this message\n\n"
        "💬 <b>Or just chat with me</b> — ask anything about writing, "
        "Substack strategy, AI topics, or how to use this agent."
    )
    await _safe_send(update, text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    all_topics = topic_memory.get_all_topics()
    await _safe_send(update, format_pipeline_status(all_topics))


async def cmd_topics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    await _safe_send(update, "🔍 Researching trends and generating topics... (~60s)")

    try:
        trend = get_trend_summary()
        topics = topic_generator.generate_weekly_topics(trend)
    except Exception as e:
        logger.error(f"Topic generation failed: {e}")
        await _safe_send(update, f"❌ Generation failed: {_h(str(e))}")
        return

    _last_topic_batch[chat_id] = topics

    await _safe_send(update, f"✅ <b>{len(topics)} topics generated!</b> Use /approve N or /dismiss N.")

    for card in format_topics_batch(topics):
        await _safe_send(update, card)


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    topics = topic_memory.get_topics_by_status("suggested")

    if not topics:
        await _safe_send(update, "No pending topics. Run /topics to generate some.")
        return

    _last_topic_batch[chat_id] = topics
    await _safe_send(update, f"📋 <b>{len(topics)} pending topics:</b>")
    for card in format_topics_batch(topics):
        await _safe_send(update, card)


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    batch = _last_topic_batch.get(chat_id, [])

    if not context.args:
        await _safe_send(update, "Usage: /approve N (e.g. /approve 3)")
        return

    try:
        n = int(context.args[0])
        topic = batch[n - 1]
    except (ValueError, IndexError):
        await _safe_send(update, f"❌ Invalid number. Choose 1–{len(batch)}.")
        return

    topic_generator.approve_topic(topic["id"])
    title = _h(topic.get("title", ""))
    await _safe_send(
        update,
        f"✅ Approved: <b>{title}</b>\n\nRun /approved then /outline N to generate an outline.",
    )


async def cmd_dismiss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    batch = _last_topic_batch.get(chat_id, [])

    if not context.args:
        await _safe_send(update, "Usage: /dismiss N")
        return

    try:
        n = int(context.args[0])
        topic = batch[n - 1]
    except (ValueError, IndexError):
        await _safe_send(update, f"❌ Invalid number. Choose 1–{len(batch)}.")
        return

    topic_generator.dismiss_topic(topic["id"])
    await _safe_send(update, f"🗑 Dismissed topic {n}.")


async def cmd_approved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    topics = topic_memory.get_topics_by_status("approved")

    if not topics:
        await _safe_send(update, "No approved topics. Use /approve N first.")
        return

    _last_approved_batch[chat_id] = topics
    lines = "\n".join(f"  {i+1}. {_h(t.get('title',''))}" for i, t in enumerate(topics))
    await _safe_send(
        update,
        f"📋 <b>Approved topics:</b>\n{lines}\n\nRun /outline N to generate an outline.",
    )


async def cmd_outline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    topics = _last_approved_batch.get(chat_id) or topic_memory.get_topics_by_status("approved")

    if not topics:
        await _safe_send(update, "No approved topics. Run /approved first.")
        return

    if not context.args:
        await _safe_send(update, "Usage: /outline N (e.g. /outline 1)")
        return

    try:
        n = int(context.args[0])
        topic = topics[n - 1]
    except (ValueError, IndexError):
        await _safe_send(update, f"❌ Invalid number. Choose 1–{len(topics)}.")
        return

    await _safe_send(update, f"📋 Generating outline for <b>{_h(topic.get('title',''))}</b>...")

    try:
        outline = outline_generator.generate_outline(topic)
        _last_outlined_batch.setdefault(chat_id, [])
        _last_outlined_batch[chat_id].append({"topic": topic, "outline": outline})
        outline_index = len(_last_outlined_batch[chat_id])

        await _safe_send(update, format_outline_summary(outline))
        await _safe_send(update, f"Run /draft {outline_index} to write the full first draft.")
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        await _safe_send(update, f"❌ Outline failed: {_h(str(e))}")


async def cmd_draft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    chat_id = update.effective_chat.id
    outlined = _last_outlined_batch.get(chat_id, [])

    if not outlined:
        await _safe_send(update, "No outlines generated yet. Run /outline N first.")
        return

    if not context.args:
        await _safe_send(update, "Usage: /draft N (e.g. /draft 1)")
        return

    try:
        n = int(context.args[0])
        entry = outlined[n - 1]
    except (ValueError, IndexError):
        await _safe_send(update, f"❌ Invalid number. Choose 1–{len(outlined)}.")
        return

    topic = entry["topic"]
    outline = entry["outline"]
    title = topic.get("title", "draft")

    await _safe_send(update, f"✍️ Writing draft for <b>{_h(title)}</b>... (~90s)")

    try:
        draft_text = draft_writer.write_draft(topic, outline)

        file_bytes = draft_text.encode("utf-8")
        filename = title[:40].lower().replace(" ", "-").replace("/", "-") + ".md"
        await update.message.reply_document(
            document=io.BytesIO(file_bytes),
            filename=filename,
            caption=f"✅ Draft ready: <b>{_h(title)}</b>\n\nEdit and paste into Substack.",
            parse_mode=PM,
        )
    except Exception as e:
        logger.error(f"Draft generation failed: {e}")
        await _safe_send(update, f"❌ Draft failed: {_h(str(e))}")


async def _send_post_as_file(update: Update, kind: str, markdown: str) -> None:
    """Send a short post both as a preview message AND as a .md file."""
    preview = markdown if len(markdown) < 3500 else markdown[:3400] + "\n\n... (full version in file)"
    await update.message.reply_text(preview, parse_mode=None)

    file_bytes = markdown.encode("utf-8")
    filename = f"{datetime_now()}_{kind}.md"
    await update.message.reply_document(
        document=io.BytesIO(file_bytes),
        filename=filename,
        caption=f"📄 Ready to paste into Substack.",
    )


def datetime_now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


# ── Onboarding commands ──────────────────────────────────────────────────────

async def cmd_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    # The guide is plain text with simple markdown, send as-is
    await update.message.reply_text(SUBSTACK_GUIDE, parse_mode=None)


async def cmd_firstpost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    await _safe_send(update, "✍️ Drafting your very first Substack post... (~60s)")
    try:
        post = daily_content.generate_first_post()
        await _send_post_as_file(update, "first_post", post)
        await _safe_send(
            update,
            "💡 <b>Before you publish:</b>\n"
            "1. Read it aloud — does it sound like YOU?\n"
            "2. Pick one of the alternative titles at the bottom if the main one doesn't land\n"
            "3. Fill in the subtitle field on Substack (don't leave blank)\n"
            "4. Write your About page first if you haven't\n"
            "5. Hit publish — done is better than perfect for post #1",
        )
    except Exception as e:
        logger.error(f"First post generation failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


# ── Daily short content commands ─────────────────────────────────────────────

async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    await _safe_send(update, "📝 Generating today's daily pack... (~90s)\n1. AI news commentary\n2. Job search tip\n3. Daily learning prompt")
    try:
        await _safe_send(update, "🔸 <b>1/3 — AI news commentary</b>")
        news = daily_content.generate_ai_news_post()
        await _send_post_as_file(update, "ai_news", news)

        await _safe_send(update, "🔸 <b>2/3 — Job search tip</b>")
        tip = daily_content.generate_job_tip_post()
        await _send_post_as_file(update, "job_tip", tip)

        await _safe_send(
            update,
            "🔸 <b>3/3 — Daily learning</b>\n\n"
            "What did you learn or debug today? Reply with\n"
            "<code>/learned your rough notes here</code>\n"
            "and I'll turn it into a polished short post.",
        )
    except Exception as e:
        logger.error(f"Daily pack failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch fresh AI news and return a LIST of post-worthy topic ideas."""
    if not _authorized(update):
        return await _deny(update)
    await _safe_send(update, "🔍 Scanning the web for fresh AI news (last ~72h)... (~45s)")
    try:
        result = get_ai_news_topics()
        ideas = result.get("text", "").strip()
        if not ideas:
            await _safe_send(update, "No news ideas generated. Try again shortly.")
            return

        # Telegram has a 4096 char limit per message — split if needed
        chunks = [ideas[i:i+3500] for i in range(0, len(ideas), 3500)]
        await _safe_send(update, "📰 <b>AI news post ideas</b>\n\nPick one and reply with:\n<code>/newspost &lt;number or short title&gt;</code>")
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode=None)
    except Exception as e:
        logger.error(f"News research failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


async def cmd_newspost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Write a full short post based on a specific news item the user picked."""
    if not _authorized(update):
        return await _deny(update)
    pick = " ".join(context.args).strip() if context.args else ""
    if not pick:
        await _safe_send(
            update,
            "Usage: <code>/newspost &lt;number from /news OR short description&gt;</code>\n\n"
            "Example: <code>/newspost 3</code> or <code>/newspost claude new agent skills release</code>",
        )
        return
    await _safe_send(update, f"✍️ Writing post about: <i>{_h(pick)}</i>... (~45s)")
    try:
        # Reuse the daily AI news generator but seed it with the user's pick
        from prompts.daily_prompts import build_ai_news_prompt
        prompt = build_ai_news_prompt(f"The author wants to write specifically about: {pick}")
        post = orchestrator.call(prompt, max_tokens=1200, temperature=0.85)
        from agent.daily_content import _save_post
        _save_post("ai_news", post)
        await _send_post_as_file(update, "ai_news", post)
    except Exception as e:
        logger.error(f"News post failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


async def cmd_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a batch of very short (30-40 word) AI Substack Notes."""
    if not _authorized(update):
        return await _deny(update)
    # Optional count argument: /notes 7
    count = 5
    if context.args:
        try:
            count = max(1, min(10, int(context.args[0])))
        except ValueError:
            pass
    await _safe_send(update, f"⚡ Generating {count} short AI notes (30-40 words each)... (~30s)")
    try:
        notes = daily_content.generate_ai_notes(count=count)
        # Send as plain text so the numbered list renders cleanly
        await update.message.reply_text(notes, parse_mode=None)
        await _safe_send(update, "📌 Pick one and paste into Substack Notes. Run /notes again for more.")
    except Exception as e:
        logger.error(f"AI notes generation failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


async def cmd_jobtip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    await _safe_send(update, "💼 Writing today's job search tip...")
    try:
        post = daily_content.generate_job_tip_post()
        await _send_post_as_file(update, "job_tip", post)
    except Exception as e:
        logger.error(f"Job tip generation failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


async def cmd_learned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)

    raw = " ".join(context.args).strip() if context.args else ""
    if not raw:
        await _safe_send(
            update,
            "Usage: <code>/learned your rough notes about what you learned today</code>\n\n"
            "Example:\n"
            "<code>/learned today i figured out that langchain's memory module is actually terrible "
            "for production — switched to storing chat history in redis directly and my latency "
            "dropped 40%. the tutorials never mention this.</code>",
        )
        return

    await _safe_send(update, f"✍️ Polishing your learning into a post... (~30s)")
    try:
        post = daily_content.generate_learning_post(raw)
        await _send_post_as_file(update, "learning", post)
    except Exception as e:
        logger.error(f"Learning post failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


# ── Comment suggester ─────────────────────────────────────────────────────────

async def cmd_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Suggest 3 human-feeling comments for a pasted Substack post or Note."""
    if not _authorized(update):
        return await _deny(update)
    raw = " ".join(context.args).strip() if context.args else ""
    if not raw:
        await _safe_send(
            update,
            "Usage: <code>/comment &lt;paste the post or note text&gt;</code>\n\n"
            "Tip: you can also just paste the post directly into chat (no slash) "
            "and I'll detect it and suggest comments automatically.",
        )
        return
    await _safe_send(update, "🧠 Drafting 3 comment options... (~20s)")
    try:
        comments = comment_suggester.suggest_comments(raw)
        await update.message.reply_text(comments, parse_mode=None)
        await _safe_send(update, "📌 Pick one, edit a word or two so it sounds like YOU, then paste it as a comment.")
    except Exception as e:
        logger.error(f"Comment suggestion failed: {e}")
        await _safe_send(update, f"❌ Failed: {_h(str(e))}")


# ── Conversational Q&A (non-command messages) ────────────────────────────────

_CHAT_COACH_PROMPT = """\
You are the user's Substack writing coach and AI content strategist, embedded in a Telegram bot. \
You answer questions conversationally — like a knowledgeable peer over text, not a formal assistant.

Context about the user:
- They are a data scientist (~2 years experience) starting a generalist AI/Data Science Substack.
- They have NEVER posted on Substack before. You help them ship consistently.
- They control this agent from Telegram. Available commands they can run:
  • /firstpost — draft their first-ever Substack post
  • /guide — first-timer's Substack guide
  • /daily — generate today's pack (AI news + job tip + learning prompt)
  • /news, /jobtip — single daily short posts
  • /learned <notes> — polish a rough learning note into a post
  • /topics — weekly long-form topic suggestions
  • /approve N, /dismiss N, /approved, /outline N, /draft N — long-form pipeline
  • /status — pipeline overview

Style:
- Short, direct, conversational. Telegram-length — usually 2–6 short paragraphs.
- If a command would help them, mention it inline (e.g. "try /firstpost").
- No corporate filler. First person where natural. Honest over hype.
- If asked to write a full post, suggest the relevant command instead of dumping a long draft inline.
"""


def _looks_like_pasted_post(text: str) -> bool:
    """
    Heuristic: a pasted post/note is long, has paragraph breaks, and isn't
    structured like a question. Triggers the comment-suggester branch.
    """
    if len(text) < 220:
        return False
    # Multiple paragraphs strongly suggest pasted content
    paragraph_breaks = text.count("\n\n")
    line_count = text.count("\n")
    word_count = len(text.split())
    if word_count < 40:
        return False
    # Question-like short messages should still hit the coach
    if text.endswith("?") and word_count < 60:
        return False
    return paragraph_breaks >= 1 or line_count >= 3 or word_count >= 80


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Top-level orchestrator for free-form messages. Routes to:
      - comment_suggester: when a long post/note is pasted
      - coach: for questions, short messages, or anything else
    """
    if not _authorized(update):
        return await _deny(update)

    text = (update.message.text or "").strip()
    if not text:
        return

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:
        pass

    # ROUTE 1: looks like a pasted Substack post / note → suggest comments
    if _looks_like_pasted_post(text):
        logger.info("Orchestrator routed to comment_suggester")
        await _safe_send(update, "🧠 Looks like a post. Drafting 3 comment options... (~20s)")
        try:
            comments = comment_suggester.suggest_comments(text)
            await update.message.reply_text(comments, parse_mode=None)
            await _safe_send(update, "📌 Pick one, tweak a word so it sounds like YOU, then paste it as a comment.")
        except Exception as e:
            logger.error(f"Comment suggestion failed: {e}")
            await _safe_send(update, f"❌ Comment suggestion failed: {_h(str(e))}")
        return

    # ROUTE 2: question / chat / anything else → coach
    logger.info("Orchestrator routed to coach")
    try:
        reply = orchestrator.call(
            text,
            extra_system=_CHAT_COACH_PROMPT,
            max_tokens=900,
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        await _safe_send(update, f"❌ Chat failed: {_h(str(e))}")
        return

    await update.message.reply_text(reply, parse_mode=None)


# ── Bot startup ───────────────────────────────────────────────────────────────

def run_bot() -> None:
    token = cfg.telegram_bot_token
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    # Onboarding
    app.add_handler(CommandHandler("guide", cmd_guide))
    app.add_handler(CommandHandler("firstpost", cmd_firstpost))
    # Daily short content
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("newspost", cmd_newspost))
    app.add_handler(CommandHandler("notes", cmd_notes))
    app.add_handler(CommandHandler("comment", cmd_comment))
    app.add_handler(CommandHandler("jobtip", cmd_jobtip))
    app.add_handler(CommandHandler("learned", cmd_learned))
    # Weekly long-form
    app.add_handler(CommandHandler("topics", cmd_topics))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("dismiss", cmd_dismiss))
    app.add_handler(CommandHandler("approved", cmd_approved))
    app.add_handler(CommandHandler("outline", cmd_outline))
    app.add_handler(CommandHandler("draft", cmd_draft))

    # Free-form conversational Q&A (must be registered AFTER all CommandHandlers)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_chat))

    logger.info("Telegram bot starting...")
    print("\n🤖 Bot is running. Open Telegram and send /start\nPress Ctrl+C to stop.\n")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
