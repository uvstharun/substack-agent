"""
Weekly scheduler — runs every Sunday evening to generate fresh topic suggestions.
Can also be triggered on-demand: python scheduler/weekly_runner.py --now
"""
from __future__ import annotations

import argparse
import json
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config.config import cfg
from agent.trend_researcher import get_trend_summary
from agent.topic_generator import generate_weekly_topics
from agent import orchestrator


def run_weekly_pipeline() -> list[dict]:
    """Full pipeline: trend research → topic generation → scoring → report."""
    start = datetime.now()
    logger.info(f"═══ Weekly pipeline started at {start.isoformat()} ═══")

    # Step 1: Trend research
    trend_summary = get_trend_summary()

    # Step 2: Topic generation
    topics = generate_weekly_topics(trend_summary)

    # Step 3: Build report
    top5 = sorted(topics, key=lambda t: t.get("scores", {}).get("composite_score", 0), reverse=True)[:5]

    elapsed = (datetime.now() - start).total_seconds()
    cost = orchestrator.session_cost_estimate()

    report = {
        "run_at": start.isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "total_topics_generated": len(topics),
        "api_cost_estimate": cost,
        "top_5_topics": top5,
    }

    _print_report(report)

    if cfg.email_notifications:
        _send_email_report(report)

    logger.info(f"═══ Pipeline complete in {elapsed:.1f}s | Est. cost: ${cost['estimated_cost_usd']} ═══")
    return topics


def _print_report(report: dict) -> None:
    print("\n" + "═" * 60)
    print(f"  WEEKLY TOPIC REPORT — {report['run_at'][:10]}")
    print("═" * 60)
    print(f"  Topics generated : {report['total_topics_generated']}")
    print(f"  API cost estimate: ${report['api_cost_estimate']['estimated_cost_usd']}")
    print(f"  Elapsed          : {report['elapsed_seconds']}s")
    print("\n  TOP 5 TOPICS THIS WEEK:")
    print("  " + "─" * 56)
    for i, t in enumerate(report["top_5_topics"], 1):
        score = t.get("scores", {}).get("composite_score", "—")
        cat = t.get("category", "—").replace("_", " ").title()
        print(f"  {i}. [{score}/10] {t.get('title')}")
        print(f"     Category : {cat}")
        print(f"     Format   : {t.get('recommended_format')}")
        print()
    print("═" * 60)
    print("  Launch the Streamlit UI to approve topics and generate outlines.")
    print("  Run: streamlit run interface/app.py")
    print("═" * 60 + "\n")


def _send_email_report(report: dict) -> None:
    if not all([cfg.smtp_user, cfg.smtp_password, cfg.email_address]):
        logger.warning("Email config incomplete — skipping email notification")
        return

    body_lines = [f"Weekly Substack Topic Report — {report['run_at'][:10]}\n"]
    for i, t in enumerate(report["top_5_topics"], 1):
        body_lines.append(f"{i}. {t.get('title')}")
        body_lines.append(f"   Category: {t.get('category')}")
        body_lines.append(f"   Why now: {t.get('why_now', '')[:200]}\n")

    body_lines.append("\nLaunch UI: streamlit run interface/app.py")
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = f"[Substack Agent] {len(report['top_5_topics'])} new topic suggestions"
    msg["From"] = cfg.smtp_user
    msg["To"] = cfg.email_address

    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.starttls()
            server.login(cfg.smtp_user, cfg.smtp_password)
            server.sendmail(cfg.smtp_user, [cfg.email_address], msg.as_string())
        logger.info("Email report sent")
    except Exception as e:
        logger.error(f"Email failed: {e}")


def start_scheduler() -> None:
    day = cfg.weekly_run_day.lower()[:3]  # 'sun', 'mon', etc.
    hour, minute = cfg.weekly_run_time.split(":")

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_weekly_pipeline,
        CronTrigger(day_of_week=day, hour=int(hour), minute=int(minute)),
        id="weekly_topics",
        name="Weekly topic generation",
    )

    logger.info(f"Scheduler started — runs every {cfg.weekly_run_day} at {cfg.weekly_run_time}")
    print(f"\nScheduler running. Next run: {cfg.weekly_run_day.capitalize()} {cfg.weekly_run_time}")
    print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Substack Content Agent — Weekly Runner")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run the pipeline immediately instead of waiting for the scheduled time",
    )
    args = parser.parse_args()

    if args.now:
        run_weekly_pipeline()
    else:
        start_scheduler()
