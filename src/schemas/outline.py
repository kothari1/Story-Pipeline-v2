from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class CulturalElement(BaseModel):
    detail: str
    category: str


class CharacterProfile(BaseModel):
    name: str
    age: int = 0
    personality: str = ""
    background: str = ""
    mannerisms: str = ""
    clothing: str = ""
    personal_goal: str = ""

    @field_validator("age", mode="before")
    @classmethod
    def parse_age(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Extract first number from strings like "70s", "about 10", "9-10"
            match = re.search(r"\d+", v)
            if match:
                return int(match.group())
        return 0


class PlotOutline(BaseModel):
    beginning: str
    middle: str
    end: str


def _coerce_to_str(v):
    """Coerce dicts and lists from LLM output into a single string."""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ".join(str(item) for item in v)
    if isinstance(v, dict):
        return " ".join(str(val) for val in v.values())
    return str(v)


class EnvironmentDetails(BaseModel):
    sensory_details: str = ""
    time_and_weather: str = ""
    local_features: str = ""

    @field_validator("sensory_details", "time_and_weather", "local_features", mode="before")
    @classmethod
    def coerce_str(cls, v):
        return _coerce_to_str(v)


class StoryOutline(BaseModel):
    cultural_elements: list[CulturalElement] = Field(default_factory=list)
    moral_lesson: str = ""
    plot: PlotOutline | None = None
    characters: list[CharacterProfile] = Field(default_factory=list)
    setting_description: str = ""
    title_suggestions: list[str] = Field(default_factory=list)
    environment: EnvironmentDetails | None = None
    refined_plot: PlotOutline | None = None
