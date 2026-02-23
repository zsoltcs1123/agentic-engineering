from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict


@dataclass
class TraceEntry:
    step: str
    prompt_len: int
    output: str
    duration_s: float
    tool_call_count: int


class WorkflowState(TypedDict):
    task: str
    workdir: str
    plan: str
    review: str
    trace: Annotated[list[TraceEntry], operator.add]
