from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.llm.client import GeminiClient
from src.llm.rate_limiter import ModelLimit, RateLimiter


@pytest.fixture
def config_dir():
    return Path(__file__).parent.parent / "config"


@pytest.fixture
def rate_limiter():
    limits = {
        "gemini-2.5-flash": ModelLimit(rpm=10, rpd=500, min_spacing=0.0),
        "gemini-2.5-pro": ModelLimit(rpm=5, rpd=100, min_spacing=0.0),
        "gemini-2.5-flash-lite": ModelLimit(rpm=15, rpd=1000, min_spacing=0.0),
    }
    return RateLimiter(limits)


@pytest.fixture
def mock_client(rate_limiter):
    client = MagicMock(spec=GeminiClient)
    client._rate_limiter = rate_limiter
    return client


@pytest.fixture
def sample_outline_data():
    return {
        "cultural_elements": [
            {"detail": "Children play kabaddi after school", "category": "games"},
            {"detail": "Fresh idli-sambar for breakfast", "category": "food"},
        ],
        "moral_lesson": "True friendship means helping others without expecting anything in return",
        "plot": {
            "beginning": "Meera finds a stray kitten near the village well",
            "middle": "She cares for it despite her family's concerns",
            "end": "The kitten brings the community together",
        },
        "characters": [
            {
                "name": "Meera",
                "age": 9,
                "personality": "curious and kind",
                "background": "Lives in a fishing village with her grandmother",
            }
        ],
        "setting_description": "A small fishing village on the coast of Karnataka",
        "title_suggestions": ["The Village Kitten", "Meera's Friend", "By the Well"],
    }


@pytest.fixture
def sample_story_data():
    return {
        "title": "The Village Kitten",
        "sections": [
            {
                "heading": "Beginning",
                "content": "Meera walked to the old stone well at the edge of the village. "
                "The morning sun painted the coconut trees gold. She heard a tiny sound. "
                "Behind the well, a small orange kitten shivered in the cool breeze. "
                "Meera knelt down and whispered softly. The kitten looked at her with wide green eyes.",
            },
            {
                "heading": "Middle",
                "content": "Every day after school, Meera brought milk and rice for the kitten. "
                "She named it Chinna, meaning small one. Her grandmother worried. "
                "But Meera was determined. She built a little shelter from palm leaves. "
                "The other children started coming to see Chinna too.",
            },
            {
                "heading": "End",
                "content": "One evening, old Mr. Shetty from the fish market brought a basket for Chinna. "
                "Mrs. Patel brought a small blanket. The whole village had grown fond of the little kitten. "
                "Meera smiled. She had learned that kindness, like ripples in water, spreads to everyone around.",
            },
        ],
        "characters": [
            {"name": "Meera", "role": "protagonist"},
            {"name": "Chinna", "role": "the kitten"},
        ],
        "vocabulary_words": [
            {
                "word": "determined",
                "context_sentence": "Meera was determined to help the kitten",
                "simple_definition": "having a strong will to do something",
            }
        ],
        "word_count": 180,
        "moral_lesson": "Kindness spreads to everyone around",
    }


@pytest.fixture
def sample_critique_data():
    return {
        "dimensions": [
            {
                "name": "Vocabulary Level",
                "score": 4,
                "evidence": "Words like 'determined' and 'shivered' are grade-appropriate",
                "suggestion": "Add one more context-rich vocabulary word",
            },
            {
                "name": "Cultural Authenticity",
                "score": 5,
                "evidence": "Fishing village, coconut trees, names like Shetty and Patel",
                "suggestion": "Could add more food details",
            },
            {
                "name": "Sentence Clarity",
                "score": 4,
                "evidence": "Sentences are short and clear",
                "suggestion": "Vary sentence length slightly more",
            },
            {
                "name": "Narrative Coherence",
                "score": 4,
                "evidence": "Clear arc from finding to community",
                "suggestion": "Strengthen the middle section transition",
            },
            {
                "name": "Child-Friendliness",
                "score": 5,
                "evidence": "Warm, engaging, age-appropriate themes",
                "suggestion": "None needed",
            },
        ],
        "overall_score": 4.4,
        "revision_priorities": [
            "Add more vocabulary words with context",
            "Strengthen middle section transition",
        ],
        "strengths": [
            "Authentic cultural details",
            "Engaging protagonist",
            "Natural moral lesson integration",
        ],
    }


@pytest.fixture
def sample_safety_data():
    return {
        "passed": True,
        "flags": [
            {
                "category": "Cultural Sensitivity",
                "severity": "info",
                "description": "Story uses regionally authentic names",
                "quote": "Mr. Shetty, Mrs. Patel",
            }
        ],
        "summary": "Story is safe and appropriate for classroom use",
    }
