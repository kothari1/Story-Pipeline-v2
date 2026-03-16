from __future__ import annotations

import json
import logging

from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.schemas.safety import SafetyCheckResult
from src.schemas.story import StoryOutput

logger = logging.getLogger(__name__)


def check_safety(
    client: GeminiClient,
    prompts: PromptManager,
    model: str,
    story: StoryOutput,
    target_grade: int,
) -> SafetyCheckResult:
    age_min = target_grade + 5
    age_max = target_grade + 6

    system = prompts.get_system_instruction(
        "safety",
    )
    story_json = json.dumps(story.model_dump(), indent=2, ensure_ascii=False)
    prompt = prompts.get_user_prompt(
        "safety",
        target_grade=str(target_grade),
        story_json=story_json,
        age_min=str(age_min),
        age_max=str(age_max),
    )

    logger.info("Safety stage: checking story content")
    result = client.generate(
        model=model,
        system_instruction=system,
        prompt=prompt,
    )

    return SafetyCheckResult.model_validate(result)
