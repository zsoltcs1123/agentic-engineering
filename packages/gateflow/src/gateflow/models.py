from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


class EngineError(Exception):
    pass


@dataclass
class EngineResult:
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, Any] | None = None
    duration_s: float = 0.0


class NodeOutput(BaseModel):
    reasoning: str
    assumptions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    blind_spots: list[str]
    output: str


class GateDecision(BaseModel):
    verdict: Literal["PASS", "ISSUES"]
    reasoning: str
    evidence: list[str]
    blind_spots: list[str]
    issues: list[str] = Field(default_factory=list)
