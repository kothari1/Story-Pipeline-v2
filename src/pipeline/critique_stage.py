from __future__ import annotations

import json
import logging

from google.genai.errors import ClientError

from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.llm.rate_limiter import RateLimitExhausted
from src.schemas.critique import CritiqueResult
from src.schemas.story import StoryOutput

logger = logging.getLogger(__name__)


def critique_stories(
    client: GeminiClient,
    prompts: PromptManager,
    model: str,
    stories: list[StoryOutput],
    target_grade: int,
    fallback_model: str | None = None,
) -> list[CritiqueResult]:
    age_min = target_grade + 5
    age_max = target_grade + 6

    system = prompts.get_system_instruction(
        "critique",
        target_grade=str(target_grade),
        age_min=str(age_min),
        age_max=str(age_max),
    )

    critiques: list[CritiqueResult] = []
    current_model = model

    for i, story in enumerate(stories):
        story_json = json.dumps(story.model_dump(), indent=2, ensure_ascii=False)
        prompt = prompts.get_user_prompt(
            "critique",
            target_grade=str(target_grade),
            story_json=story_json,
        )

        logger.info(f"Critique stage: evaluating version {i + 1} with {current_model}")
        try:
            result = client.generate(
                model=current_model,
                system_instruction=system,
                prompt=prompt,
            )
        except (RateLimitExhausted, ClientError) as exc:
            is_429 = isinstance(exc, ClientError) and exc.code == 429
            if (isinstance(exc, RateLimitExhausted) or is_429) and fallback_model and current_model != fallback_model:
                logger.warning(
                    f"{current_model} rate-limited, falling back to {fallback_model}"
                )
                current_model = fallback_model
                result = client.generate(
                    model=current_model,
                    system_instruction=system,
                    prompt=prompt,
                )
            else:
                raise

        critique = CritiqueResult.model_validate(result)
        critiques.append(critique)

    return critiques
