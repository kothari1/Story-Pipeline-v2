from __future__ import annotations

import json
import logging

from src.llm.client import GeminiClient
from src.llm.prompts import PromptManager
from src.schemas.outline import StoryOutline

logger = logging.getLogger(__name__)


def generate_outline(
    client: GeminiClient,
    prompts: PromptManager,
    model: str,
    location: str,
    culture_context: str,
    target_grade: int,
    temperature: float = 0.8,
) -> StoryOutline:
    age_min = target_grade + 5
    age_max = target_grade + 6

    # Determine location type for persona
    location_lower = location.lower()
    if any(w in location_lower for w in ["village", "rural", "farm"]):
        location_type = "rural"
    elif any(w in location_lower for w in ["city", "metro", "urban", "mumbai", "delhi", "bangalore", "chennai"]):
        location_type = "urban"
    else:
        location_type = "semi-urban"

    system = prompts.get_system_instruction(
        "outline", location_type=location_type
    )

    # Call 1: CoT outline
    prompt = prompts.get_user_prompt(
        "outline",
        prompt_key="user_cot",
        target_grade=str(target_grade),
        location=location,
        culture_context=culture_context,
    )
    logger.info("Outline stage: generating initial outline")
    result = client.generate(
        model=model,
        system_instruction=system,
        prompt=prompt,
        temperature=temperature,
    )

    outline = StoryOutline.model_validate(result)

    # Call 2: Elaborate characters and environment
    elaborate_prompt = prompts.get_user_prompt(
        "outline",
        prompt_key="user_elaborate",
        outline_json=json.dumps(result, indent=2, ensure_ascii=False),
    )
    logger.info("Outline stage: elaborating characters and environment")
    elaboration = client.generate(
        model=model,
        system_instruction=system,
        prompt=elaborate_prompt,
        temperature=temperature,
    )

    # Merge elaboration into outline
    if "characters" in elaboration:
        from src.schemas.outline import CharacterProfile
        outline.characters = [
            CharacterProfile.model_validate(c) for c in elaboration["characters"]
        ]
    if "environment" in elaboration:
        from src.schemas.outline import EnvironmentDetails
        outline.environment = EnvironmentDetails.model_validate(
            elaboration["environment"]
        )
    if "refined_plot" in elaboration:
        from src.schemas.outline import PlotOutline
        outline.refined_plot = PlotOutline.model_validate(elaboration["refined_plot"])

    return outline
