from src.evaluation.readability import assess
from src.schemas.story import StoryOutput


def test_assess_returns_scores(sample_story_data):
    story = StoryOutput.model_validate(sample_story_data)
    scores = assess(story, target_grade=4)
    assert scores.target_grade == 4
    assert isinstance(scores.flesch_kincaid_grade, float)
    assert isinstance(scores.dale_chall_grade, float)
    assert isinstance(scores.within_tolerance, bool)


def test_assess_grade_boundaries():
    """A very simple text should score low grade level."""
    story = StoryOutput(
        title="Test",
        sections=[
            {"heading": "Beginning", "content": "The cat sat on the mat. The dog ran fast. It was a good day. The sun was out. Birds sang in the trees."},
        ],
        characters=[],
        word_count=30,
    )
    scores = assess(story, target_grade=3)
    # Very simple text should be within tolerance for grade 3
    assert scores.flesch_kincaid_grade < 6.0
