# Substack Content Strategy Agent

A personal content intelligence agent built for a Data Scientist specializing in Healthcare AI. This agent acts as your content strategist and writing partner — it does **not** auto-post to Substack.

## What it does

- Suggests 11 personalized, trend-aware Substack topics every week across 5 categories
- Explains *why* each topic is worth writing now (trend relevance, audience demand, SEO, career value)
- Generates complete post outlines for approved topics
- Writes full first drafts you can edit and publish
- Tracks all topics suggested and published so you never repeat yourself
- Learns your writing style from feedback over time
- Runs on a weekly schedule (Sunday evenings by default)

## What it does NOT do

- Auto-post or schedule anything to Substack
- Scrape or interact with any social platform
- Make any publishing decisions without your approval

---

## Architecture

```
Trend Research (web search)
        ↓
Topic Generator (Claude — 5 categories, 11 topics/week)
        ↓
Content Scorer (audience fit, originality, timeliness, career value)
        ↓
[Author approves topics in Streamlit UI]
        ↓
Outline Generator (Claude — full structured outline with prompts)
        ↓
[Author reviews outline, triggers draft]
        ↓
Draft Writer (Claude — complete first draft in author's voice)
        ↓
[Author edits, rates, publishes to Substack manually]
        ↓
Style Learner (feedback → updates style memory for future runs)
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))

### 2. Install dependencies

```bash
cd substack-content-agent
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
ANTHROPIC_API_KEY=sk-ant-...
AUTHOR_NAME=Your Name
SUBSTACK_URL=https://yourname.substack.com
```

### 4. Verify API connection

```bash
python -c "from agent.orchestrator import call; print(call('Say hello in one word.'))"
```

---

## Running the agent

### Launch the Streamlit UI

```bash
streamlit run interface/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Generate topics on demand (no UI)

```bash
python scheduler/weekly_runner.py --now
```

### Start the weekly scheduler (background)

```bash
python scheduler/weekly_runner.py
```

Runs every Sunday at 6:00 PM by default. Customize via `WEEKLY_RUN_DAY` and `WEEKLY_RUN_TIME` in `.env`.

---

## First session workflow

1. Run `streamlit run interface/app.py`
2. Click **Generate Fresh Topics** on the Home dashboard (~60 seconds)
3. Review the 11 topic cards — approve topics you want to develop
4. Go to **Outline Builder** → click "Generate Outline" for any approved topic (~30 seconds)
5. Review the outline in the expander — sections, hooks, and personal detail prompts
6. Click **Generate Draft** to get a full first draft (~90 seconds)
7. Go to **Draft Review** → read the draft, edit inline, rate it, and leave style feedback
8. Export as markdown and paste into Substack
9. After publishing, click **Mark as Published** and paste your Substack URL

---

## Topic categories

| Category | Topics/week | Purpose |
|---|---|---|
| Lessons From My Work | 3 | Insider stories from real healthcare data science |
| Healthcare AI Explainers | 3 | Translate AI concepts through healthcare lens |
| Career & Transition | 2 | Content for data scientists leveling up |
| Trending Through Healthcare | 2 | Current AI trends filtered through expertise |
| Opinion & Hot Takes | 1 | Contrarian takes that spark conversation |

---

## Style learning

After reviewing any draft, go to **Draft Review → Feedback tab** and:
- Rate the draft 1–5 stars
- Leave free-form notes ("too long", "more personal stories", "loved the hook")

The agent parses your feedback with Claude and updates `storage/style_memory.json`. Every subsequent generation incorporates your accumulated preferences. You can also override settings directly in **Style Preferences**.

---

## Folder structure

```
agent/           — Core AI agents (orchestrator, topic generator, outline, draft, style)
tools/           — Web search, trend analysis, keyword research, content scoring
memory/          — Topic tracking, published post tracking, style preferences
prompts/         — All Claude prompt templates
storage/         — JSON data files and generated outlines/drafts
scheduler/       — Weekly runner with APScheduler
interface/       — Streamlit web UI
config/          — Config loader (reads from .env)
tests/           — pytest test suite
```

---

## Tech stack

| Component | Technology |
|---|---|
| LLM | Claude (Sonnet 4.6) via Anthropic API |
| UI | Streamlit |
| Scheduling | APScheduler |
| Web search | DuckDuckGo HTML interface (no API key) |
| Storage | JSON files (local, portable) |
| Config | python-dotenv + Pydantic |
| Logging | Loguru |
| Testing | pytest |

---

## Customizing your professional context

The agent's knowledge of your background is hardcoded in `prompts/system_prompts.py` — the `MASTER_SYSTEM_PROMPT` constant. Edit this file to:

- Add new projects as they start
- Update your skills list
- Refine your target audience description
- Adjust your stated content goals

Every Claude call includes this system prompt, so keeping it current ensures all generations stay personalized.

---

## Running tests

```bash
pytest tests/ -v
```

---

## Roadmap

- [ ] Substack RSS ingestion to track what's already published
- [ ] LinkedIn and Reddit trend monitoring for audience signal
- [ ] Multi-draft A/B comparison view
- [ ] Notion export for draft organization
- [ ] Automated weekly email digest with rendered topic cards
- [ ] GPT-4o comparison mode for headline testing
