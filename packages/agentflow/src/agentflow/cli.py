from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from agentflow.engine import CursorCLI
from agentflow.workflow import WorkflowState, build_graph
from agentflow.workflow.checkpointer import create_checkpointer
from agentflow.workflow.display import (
    print_aborted,
    print_next_step,
    print_step_output,
    print_summary,
    print_usage_error,
    print_workflow_header,
    prompt_continue_or_abort,
)


async def _setup_workflow(
    args: argparse.Namespace,
) -> tuple[CompiledStateGraph[Any, Any, Any, Any], WorkflowState, RunnableConfig, AsyncSqliteSaver]:
    workdir = Path(args.workdir).resolve()
    db_dir = workdir / ".agentflow"
    db_dir.mkdir(parents=True, exist_ok=True)

    engine = CursorCLI(model=args.model)
    checkpointer = await create_checkpointer(str(db_dir / "checkpoints.db"))
    graph = build_graph(engine, checkpointer=checkpointer)

    initial_state = WorkflowState(
        task=args.task,
        workdir=str(workdir),
        plan="",
        review="",
        trace=[],
    )
    thread_id = uuid.uuid4().hex[:8]
    config = RunnableConfig(configurable={"thread_id": thread_id})

    print_workflow_header(thread_id, args.task, workdir, args.model)

    return graph, initial_state, config, checkpointer


async def _run_interactive_loop(
    graph: CompiledStateGraph[Any, Any, Any, Any],
    initial_state: WorkflowState,
    config: RunnableConfig,
) -> None:
    await graph.ainvoke(initial_state, config)

    while True:
        state = await graph.aget_state(config)
        if not state.next:
            break

        print_step_output(state.values)
        next_step = state.next[0] if state.next else "?"
        print_next_step(next_step)

        answer = prompt_continue_or_abort()

        if answer.startswith("a"):
            print_aborted()
            print_summary(state.values)
            return

        await graph.ainvoke(None, config)

    final_state = await graph.aget_state(config)
    print_summary(final_state.values)


async def _run_workflow(args: argparse.Namespace) -> None:
    graph, initial_state, config, checkpointer = await _setup_workflow(args)
    try:
        await _run_interactive_loop(graph, initial_state, config)
    finally:
        await checkpointer.conn.close()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agentflow",
        description="Minimal LangGraph workflow over Cursor CLI",
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run a workflow")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--workdir", default=".", help="Working directory (default: .)")
    run_parser.add_argument("--model", default=None, help="Cursor CLI model override")

    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    if args.command == "run":
        asyncio.run(_run_workflow(args))
    else:
        print_usage_error()
        raise SystemExit(1)
