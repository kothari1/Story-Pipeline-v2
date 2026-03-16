from __future__ import annotations

import json
import logging

from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.schemas.outline import StoryOutline
from src.schemas.story import StoryMetadata, StoryOutput

logger = logging.getLogger(__name__)


def generate_stories(
    client: GeminiClient,
    prompts: PromptManager,
    model: str,
    outline: StoryOutline,
    run_id: str,
    temperatures: list[float] | None = None,
    word_count_min: int = 500,
    word_count_max: int = 800,
    target_grade: int = 4,
) -> list[StoryOutput]:
    if temperatures is None:
        temperatures = [0.7, 0.8, 0.9]

    age_min = target_grade + 5
    age_max = target_grade + 6

    system = prompts.get_system_instruction(
        "generation",
        target_grade=str(target_grade),
        word_count_min=str(word_count_min),
        word_count_max=str(word_count_max),
        age_min=str(age_min),
        age_max=str(age_max),
    )

    outline_json = json.dumps(outline.model_dump(), indent=2, ensure_ascii=False)
    prompt = prompts.get_user_prompt(
        "generation",
        outline_json=outline_json,
    )

    stories: list[StoryOutput] = []
    for i, temp in enumerate(temperatures):
        version = i + 1
        logger.info(f"Generation stage: writing version {version} (temp={temp})")
        result = client.generate(
            model=model,
            system_instruction=system,
            prompt=prompt,
            temperature=temp,
        )

        story = StoryOutput.model_validate(result)
        story.metadata = StoryMetadata(
            run_id=run_id,
            version=version,
            model_used=model,
            temperature=temp,
            prompt_version=prompts.version,
        )
        stories.append(story)

    return stories
