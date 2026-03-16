import time

import pytest

from src.llm.rate_limiter import ModelLimit, RateLimitExhausted, RateLimiter


def test_acquire_basic():
    limiter = RateLimiter({
        "test-model": ModelLimit(rpm=10, rpd=100, min_spacing=0.0),
    })
    limiter.acquire("test-model")
    status = limiter.get_status("test-model")
    assert status["rpd_remaining"] == 99
    assert status["rpm_remaining"] == 9


def test_rpd_exhausted():
    limiter = RateLimiter({
        "test-model": ModelLimit(rpm=100, rpd=2, min_spacing=0.0),
    })
    limiter.acquire("test-model")
    limiter.acquire("test-model")
    with pytest.raises(RateLimitExhausted):
        limiter.acquire("test-model")


def test_rpd_exhausted_check():
    limiter = RateLimiter({
        "test-model": ModelLimit(rpm=100, rpd=1, min_spacing=0.0),
    })
    assert not limiter.rpd_exhausted("test-model")
    limiter.acquire("test-model")
    assert limiter.rpd_exhausted("test-model")


def test_min_spacing():
    limiter = RateLimiter({
        "test-model": ModelLimit(rpm=10, rpd=100, min_spacing=0.1),
    })
    limiter.acquire("test-model")
    start = time.time()
    limiter.acquire("test-model")
    elapsed = time.time() - start
    assert elapsed >= 0.09  # Allow slight timing slack


def test_unknown_model_passthrough():
    limiter = RateLimiter({})
    limiter.acquire("unknown-model")  # Should not raise
    assert limiter.get_status("unknown-model") == {}
