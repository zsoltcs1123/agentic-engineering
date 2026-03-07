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
    review_passed: bool
    review_cycles: int
    max_review_cycles: int
    trace: Annotated[list[TraceEntry], operator.add]
