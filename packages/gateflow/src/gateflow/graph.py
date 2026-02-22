from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from gateflow.domain import DomainPack
from gateflow.engines import ExecutionEngine
from gateflow.nodes import make_node
from gateflow.state import WorkflowState


def gate_router(state: WorkflowState) -> Literal["pass", "issues"]:
    verdict = state.get("gate_verdict", "")
    if verdict == "ISSUES":
        return "issues"
    return "pass"


def build_graph(
    domain: DomainPack,
    engines: dict[str, ExecutionEngine],
) -> CompiledStateGraph[Any, Any, Any, Any]:
    graph = StateGraph(WorkflowState)
    steps = domain.steps

    for step in steps:
        engine = engines[domain.resolve_engine(step.name)]
        graph.add_node(step.name, make_node(step, domain, engine))  # type: ignore[call-overload]

    graph.add_edge(START, steps[0].name)

    for i, step in enumerate(steps[:-1]):
        next_name = steps[i + 1].name
        if step.gate:
            graph.add_conditional_edges(
                step.name,
                gate_router,
                {"pass": next_name, "issues": END},
            )
        else:
            graph.add_edge(step.name, next_name)

    graph.add_edge(steps[-1].name, END)

    return graph.compile()
