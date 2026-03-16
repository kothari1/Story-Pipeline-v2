from __future__ import annotations

import json
import logging
import re
import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pydantic import BaseModel

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def _extract_json(text: str) -> dict:
    """Extract JSON from model response, handling markdown fences and thinking blocks."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Find the first { ... } or [ ... ] block
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        # Find matching closing bracket by counting nesting
        depth = 0
        for i in range(start, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


class GeminiClient:
    def __init__(self, api_key: str, rate_limiter: RateLimiter) -> None:
        self._client = genai.Client(api_key=api_key)
        self._rate_limiter = rate_limiter

    def generate(
        self,
        model: str,
        system_instruction: str,
        prompt: str,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.8,
        max_output_tokens: int = 8192,
    ) -> dict:
        self._rate_limiter.acquire(model)

        config_kwargs: dict = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "response_mime_type": "application/json",
        }
        if response_schema is not None:
            config_kwargs["response_schema"] = response_schema

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            **config_kwargs,
        )

        start = time.time()
        logger.info(
            f"Calling {model} (prompt: {len(prompt)} chars, temp: {temperature})"
        )

        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                break
            except ClientError as e:
                last_err = e
                if e.code == 429 and attempt < MAX_RETRIES:
                    # Parse retry delay from error if available, default 40s
                    wait = _parse_retry_delay(e) or 40
                    logger.warning(
                        f"429 rate-limited on {model}, "
                        f"retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})"
                    )
                    time.sleep(wait)
                else:
                    raise
        else:
            raise last_err  # type: ignore[misc]

        latency = time.time() - start
        text = response.text or ""
        logger.info(f"{model} responded in {latency:.1f}s ({len(text)} chars)")

        try:
            return _extract_json(text)
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {model}, returning raw text")
            return {"raw_text": text}


def _parse_retry_delay(err: ClientError) -> int | None:
    """Extract retryDelay seconds from a 429 error message."""
    try:
        # The error message contains "Please retry in XXs"
        msg = str(err)
        match = re.search(r"[Rr]etry in (\d+)", msg)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None
