"""Central Claude API client — all LLM calls flow through here."""
from __future__ import annotations

import json
import time
from typing import Generator, Optional

import anthropic
from loguru import logger

from config.config import cfg
from prompts.system_prompts import MASTER_SYSTEM_PROMPT

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    return _client


# ── Token tracking ────────────────────────────────────────────────────────────

_session_input_tokens = 0
_session_output_tokens = 0
_COST_PER_M_INPUT = 3.00   # USD per 1M tokens (Sonnet 4.6 pricing)
_COST_PER_M_OUTPUT = 15.00


def session_cost_estimate() -> dict:
    return {
        "input_tokens": _session_input_tokens,
        "output_tokens": _session_output_tokens,
        "estimated_cost_usd": round(
            (_session_input_tokens / 1_000_000 * _COST_PER_M_INPUT)
            + (_session_output_tokens / 1_000_000 * _COST_PER_M_OUTPUT),
            4,
        ),
    }


def reset_session_tokens() -> None:
    global _session_input_tokens, _session_output_tokens
    _session_input_tokens = 0
    _session_output_tokens = 0


# ── Core call ─────────────────────────────────────────────────────────────────

def call(
    user_prompt: str,
    extra_system: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.8,
    retries: int = 3,
) -> str:
    """Make a blocking Claude API call and return the text response."""
    global _session_input_tokens, _session_output_tokens

    system = MASTER_SYSTEM_PROMPT
    if extra_system:
        system = f"{system}\n\n{extra_system}"

    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = client.messages.create(
                model=cfg.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            _session_input_tokens += response.usage.input_tokens
            _session_output_tokens += response.usage.output_tokens
            return response.content[0].text

        except anthropic.RateLimitError as e:
            wait = 2 ** attempt
            logger.warning(f"Rate limit hit (attempt {attempt}), waiting {wait}s: {e}")
            time.sleep(wait)
            last_error = e
        except anthropic.APIError as e:
            logger.error(f"API error (attempt {attempt}): {e}")
            last_error = e
            if attempt < retries:
                time.sleep(2)

    raise RuntimeError(f"Claude API call failed after {retries} attempts") from last_error


def stream(
    user_prompt: str,
    extra_system: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.8,
) -> Generator[str, None, None]:
    """Stream a Claude response, yielding text chunks as they arrive."""
    system = MASTER_SYSTEM_PROMPT
    if extra_system:
        system = f"{system}\n\n{extra_system}"

    client = _get_client()

    with client.messages.stream(
        model=cfg.default_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream_ctx:
        for text in stream_ctx.text_stream:
            yield text


def call_json(
    user_prompt: str,
    extra_system: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> list | dict:
    """Call Claude expecting a JSON response. Returns parsed object."""
    raw = call(
        user_prompt=user_prompt,
        extra_system=extra_system + "\n\nYou MUST respond with valid JSON only. No prose before or after.",
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed. Raw response:\n{raw[:500]}")
        raise ValueError(f"Claude returned invalid JSON: {e}") from e
