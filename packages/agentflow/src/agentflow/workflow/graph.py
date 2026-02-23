from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentflow.engine import CursorCLI, EngineResult
from agentflow.engine.types import PermissionMode
from agentflow.workflow.display import print_engine_input, print_engine_output
from agentflow.workflow.state import TraceEntry, WorkflowState


def _make_trace_entry(step: str, prompt: str, result: EngineResult) -> TraceEntry:
    return TraceEntry(
        step=step,
        prompt_len=len(prompt),
        output=result.output,
        duration_s=result.duration_s,
        tool_call_count=len(result.tool_calls),
    )


async def _run_step(
    engine: CursorCLI,
    state: WorkflowState,
    *,
    step_name: str,
    prompt: str,
    mode: PermissionMode,
) -> tuple[EngineResult, list[TraceEntry]]:
    print_engine_input(step_name, prompt, mode)
    result = await engine.run(prompt, working_directory=state["workdir"], mode=mode)
    print_engine_output(step_name, result)
    return result, [_make_trace_entry(step_name, prompt, result)]


def build_graph(
    engine: CursorCLI,
    *,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    async def plan(state: WorkflowState) -> dict[str, Any]:
        prompt = f"Create a plan for this task:\n\n{state['task']}"
        result, trace = await _run_step(
            engine, state, step_name="plan", prompt=prompt, mode="default"
        )
        return {"plan": result.output, "trace": trace}

    async def implement(state: WorkflowState) -> dict[str, Any]:
        prompt = f"Implement the following plan:\n\n{state['plan']}"
        _, trace = await _run_step(
            engine, state, step_name="implement", prompt=prompt, mode="acceptEdits"
        )
        return {"trace": trace}

    async def review(state: WorkflowState) -> dict[str, Any]:
        prompt = (
            f"Review recent changes in {state['workdir']}"
            " (use git diff, git status, etc. scoped to this directory)"
        )
        result, trace = await _run_step(
            engine, state, step_name="review", prompt=prompt, mode="default"
        )
        return {"review": result.output, "trace": trace}

    graph = StateGraph(WorkflowState)

    graph.add_node("plan", plan)
    graph.add_node("implement", implement)
    graph.add_node("review", review)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "implement")
    graph.add_edge("implement", "review")
    graph.add_edge("review", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["plan", "implement", "review"],
    )
