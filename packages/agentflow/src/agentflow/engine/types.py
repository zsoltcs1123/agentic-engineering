from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PermissionMode = Literal["readonly", "acceptEdits", "default"]


@dataclass
class ToolCallEntry:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    output: str
    tool_calls: list[ToolCallEntry] = field(default_factory=list)
    duration_s: float = 0.0


class EngineError(Exception):
    pass
