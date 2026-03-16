from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GradeLevel(str, Enum):
    GRADE_3 = "grade_3"
    GRADE_4 = "grade_4"
    GRADE_5 = "grade_5"
    GRADE_6 = "grade_6"

    @property
    def number(self) -> int:
        return int(self.value.split("_")[1])

    @property
    def age_min(self) -> int:
        return self.number + 5

    @property
    def age_max(self) -> int:
        return self.number + 6


class VocabularyWord(BaseModel):
    word: str
    context_sentence: str
    simple_definition: str


class Character(BaseModel):
    name: str
    role: str


class StorySection(BaseModel):
    heading: str
    content: str


class ReadabilityScores(BaseModel):
    flesch_kincaid_grade: float = 0.0
    dale_chall_grade: float = 0.0
    target_grade: int = 0
    within_tolerance: bool = False


class StoryMetadata(BaseModel):
    run_id: str = ""
    version: int = 0
    model_used: str = ""
    temperature: float = 0.0
    prompt_version: str = ""
    is_revised: bool = False


class StoryOutput(BaseModel):
    title: str
    sections: list[StorySection]
    characters: list[Character]
    vocabulary_words: list[VocabularyWord] = Field(default_factory=list)
    word_count: int = 0
    moral_lesson: str = ""
    revisions_made: list[str] = Field(default_factory=list)
    readability: ReadabilityScores | None = None
    metadata: StoryMetadata = Field(default_factory=StoryMetadata)

    @property
    def full_text(self) -> str:
        return "\n\n".join(s.content for s in self.sections)
