from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Any

import aiosqlite
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from gateflow_poc.engine import CursorCLI
from gateflow_poc.graph import build_graph
from gateflow_poc.installer import install, uninstall
from gateflow_poc.state import WorkflowState


async def _create_checkpointer(db_path: str) -> AsyncSqliteSaver:
    conn = await aiosqlite.connect(db_path)
    saver = AsyncSqliteSaver(conn)
    await saver.setup()
    return saver


def _build_initial_state(task: str, workdir: str) -> WorkflowState:
    return WorkflowState(
        task=task,
        workdir=str(Path(workdir).resolve()),
        plan="",
        review="",
        verification="",
        gate_verdict="",
        trace=[],
    )


def _print_step_output(values: dict[str, Any]) -> None:
    trace = values.get("trace", [])
    if not trace:
        return
    latest = trace[-1]
    step = latest.get("step", "?")
    duration = latest.get("duration_s", 0.0)
    output = latest.get("output", "")

    print(f"\n{'=' * 60}")
    print(f"  Step: {step}  ({duration:.1f}s)")
    print(f"{'=' * 60}")

    gate = values.get("gate_verdict", "")
    if gate:
        print(f"  Gate verdict: {gate}")

    if output:
        print(f"  Output:\n{output}")
    print()


def _print_summary(values: dict[str, Any]) -> None:
    trace = values.get("trace", [])
    total = sum(e.get("duration_s", 0.0) for e in trace)

    print(f"\n{'=' * 60}")
    print("  Workflow Summary")
    print(f"{'=' * 60}")
    print(f"  Task: {values.get('task', '')}")
    print(f"  Steps completed: {len(trace)}")
    print(f"  Total duration: {total:.1f}s")
    print()
    for entry in trace:
        step = entry.get("step", "?")
        dur = entry.get("duration_s", 0.0)
        tools = entry.get("tool_call_count", 0)
        print(f"    {step:15s}  {dur:6.1f}s  tools: {tools}")

    gate = values.get("gate_verdict", "")
    if gate == "ISSUES":
        print(f"\n  Final gate verdict: {gate}")
    print()


async def _run_workflow(args: argparse.Namespace) -> None:
    workdir = Path(args.workdir).resolve()
    db_dir = workdir / ".gateflow-poc"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(db_dir / "checkpoints.db")

    engine = CursorCLI(model=args.model)
    checkpointer = await _create_checkpointer(db_path)

    try:
        graph = build_graph(engine, checkpointer=checkpointer)
        initial_state = _build_initial_state(args.task, str(workdir))
        thread_id = uuid.uuid4().hex[:8]
        config = RunnableConfig(configurable={"thread_id": thread_id})

        print(f"Starting workflow — thread: {thread_id}")
        print(f"  Task: {args.task}")
        print(f"  Workdir: {workdir}")
        print(f"  Model: {args.model or 'default'}")
        print()

        await graph.ainvoke(initial_state, config)

        while True:
            state = await graph.aget_state(config)
            if not state.next:
                break

            _print_step_output(state.values)
            next_step = state.next[0] if state.next else "?"
            print(f"  Next step: {next_step}")

            try:
                answer = input("  [c]ontinue / [a]bort: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "a"

            if answer.startswith("a"):
                print("\nAborted.")
                _print_summary(state.values)
                return

            await graph.ainvoke(None, config)

        final_state = await graph.aget_state(config)
        _print_summary(final_state.values)
    finally:
        await checkpointer.conn.close()


def _run_install(args: argparse.Namespace) -> None:
    workdir = Path(args.workdir).resolve()
    written = install(workdir)
    print(f"Installed {len(written)} rule(s) to {workdir / '.cursor' / 'rules'}")
    for p in written:
        print(f"  {p.name}")


def _run_uninstall(args: argparse.Namespace) -> None:
    workdir = Path(args.workdir).resolve()
    removed = uninstall(workdir)
    if removed:
        print(f"Removed {len(removed)} rule(s)")
        for p in removed:
            print(f"  {p.name}")
    else:
        print("No gateflow-poc rules found.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gateflow-poc",
        description="Minimal LangGraph orchestrator over Cursor CLI",
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run a workflow")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--workdir", default=".", help="Working directory (default: .)")
    run_parser.add_argument("--model", default=None, help="Cursor CLI model override")

    install_parser = sub.add_parser("install", help="Install rules into target workspace")
    install_parser.add_argument("--workdir", default=".", help="Target workspace (default: .)")

    uninstall_parser = sub.add_parser("uninstall", help="Remove rules from target workspace")
    uninstall_parser.add_argument("--workdir", default=".", help="Target workspace (default: .)")

    _ = install_parser, uninstall_parser
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    if args.command == "run":
        asyncio.run(_run_workflow(args))
    elif args.command == "install":
        _run_install(args)
    elif args.command == "uninstall":
        _run_uninstall(args)
    else:
        print("Usage: gateflow-poc {run|install|uninstall} [options]")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
