from src.schemas.critique import CritiqueResult
from src.schemas.outline import StoryOutline
from src.schemas.safety import SafetyCheckResult
from src.schemas.story import GradeLevel, StoryOutput


def test_grade_level_properties():
    g = GradeLevel.GRADE_4
    assert g.number == 4
    assert g.age_min == 9
    assert g.age_max == 10


def test_story_output_from_dict(sample_story_data):
    story = StoryOutput.model_validate(sample_story_data)
    assert story.title == "The Village Kitten"
    assert len(story.sections) == 3
    assert len(story.characters) == 2
    assert story.full_text.startswith("Meera walked")


def test_story_outline_from_dict(sample_outline_data):
    outline = StoryOutline.model_validate(sample_outline_data)
    assert len(outline.cultural_elements) == 2
    assert outline.plot.beginning.startswith("Meera")
    assert len(outline.characters) == 1


def test_critique_result_from_dict(sample_critique_data):
    critique = CritiqueResult.model_validate(sample_critique_data)
    assert len(critique.dimensions) == 5
    assert critique.overall_score == 4.4
    assert len(critique.revision_priorities) == 2


def test_safety_result_from_dict(sample_safety_data):
    safety = SafetyCheckResult.model_validate(sample_safety_data)
    assert safety.passed is True
    assert len(safety.flags) == 1
    assert safety.flags[0].severity == "info"


def test_story_output_json_roundtrip(sample_story_data):
    story = StoryOutput.model_validate(sample_story_data)
    data = story.model_dump()
    story2 = StoryOutput.model_validate(data)
    assert story2.title == story.title
    assert len(story2.sections) == len(story.sections)
