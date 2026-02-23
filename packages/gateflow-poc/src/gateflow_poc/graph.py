from __future__ import annotations

import json
from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from gateflow_poc.engine import CursorCLI, EngineResult, PermissionMode
from gateflow_poc.prompts import (
    build_execute_prompt,
    build_finalize_prompt,
    build_plan_prompt,
    build_review_prompt,
    build_verify_prompt,
)
from gateflow_poc.state import WorkflowState

INTERRUPT_AFTER = ["plan", "review", "verify"]


def _parse_verdict(output: str) -> str:
    try:
        data = json.loads(output)
        verdict: str = data.get("verdict", "")
        if verdict in ("PASS", "ISSUES"):
            return verdict
    except (json.JSONDecodeError, AttributeError):
        pass
    upper = output.upper()
    if "ISSUES" in upper:
        return "ISSUES"
    return "PASS"


def _make_trace_entry(step: str, prompt: str, result: EngineResult) -> dict[str, Any]:
    return {
        "step": step,
        "prompt_len": len(prompt),
        "output": result.output,
        "duration_s": result.duration_s,
        "tool_call_count": len(result.tool_calls),
    }


def _make_node(
    step_name: str,
    prompt_builder: Any,
    engine: CursorCLI,
    mode: PermissionMode,
    *,
    is_gate: bool = False,
) -> Any:
    async def node(state: WorkflowState) -> dict[str, Any]:
        prompt = prompt_builder(state)
        result = await engine.run(
            prompt, working_directory=state["workdir"], mode=mode, step_name=step_name
        )
        update: dict[str, Any] = {"trace": [_make_trace_entry(step_name, prompt, result)]}

        if step_name == "plan":
            update["plan"] = result.output
        elif step_name == "review":
            update["review"] = result.output
        elif step_name == "verify":
            update["verification"] = result.output

        if is_gate:
            update["gate_verdict"] = _parse_verdict(result.output)

        return update

    node.__name__ = step_name
    node.__qualname__ = step_name
    return node


def gate_router(state: WorkflowState) -> Literal["pass", "issues"]:
    if state.get("gate_verdict", "") == "ISSUES":
        return "issues"
    return "pass"


def build_graph(
    engine: CursorCLI,
    *,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    graph = StateGraph(WorkflowState)

    graph.add_node("plan", _make_node("plan", build_plan_prompt, engine, "default"))
    graph.add_node("execute", _make_node("execute", build_execute_prompt, engine, "acceptEdits"))
    graph.add_node(
        "review", _make_node("review", build_review_prompt, engine, "default", is_gate=True)
    )
    graph.add_node(
        "verify", _make_node("verify", build_verify_prompt, engine, "default", is_gate=True)
    )
    graph.add_node("finalize", _make_node("finalize", build_finalize_prompt, engine, "acceptEdits"))

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "review")
    graph.add_conditional_edges("review", gate_router, {"pass": "verify", "issues": END})
    graph.add_conditional_edges("verify", gate_router, {"pass": "finalize", "issues": END})
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer, interrupt_after=INTERRUPT_AFTER)
