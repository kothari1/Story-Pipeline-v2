from __future__ import annotations

from pydantic import BaseModel, Field


class SafetyFlag(BaseModel):
    category: str
    severity: str = Field(description="info, warning, or block")
    description: str
    quote: str = ""


class SafetyCheckResult(BaseModel):
    passed: bool = True
    flags: list[SafetyFlag] = Field(default_factory=list)
    summary: str = ""
