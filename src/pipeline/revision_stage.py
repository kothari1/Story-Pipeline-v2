from __future__ import annotations

import json
import logging

from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.schemas.critique import CritiqueResult
from src.schemas.story import StoryOutput

logger = logging.getLogger(__name__)


def revise_stories(
    client: GeminiClient,
    prompts: PromptManager,
    model: str,
    stories: list[StoryOutput],
    critiques: list[CritiqueResult],
    target_grade: int,
    word_count_min: int = 500,
    word_count_max: int = 800,
) -> list[StoryOutput]:
    system = prompts.get_system_instruction("revision")
    revised: list[StoryOutput] = []

    for i, (story, critique) in enumerate(zip(stories, critiques)):
        story_json = json.dumps(story.model_dump(), indent=2, ensure_ascii=False)
        critique_json = json.dumps(critique.model_dump(), indent=2, ensure_ascii=False)
        priorities = "\n".join(
            f"{j + 1}. {p}" for j, p in enumerate(critique.revision_priorities)
        )

        prompt = prompts.get_user_prompt(
            "revision",
            story_json=story_json,
            critique_json=critique_json,
            revision_priorities=priorities,
            word_count_min=str(word_count_min),
            word_count_max=str(word_count_max),
        )

        logger.info(f"Revision stage: revising version {i + 1}")
        result = client.generate(
            model=model,
            system_instruction=system,
            prompt=prompt,
        )

        rev = StoryOutput.model_validate(result)
        rev.metadata = story.metadata.model_copy()
        rev.metadata.is_revised = True
        revised.append(rev)

    return revised
