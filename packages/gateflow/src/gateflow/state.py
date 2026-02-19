import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class WorkflowState(TypedDict):
    task_id: str
    task_description: str
    working_directory: str
    current_step: str
    status: str
    plan: str
    review_result: str
    verification_result: str
    trace: Annotated[list[dict[str, Any]], operator.add]
    domain_data: dict[str, Any]
