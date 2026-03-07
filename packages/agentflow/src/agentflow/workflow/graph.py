from __future__ import annotations

import re
from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentflow.engine import CursorCLI, EngineResult
from agentflow.engine.types import PermissionMode
from agentflow.workflow.display import print_engine_input, print_engine_output
from agentflow.workflow.state import TraceEntry, WorkflowState

_PASS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bpass\b", re.IGNORECASE),
    re.compile(r"\blgtm\b", re.IGNORECASE),
    re.compile(r"\bno issues\b", re.IGNORECASE),
    re.compile(r"\bapproved\b", re.IGNORECASE),
    re.compile(r"\bno problems\b", re.IGNORECASE),
    re.compile(r"\blooks good\b", re.IGNORECASE),
]


def _review_passed(output: str) -> bool:
    return any(p.search(output) for p in _PASS_PATTERNS)


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


def _review_router(state: WorkflowState) -> Literal["implement", "document"]:
    if state["review_passed"]:
        return "document"
    if state["review_cycles"] >= state["max_review_cycles"]:
        return "document"
    return "implement"


def build_graph(
    engine: CursorCLI,
    *,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    async def implement(state: WorkflowState) -> dict[str, Any]:
        prompt = f"Implement the following plan:\n\n{state['task']}"
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
        passed = _review_passed(result.output)
        cycles = state["review_cycles"] + 1
        return {"review_passed": passed, "review_cycles": cycles, "trace": trace}

    async def document(state: WorkflowState) -> dict[str, Any]:
        prompt = (
            f"Update project documentation in {state['workdir']} to reflect the changes just made."
        )
        _, trace = await _run_step(
            engine, state, step_name="document", prompt=prompt, mode="acceptEdits"
        )
        return {"trace": trace}

    async def finalize(state: WorkflowState) -> dict[str, Any]:
        prompt = (
            f"Commit all changes in {state['workdir']}."
            " Optionally push the branch and open a pull request."
        )
        _, trace = await _run_step(
            engine, state, step_name="finalize", prompt=prompt, mode="acceptEdits"
        )
        return {"trace": trace}

    graph = StateGraph(WorkflowState)

    graph.add_node("implement", implement)
    graph.add_node("review", review)
    graph.add_node("document", document)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "implement")
    graph.add_edge("implement", "review")
    graph.add_conditional_edges("review", _review_router)
    graph.add_edge("document", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["implement", "review", "document", "finalize"],
    )
