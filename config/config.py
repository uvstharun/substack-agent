from __future__ import annotations
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config(BaseModel):
    # Claude API
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    default_model: str = "claude-sonnet-4-6"

    # Author
    author_name: str = Field(default_factory=lambda: os.getenv("AUTHOR_NAME", "Author"))
    substack_url: str = Field(default_factory=lambda: os.getenv("SUBSTACK_URL", ""))

    # Scheduler
    weekly_run_day: str = Field(default_factory=lambda: os.getenv("WEEKLY_RUN_DAY", "sunday"))
    weekly_run_time: str = Field(default_factory=lambda: os.getenv("WEEKLY_RUN_TIME", "18:00"))

    # Content
    default_tone: str = Field(default_factory=lambda: os.getenv("DEFAULT_TONE", "conversational"))
    default_post_length: str = Field(default_factory=lambda: os.getenv("DEFAULT_POST_LENGTH", "medium"))
    max_topics_per_week: int = Field(default_factory=lambda: int(os.getenv("MAX_TOPICS_PER_WEEK", "11")))

    # Telegram
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    # Notifications
    email_notifications: bool = Field(default_factory=lambda: os.getenv("EMAIL_NOTIFICATIONS", "false").lower() == "true")
    email_address: str = Field(default_factory=lambda: os.getenv("EMAIL_ADDRESS", ""))
    smtp_host: str = Field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_user: str = Field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    smtp_password: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))

    # Storage
    storage_path: Path = Field(default_factory=lambda: BASE_DIR / os.getenv("STORAGE_PATH", "storage"))

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @property
    def topics_suggested_path(self) -> Path:
        return self.storage_path / "topics_suggested.json"

    @property
    def topics_published_path(self) -> Path:
        return self.storage_path / "topics_published.json"

    @property
    def drafts_dir(self) -> Path:
        return self.storage_path / "drafts"

    @property
    def outlines_dir(self) -> Path:
        return self.storage_path / "outlines"

    @property
    def style_memory_path(self) -> Path:
        return self.storage_path / "style_memory.json"

    def ensure_storage_dirs(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.outlines_dir.mkdir(parents=True, exist_ok=True)


cfg = Config()
cfg.ensure_storage_dirs()
