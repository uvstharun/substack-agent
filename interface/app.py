"""Streamlit interface for the Substack Content Strategy Agent."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from config.config import cfg
from memory import topic_memory, published_tracker, style_memory
from agent import topic_generator, outline_generator, draft_writer, style_learner
from agent.trend_researcher import get_trend_summary
from agent import orchestrator

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Substack Content Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    :root {
        --cream: #F5F0E8;
        --charcoal: #2C2C2C;
        --accent: #4A7C59;
        --muted: #8A8A8A;
        --card-bg: #FDFAF5;
        --border: #E0D8CC;
    }
    .main { background-color: var(--cream); }
    .stApp { background-color: var(--cream); }
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .topic-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .score-badge {
        background: var(--accent);
        color: white;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .category-pill {
        background: #E8F0EC;
        color: var(--accent);
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
    }
    h1, h2, h3 { color: var(--charcoal); }
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✍️ Substack Agent")
    st.markdown("---")
    view = st.radio(
        "Navigation",
        ["Home", "Outline Builder", "Draft Review", "Content Calendar", "Topic History", "Style Preferences"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    cost = orchestrator.session_cost_estimate()
    st.caption(f"Session tokens: {cost['input_tokens']:,} in / {cost['output_tokens']:,} out")
    st.caption(f"Est. cost: ${cost['estimated_cost_usd']}")


# ═══════════════════════════════════════════════════════════════════════════════
# HOME DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

if view == "Home":
    st.title("Weekly Topic Suggestions")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Generate Fresh Topics", use_container_width=True, type="primary"):
            with st.spinner("Researching trends and generating topics... (~60s)"):
                try:
                    trend = get_trend_summary()
                    topic_generator.generate_weekly_topics(trend)
                    st.success("New topics generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    pending = topic_memory.get_topics_by_status("suggested")
    approved_count = len(topic_memory.get_topics_by_status("approved"))
    published_count = len(published_tracker.get_all_published())

    m1, m2, m3 = st.columns(3)
    m1.metric("Pending Topics", len(pending))
    m2.metric("Approved", approved_count)
    m3.metric("Published", published_count)

    if not pending:
        st.info("No pending topic suggestions. Click 'Generate Fresh Topics' to get started.")
        st.stop()

    # Group by category
    category_labels = {
        "lessons_from_work": "📓 Lessons From My Work",
        "healthcare_ai_explainers": "🏥 Healthcare AI Explainers",
        "career_and_transition": "🚀 Career & Transition",
        "trending_through_healthcare": "📈 Trending Through Healthcare",
        "opinion_hot_takes": "🔥 Opinion & Hot Takes",
    }

    categories = {}
    for t in pending:
        cat = t.get("category", "other")
        categories.setdefault(cat, []).append(t)

    for cat_key, cat_topics in categories.items():
        st.markdown(f"### {category_labels.get(cat_key, cat_key)}")
        for topic in cat_topics:
            tid = topic.get("id", "")
            scores = topic.get("scores", {})
            composite = scores.get("composite_score", "—")
            virality = topic.get("virality_score", "—")
            career = topic.get("career_positioning_score", "—")

            with st.container():
                st.markdown(f"""
<div class="topic-card">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
    <strong style="font-size:1.05rem">{topic.get('title')}</strong>
    <span class="score-badge">Score: {composite}/10</span>
  </div>
  <p style="color:#555; margin:8px 0; font-size:0.9rem">{topic.get('why_now','')}</p>
  <div style="display:flex; gap:12px; flex-wrap:wrap; margin:8px 0; font-size:0.82rem; color:#666;">
    <span>👤 {topic.get('target_reader','')[:60]}</span>
    <span>⏱ {topic.get('estimated_read_time_minutes','—')} min read</span>
    <span>🔥 Virality: {virality}/10</span>
    <span>🎯 Career: {career}/10</span>
    <span>📝 {topic.get('recommended_format','')}</span>
  </div>
  <div style="font-size:0.82rem; color:#666;">
    Keywords: {', '.join(topic.get('seo_keywords', [])[:4])}
  </div>
