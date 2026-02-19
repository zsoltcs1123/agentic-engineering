from typing import Any

import pytest
from langgraph.graph import StateGraph

from gateflow import WorkflowState


@pytest.mark.unit
def test_workflow_state_usable_as_langgraph_state():
    graph = StateGraph[Any, None, Any, Any](WorkflowState)
    graph.add_node("noop", lambda state: state)
    graph.set_entry_point("noop")
    compiled = graph.compile()
    assert compiled is not None
