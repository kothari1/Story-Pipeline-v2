import json
from unittest.mock import MagicMock

from src.llm.prompts import PromptManager
from src.pipeline.critique_stage import critique_stories
from src.pipeline.generation_stage import generate_stories
from src.pipeline.outline_stage import generate_outline
from src.pipeline.revision_stage import revise_stories
from src.pipeline.safety_stage import check_safety
from src.schemas.critique import CritiqueResult
from src.schemas.outline import StoryOutline
from src.schemas.story import StoryOutput


def test_outline_stage(
    mock_client, config_dir, sample_outline_data
):
    prompts = PromptManager(config_dir, version="v1")
    # Call 1 returns outline, Call 2 returns elaboration
    elaboration = {
        "characters": sample_outline_data["characters"],
        "environment": {
            "sensory_details": "Smell of salt water",
            "time_and_weather": "Morning, warm",
            "local_features": "Stone well, coconut grove",
        },
        "refined_plot": sample_outline_data["plot"],
    }
    mock_client.generate.side_effect = [sample_outline_data, elaboration]

    outline = generate_outline(
        client=mock_client,
        prompts=prompts,
        model="gemini-2.5-flash",
        location="a village near Mangalore",
        culture_context="Tulu fishing community",
        target_grade=4,
    )
    assert isinstance(outline, StoryOutline)
    assert mock_client.generate.call_count == 2
    assert outline.environment is not None


def test_generation_stage(mock_client, config_dir, sample_outline_data, sample_story_data):
    prompts = PromptManager(config_dir, version="v1")
    outline = StoryOutline.model_validate(sample_outline_data)
    mock_client.generate.return_value = sample_story_data

    stories = generate_stories(
        client=mock_client,
        prompts=prompts,
        model="gemini-2.5-flash",
        outline=outline,
        run_id="test_run",
        target_grade=4,
    )
    assert len(stories) == 3
    assert all(isinstance(s, StoryOutput) for s in stories)
    assert stories[0].metadata.version == 1
    assert stories[2].metadata.version == 3


def test_critique_stage(mock_client, config_dir, sample_story_data, sample_critique_data):
    prompts = PromptManager(config_dir, version="v1")
    stories = [StoryOutput.model_validate(sample_story_data) for _ in range(3)]
    mock_client.generate.return_value = sample_critique_data

    critiques = critique_stories(
        client=mock_client,
        prompts=prompts,
        model="gemini-2.5-pro",
        stories=stories,
        target_grade=4,
    )
    assert len(critiques) == 3
    assert all(isinstance(c, CritiqueResult) for c in critiques)


def test_revision_stage(
    mock_client, config_dir, sample_story_data, sample_critique_data
):
    prompts = PromptManager(config_dir, version="v1")
    stories = [StoryOutput.model_validate(sample_story_data)]
    critiques = [CritiqueResult.model_validate(sample_critique_data)]
    revised_data = {**sample_story_data, "revisions_made": ["Added vocabulary"]}
    mock_client.generate.return_value = revised_data

    revised = revise_stories(
        client=mock_client,
        prompts=prompts,
        model="gemini-2.5-flash",
        stories=stories,
        critiques=critiques,
        target_grade=4,
    )
    assert len(revised) == 1
    assert revised[0].metadata.is_revised is True


def test_safety_stage(mock_client, config_dir, sample_story_data, sample_safety_data):
    prompts = PromptManager(config_dir, version="v1")
    story = StoryOutput.model_validate(sample_story_data)
    mock_client.generate.return_value = sample_safety_data

    result = check_safety(
        client=mock_client,
        prompts=prompts,
        model="gemini-2.5-flash-lite",
        story=story,
        target_grade=4,
    )
    assert result.passed is True
