from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class WorkflowState(TypedDict):
    task: str
    workdir: str
    plan: str
    review: str
    verification: str
    gate_verdict: str
    trace: Annotated[list[dict[str, Any]], operator.add]
