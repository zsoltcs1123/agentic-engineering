from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from gateflow.checkpointer import create_checkpointer
from gateflow.domain import DomainPack
from gateflow.engines import ExecutionEngine
from gateflow.engines.cursor_cli import CursorCLIEngine
from gateflow.engines.cursor_cloud import CursorCloudEngine
from gateflow.engines.raw_llm import RawLLMEngine
from gateflow.graph import build_graph
from gateflow.installer import install, uninstall
from gateflow.state import WorkflowState

_DEFAULT_DOMAIN_PACK = Path(__file__).resolve().parents[2] / "domain_packs" / "software-dev"

_ENGINE_FACTORIES: dict[str, type[Any]] = {
    "raw-llm": RawLLMEngine,
    "cursor-cli": CursorCLIEngine,
    "cursor-cloud": CursorCloudEngine,
}


_SUBCOMMANDS = {"run", "install", "uninstall"}


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("task_description", help="Task to execute")
    parser.add_argument("--workdir", default=".", help="Working directory (default: .)")
    parser.add_argument("--domain", default=None, help="Path to domain pack directory")
    parser.add_argument(
        "--engine",
        default=None,
        choices=list(_ENGINE_FACTORIES),
        help="Override the default engine from the domain pack",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    import sys

    raw = argv if argv is not None else sys.argv[1:]
    if raw and raw[0] not in _SUBCOMMANDS and not raw[0].startswith("-"):
        raw = ["run", *raw]

    parser = argparse.ArgumentParser(
        prog="gateflow",
        description="Quality-gated workflow orchestrator",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a workflow")
    _add_run_args(run_parser)

    install_parser = subparsers.add_parser(
        "install", help="Install domain pack rules into a workspace"
    )
    install_parser.add_argument("--domain", default=None, help="Path to domain pack directory")
    install_parser.add_argument(
        "--workdir", default=".", help="Target workspace directory (default: .)"
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall", help="Remove installed gateflow rules from a workspace"
    )
    uninstall_parser.add_argument(
        "--workdir", default=".", help="Target workspace directory (default: .)"
    )

    args = parser.parse_args(raw)
    _ = install_parser, uninstall_parser
    return args


def _resolve_domain_path(domain_arg: str | None) -> Path:
    if domain_arg is not None:
        return Path(domain_arg).resolve()
    return _DEFAULT_DOMAIN_PACK


def _create_engine_instance(name: str) -> ExecutionEngine:
    factory = _ENGINE_FACTORIES.get(name)
    if factory is None:
        supported = ", ".join(sorted(_ENGINE_FACTORIES))
        raise SystemExit(f"Unknown engine '{name}'. Supported: {supported}")
    return factory()  # type: ignore[no-any-return]


def create_engines(
    domain: DomainPack, engine_override: str | None = None
) -> dict[str, ExecutionEngine]:
    needed: set[str] = set()
    for step in domain.steps:
        engine_name = domain.resolve_engine(step.name)
        if engine_override is not None:
            needed.add(engine_override)
        else:
            needed.add(engine_name)

    engines: dict[str, ExecutionEngine] = {}
    for name in needed:
        engines[name] = _create_engine_instance(name)

    if engine_override is not None:
        for step in domain.steps:
            original = domain.resolve_engine(step.name)
            if original not in engines:
                engines[original] = engines[engine_override]

    return engines


def _build_initial_state(task_description: str, working_directory: str) -> WorkflowState:
    return WorkflowState(
        task_id=uuid.uuid4().hex[:8],
        task_description=task_description,
        working_directory=str(Path(working_directory).resolve()),
        current_step="",
        status="running",
        plan="",
        review_result="",
        verification_result="",
        gate_verdict="",
        trace=[],
        domain_data={},
    )


def _print_step_output(state_values: dict[str, Any]) -> None:
    step = state_values.get("current_step", "")
    print(f"\n{'=' * 60}")
    print(f"  Completed step: {step}")
    print(f"{'=' * 60}")

    gate_verdict = state_values.get("gate_verdict", "")
    if gate_verdict:
        print(f"  Gate verdict: {gate_verdict}")

    trace = state_values.get("trace", [])
    if trace:
        latest = trace[-1]
        duration = latest.get("duration_s", 0.0)
        prompt = latest.get("prompt", "")
        output = latest.get("output", "")
        print(f"  Duration: {duration:.2f}s")
        if prompt:
            print(f"  Prompt:\n    {prompt}")
        print(f"  Output:\n    {output}")
    print()


def _print_summary(state_values: dict[str, Any]) -> None:
    trace = state_values.get("trace", [])
    total_duration = sum(entry.get("duration_s", 0.0) for entry in trace)

    print(f"\n{'=' * 60}")
    print("  Workflow Summary")
    print(f"{'=' * 60}")
    print(f"  Task: {state_values.get('task_description', '')}")
    print(f"  Steps completed: {len(trace)}")
    print(f"  Total duration: {total_duration:.2f}s")
    print()

    for entry in trace:
        step = entry.get("step", "?")
        duration = entry.get("duration_s", 0.0)
        tokens = entry.get("token_usage") or {}
        input_t = tokens.get("input_tokens", "-")
        output_t = tokens.get("output_tokens", "-")
        print(f"  {step:20s}  {duration:6.2f}s  tokens: {input_t}/{output_t}")

    gate = state_values.get("gate_verdict", "")
    if gate == "ISSUES":
        print(f"\n  Final gate verdict: {gate}")
    print()


async def _run_workflow(args: argparse.Namespace) -> None:
    domain = DomainPack.load(_resolve_domain_path(args.domain))
    engines = create_engines(domain, args.engine)

    workdir = Path(args.workdir).resolve()
    db_dir = workdir / ".gateflow"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(db_dir / "checkpoints.db")

    checkpointer = await create_checkpointer(db_path)
    try:
        graph = build_graph(domain, engines, checkpointer=checkpointer)
        initial_state = _build_initial_state(args.task_description, args.workdir)
        config = RunnableConfig(configurable={"thread_id": initial_state["task_id"]})

        print(f"Starting workflow [{domain.name}] — task_id: {initial_state['task_id']}")
        print(f"  Task: {args.task_description}")
        print(f"  Working directory: {initial_state['working_directory']}")
        interrupt_steps = domain.interrupt_after_steps()
        if interrupt_steps:
            print(f"  Interrupt after: {', '.join(interrupt_steps)}")
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
                print("\nWorkflow aborted by user.")
                _print_summary(state.values)
                return

            await graph.ainvoke(None, config)

        final_state = await graph.aget_state(config)
        _print_summary(final_state.values)
    finally:
        await checkpointer.conn.close()


def _run_install(args: argparse.Namespace) -> None:
    domain_path = _resolve_domain_path(args.domain)
    workdir = Path(args.workdir).resolve()
    written = install(domain_path, workdir)
    print(f"Installed {len(written)} rule(s) to {workdir / '.cursor' / 'rules'}")
    for path in written:
        print(f"  {path.name}")


def _run_uninstall(args: argparse.Namespace) -> None:
    workdir = Path(args.workdir).resolve()
    removed = uninstall(workdir)
    if removed:
        print(f"Removed {len(removed)} rule(s) from {workdir / '.cursor' / 'rules'}")
        for path in removed:
            print(f"  {path.name}")
    else:
        print("No gateflow rules found to remove.")


def main() -> None:
    load_dotenv()
    args = parse_args()

    if args.command == "install":
        _run_install(args)
    elif args.command == "uninstall":
        _run_uninstall(args)
    elif args.command == "run":
        asyncio.run(_run_workflow(args))
    else:
        print("Usage: gateflow {run|install|uninstall} [options]")
        print("  Run 'gateflow <command> --help' for command-specific options.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
