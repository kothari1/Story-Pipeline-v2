"""Integration tests that require a real GOOGLE_API_KEY.

Run with: pytest tests/test_integration.py -m slow
"""

import os

import pytest

from src.pipeline.orchestrator import StoryPipeline

pytestmark = pytest.mark.slow


@pytest.fixture
def api_key():
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        pytest.skip("GOOGLE_API_KEY not set")
    return key


def test_full_pipeline(api_key, tmp_path):
    pipeline = StoryPipeline(
        config_dir="config",
        api_key=api_key,
        fast=True,
    )
    pipeline.output_base = tmp_path

    run_id = pipeline.run(
        location="a village near Mangalore in coastal Karnataka",
        culture_context="Tulu-speaking fishing community",
        target_grade=4,
        review_callback=None,  # Skip HITL for automated test
    )

    run_dir = tmp_path / run_id
    assert (run_dir / "outline.json").exists()
    assert (run_dir / "final/story_final.json").exists()