</div>
""", unsafe_allow_html=True)

                c1, c2, c3 = st.columns([1, 1, 2])
                if c1.button("✅ Approve", key=f"approve_{tid}"):
                    topic_generator.approve_topic(tid)
                    st.success(f"Approved: {topic.get('title')[:40]}")
                    st.rerun()
                if c2.button("❌ Dismiss", key=f"dismiss_{tid}"):
                    topic_generator.dismiss_topic(tid)
                    st.rerun()
                with c3.expander("View full details"):
                    st.write("**Series suggestion:**", topic.get("suggested_series", "—"))
                    st.write("**Differentiate from:**")
                    for s in topic.get("similar_posts_to_differentiate_from", []):
                        st.markdown(f"- {s}")
                    st.write("**Virality reasoning:**", topic.get("virality_reasoning", "—"))
                    st.write("**Career positioning:**", topic.get("career_positioning_reasoning", "—"))

        st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# OUTLINE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

elif view == "Outline Builder":
    st.title("Outline Builder")

    approved = topic_memory.get_topics_by_status("approved")
    outlined = topic_memory.get_topics_by_status("outlined")

    tabs = st.tabs(["Generate Outline", "View Saved Outlines"])

    with tabs[0]:
        if not approved:
            st.info("No approved topics yet. Go to Home and approve some topics first.")
        else:
            for topic in approved:
                tid = topic.get("id", "")
                with st.container():
                    st.markdown(f"**{topic.get('title')}**")
                    st.caption(f"Category: {topic.get('category')} | Format: {topic.get('recommended_format')}")
                    if st.button(f"📋 Generate Outline", key=f"outline_{tid}", type="primary"):
                        with st.spinner("Generating outline..."):
                            try:
                                outline = outline_generator.generate_outline(topic)
                                st.session_state[f"outline_{tid}"] = outline
                                st.success("Outline generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
                    st.markdown("---")

    with tabs[1]:
        saved = outline_generator.get_saved_outlines()
        if not saved:
            st.info("No outlines generated yet.")
        else:
            for o in saved:
                topic_title = o.get("topic_title", o.get("_filename", "Untitled"))
                with st.expander(f"📋 {topic_title}"):
                    # Headlines
                    st.markdown("#### Headline Options")
                    for h in o.get("headline_options", []):
                        st.markdown(f"**{h.get('angle','').title()}:** {h.get('title','')}")
                        for sub in h.get("subtitle_options", []):
                            st.caption(f"  → {sub}")

                    # Hook options
                    st.markdown("#### Hook Options")
                    for hook in o.get("hook_options", []):
                        with st.container():
                            st.markdown(f"*{hook.get('type','').replace('_',' ').title()}*")
                            st.write(hook.get("text", ""))

                    # Sections
                    st.markdown("#### Post Structure")
                    for section in o.get("sections", []):
                        st.markdown(f"**{section.get('title','')}** (~{section.get('estimated_word_count','')} words)")
                        for bp in section.get("bullet_points", []):
                            st.markdown(f"- {bp}")
                        for prompt in section.get("personal_anecdotes_to_include", []):
                            st.caption(f"  💡 {prompt}")

                    st.markdown(f"**Total estimated length:** {o.get('total_estimated_word_count','')} words "
                                f"(~{o.get('estimated_read_time_minutes','')} min read)")

                    # Find matching topic for draft generation
                    topic_id = o.get("topic_id", "")
                    all_topics = topic_memory.get_all_topics()
                    matching = next((t for t in all_topics if t.get("id") == topic_id), None)

                    if matching and st.button(f"✍️ Generate Draft", key=f"draft_{o.get('_filename','')}", type="primary"):
                        with st.spinner("Writing first draft... (this takes ~60s)"):
                            try:
                                draft = draft_writer.write_draft(matching, o)
                                st.success("Draft written and saved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Draft failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# DRAFT REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

elif view == "Draft Review":
    st.title("Draft Review")

    drafts = draft_writer.get_saved_drafts()
    if not drafts:
        st.info("No drafts generated yet. Generate an outline first, then write a draft.")
        st.stop()

    selected = st.selectbox(
        "Select draft",
        options=[d["filename"] for d in drafts],
        format_func=lambda f: next((d["title"] for d in drafts if d["filename"] == f), f),
    )

    content = draft_writer.load_draft(selected)
    if not content:
        st.error("Draft not found.")
        st.stop()

    tabs = st.tabs(["Preview", "Edit", "Feedback"])

    with tabs[0]:
        meta = next((d for d in drafts if d["filename"] == selected), {})
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{meta.get('title', '')}** — {meta.get('word_count', '')} words")
        if c2.download_button("⬇️ Export .md", data=content, file_name=selected, mime="text/markdown"):
            pass
        st.markdown("---")
        st.markdown(content)

    with tabs[1]:
        edited = st.text_area("Edit draft", value=content, height=600)
        if st.button("💾 Save Edits", type="primary"):
            draft_writer.save_edited_draft(selected, edited)
            st.success("Saved.")

    with tabs[2]:
        st.markdown("#### Rate this draft")
        rating = st.slider("Rating", 1, 5, 3)
        feedback_text = st.text_area(
            "Feedback (what worked, what didn't, style notes)",
            placeholder="e.g. 'Too long, more personal stories, loved the opening hook, less technical jargon in section 3'",
            height=120,
        )
        if st.button("Submit Feedback", type="primary"):
            if feedback_text.strip():
                style_learner.process_feedback(feedback_text, rating, "draft")
                st.success("Feedback saved — the agent will incorporate this in future generations.")
            else:
                st.warning("Please enter some feedback text.")

        st.markdown("---")
        st.markdown("#### Mark as Published")
        pub_url = st.text_input("Substack URL (paste after publishing)")
        pub_notes = st.text_area("Performance notes (views, engagement, etc.)", height=80)
        all_topics = topic_memory.get_all_topics()
        stem = Path(selected).stem
        matching_topic = next((t for t in all_topics if t.get("status") == "drafted"), {})
        if st.button("✅ Mark as Published"):
            published_tracker.mark_published(
                topic_id=matching_topic.get("id", ""),
                title=meta.get("title", selected),
                substack_url=pub_url,
                performance_notes=pub_notes,
                category=matching_topic.get("category", ""),
            )
            if matching_topic.get("id"):
                topic_memory.update_topic_status(matching_topic["id"], "published")
            st.success("Marked as published!")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════

elif view == "Content Calendar":
    st.title("Content Calendar")

    all_topics = topic_memory.get_all_topics()
    published = published_tracker.get_all_published()
    cadence = published_tracker.publishing_cadence()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Published", cadence["total_published"])
    m2.metric("Topics in Pipeline", len([t for t in all_topics if t.get("status") in ("approved", "outlined", "drafted")]))
    m3.metric("Suggested Pending", len([t for t in all_topics if t.get("status") == "suggested"]))

    st.markdown("---")

    # Category distribution
    dist = topic_memory.category_distribution()
    if dist:
        labels = {
            "lessons_from_work": "Lessons From Work",
            "healthcare_ai_explainers": "Healthcare AI Explainers",
            "career_and_transition": "Career & Transition",
            "trending_through_healthcare": "Trending Healthcare",
            "opinion_hot_takes": "Opinion & Hot Takes",
        }
        df_dist = pd.DataFrame([
            {"Category": labels.get(k, k), "Count": v}
            for k, v in dist.items()
        ])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Topic Category Distribution")
            fig = px.pie(df_dist, names="Category", values="Count",
                         color_discrete_sequence=["#4A7C59", "#7FB08A", "#A8C9B2", "#D0E4D9", "#E8F4EB"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Posts Per Month")
            monthly = cadence.get("posts_per_month", {})
            if monthly:
                df_monthly = pd.DataFrame(
                    [{"Month": k, "Posts": v} for k, v in sorted(monthly.items())]
                )
                fig2 = px.bar(df_monthly, x="Month", y="Posts", color_discrete_sequence=["#4A7C59"])
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No published posts yet.")

    # Series candidates
    st.markdown("---")
    st.markdown("#### Series Opportunities")
    series = topic_memory.get_series_candidates()
    if series:
        for s in series[:5]:
            with st.expander(f"📚 \"{s['keyword']}\" series ({s['topic_count']} related topics)"):
                for t in s["topics"]:
                    st.markdown(f"- {t.get('title','')}")
    else:
        st.info("Keep generating topics — series opportunities will appear once patterns emerge.")


# ═══════════════════════════════════════════════════════════════════════════════
# TOPIC HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

elif view == "Topic History":
    st.title("Topic History")

    all_topics = topic_memory.get_all_topics()
    if not all_topics:
        st.info("No topics yet. Generate your first batch from the Home dashboard.")
        st.stop()

    # Filters
    c1, c2 = st.columns(2)
    status_filter = c1.multiselect(
        "Filter by status",
        options=["suggested", "approved", "outlined", "drafted", "published", "dismissed"],
        default=[],
    )
    category_filter = c2.multiselect(
        "Filter by category",
        options=list({t.get("category", "") for t in all_topics}),
        default=[],
    )

    filtered = all_topics
    if status_filter:
        filtered = [t for t in filtered if t.get("status") in status_filter]
    if category_filter:
        filtered = [t for t in filtered if t.get("category") in category_filter]

    # Table
    rows = []
    for t in filtered:
        scores = t.get("scores", {})
        rows.append({
            "Title": t.get("title", ""),
            "Category": t.get("category", "").replace("_", " ").title(),
            "Status": t.get("status", ""),
            "Score": scores.get("composite_score", "—"),
            "Format": t.get("recommended_format", ""),
            "Suggested": t.get("suggested_at", "")[:10],
            "Virality": t.get("virality_score", ""),
            "Career": t.get("career_positioning_score", ""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=500)

    csv = df.to_csv(index=False)
    st.download_button("⬇️ Export CSV", data=csv, file_name="topic_history.csv", mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# STYLE PREFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

elif view == "Style Preferences":
    st.title("Style Preferences")
    st.caption("These settings are learned from your feedback and influence every generation.")

    prefs = style_memory.get_preferences()
    full_mem = style_memory.get_full_memory()

    tabs = st.tabs(["Current Preferences", "Manual Overrides", "Feedback History"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        c1.metric("Tone", prefs.get("tone", "—").title())
        c1.metric("Length", prefs.get("length", "—").title())
        c2.metric("Technical Depth", prefs.get("technical_depth", "—").title())
        c2.metric("Preferred Hook", prefs.get("preferred_hook", "—").replace("_", " ").title())

        st.markdown("**Wants more of:**")
        for item in prefs.get("wants_more", []):
            st.markdown(f"- {item}")

        st.markdown("**Wants less of:**")
        for item in prefs.get("wants_less", []):
            st.markdown(f"- {item}")

        if prefs.get("phrases_to_avoid"):
            st.markdown("**Phrases to avoid:** " + ", ".join(prefs["phrases_to_avoid"]))

        if prefs.get("free_form_notes"):
            st.markdown("**Notes:**")
            st.write(prefs["free_form_notes"])

    with tabs[1]:
        st.markdown("Adjust preferences directly. These override learned settings.")

        tone = st.selectbox("Tone", ["conversational", "casual", "formal", "technical", "accessible"],
                            index=["conversational", "casual", "formal", "technical", "accessible"]
                            .index(prefs.get("tone", "conversational")))
        length = st.selectbox("Length", ["short", "medium", "long"],
                              index=["short", "medium", "long"].index(prefs.get("length", "medium")))
        depth = st.selectbox("Technical depth", ["accessible", "balanced", "technical"],
                             index=["accessible", "balanced", "technical"]
                             .index(prefs.get("technical_depth", "balanced")))
        hook = st.selectbox("Preferred hook style",
                            ["personal_story", "surprising_stat", "provocative_question"],
                            index=["personal_story", "surprising_stat", "provocative_question"]
                            .index(prefs.get("preferred_hook", "personal_story")))

        avoid_raw = st.text_input(
            "Phrases to avoid (comma-separated)",
            value=", ".join(prefs.get("phrases_to_avoid", [])),
        )
        notes = st.text_area("Additional notes for the agent", value=prefs.get("free_form_notes", ""), height=100)

        if st.button("💾 Save Preferences", type="primary"):
            style_learner.manually_update_preference("tone", tone)
            style_learner.manually_update_preference("length", length)
            style_learner.manually_update_preference("technical_depth", depth)
            style_learner.manually_update_preference("preferred_hook", hook)
            style_learner.manually_update_preference(
                "phrases_to_avoid", [p.strip() for p in avoid_raw.split(",") if p.strip()]
            )
            style_learner.manually_update_preference("free_form_notes", notes)
            st.success("Preferences saved.")

    with tabs[2]:
        history = style_learner.get_feedback_history()
        if not history:
            st.info("No feedback submitted yet. Rate drafts from the Draft Review view to build history.")
        else:
            for entry in reversed(history[-20:]):
                with st.expander(f"{entry.get('timestamp','')[:10]} — {entry.get('content_type','').title()} (Rating: {entry.get('rating','—')}/5)"):
                    st.write(entry.get("feedback_text", ""))
                    if entry.get("adjustments_applied"):
                        st.json(entry["adjustments_applied"])
