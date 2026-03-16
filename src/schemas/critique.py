from __future__ import annotations

from pydantic import BaseModel, Field


class CritiqueDimension(BaseModel):
    name: str
    score: int = Field(ge=1, le=5)
    evidence: str = ""
    suggestion: str = ""


class CritiqueResult(BaseModel):
    dimensions: list[CritiqueDimension] = Field(default_factory=list)
    overall_score: float = 0.0
    revision_priorities: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
