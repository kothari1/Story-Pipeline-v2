from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ModelLimit:
    rpm: int
    rpd: int
    min_spacing: float  # seconds between calls


@dataclass
class ModelState:
    timestamps: deque = field(default_factory=deque)
    daily_count: int = 0
    day_start: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    def __init__(self, limits: dict[str, ModelLimit]) -> None:
        self._limits = limits
        self._states: dict[str, ModelState] = {
            name: ModelState(day_start=time.time()) for name in limits
        }

    def acquire(self, model: str) -> None:
        if model not in self._limits:
            return
        limit = self._limits[model]
        state = self._states[model]

        with state.lock:
            now = time.time()

            # Reset daily counter if a new day
            if now - state.day_start >= 86400:
                state.daily_count = 0
                state.day_start = now

            # Check RPD
            if state.daily_count >= limit.rpd:
                raise RateLimitExhausted(
                    f"{model} daily limit exhausted ({limit.rpd} RPD)"
                )

            # Enforce min spacing
            if state.timestamps:
                elapsed = now - state.timestamps[-1]
                if elapsed < limit.min_spacing:
                    wait = limit.min_spacing - elapsed
                    logger.info(f"Rate limiter: waiting {wait:.1f}s for {model}")
                    time.sleep(wait)

            # Enforce RPM with sliding window
            window_start = time.time() - 60
            while state.timestamps and state.timestamps[0] < window_start:
                state.timestamps.popleft()

            if len(state.timestamps) >= limit.rpm:
                wait = state.timestamps[0] + 60 - time.time()
                if wait > 0:
                    logger.info(
                        f"Rate limiter: RPM limit, waiting {wait:.1f}s for {model}"
                    )
                    time.sleep(wait)
                # Clean again after sleep
                window_start = time.time() - 60
                while state.timestamps and state.timestamps[0] < window_start:
                    state.timestamps.popleft()

            state.timestamps.append(time.time())
            state.daily_count += 1
            logger.debug(
                f"{model}: {state.daily_count}/{limit.rpd} RPD, "
                f"{len(state.timestamps)}/{limit.rpm} RPM"
            )

    def get_status(self, model: str) -> dict:
        if model not in self._limits:
            return {}
        limit = self._limits[model]
        state = self._states[model]
        with state.lock:
            now = time.time()
            window_start = now - 60
            rpm_used = sum(1 for t in state.timestamps if t >= window_start)
            return {
                "rpm_remaining": limit.rpm - rpm_used,
                "rpd_remaining": limit.rpd - state.daily_count,
            }

    def rpd_exhausted(self, model: str) -> bool:
        if model not in self._limits:
            return False
        state = self._states[model]
        limit = self._limits[model]
        with state.lock:
            if time.time() - state.day_start >= 86400:
                return False
            return state.daily_count >= limit.rpd


class RateLimitExhausted(Exception):
    pass
