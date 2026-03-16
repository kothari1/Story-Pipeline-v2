from __future__ import annotations

import json
import logging
import time

import anthropic

from .client import _extract_json
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Thin wrapper over the Anthropic SDK with the same interface as GeminiClient."""

    def __init__(self, api_key: str, rate_limiter: RateLimiter) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._rate_limiter = rate_limiter

    def generate(
        self,
        model: str,
        system_instruction: str,
        prompt: str,
        response_schema=None,  # unused — Claude doesn't support native schema enforcement
        temperature: float = 0.8,
        max_output_tokens: int = 8192,
    ) -> dict:
        self._rate_limiter.acquire(model)

        # Append JSON instruction to system prompt so Claude outputs parseable JSON
        system = (
            system_instruction.rstrip()
            + "\n\nIMPORTANT: Your response must be valid JSON only, with no markdown "
            "fences, no explanation before or after — just the raw JSON object."
        )

        start = time.time()
        logger.info(
            f"Calling {model} (prompt: {len(prompt)} chars, temp: {temperature})"
        )

        with self._client.messages.stream(
            model=model,
            max_tokens=max_output_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        latency = time.time() - start
        text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )
        logger.info(f"{model} responded in {latency:.1f}s ({len(text)} chars)")

        try:
            return _extract_json(text)
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {model}, returning raw text")
            return {"raw_text": text}
