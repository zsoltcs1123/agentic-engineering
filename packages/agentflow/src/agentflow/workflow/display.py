from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from agentflow.engine.types import EngineResult, PermissionMode
from agentflow.workflow.state import TraceEntry

_console = Console()

_MAX_BODY_CHARS = 2000


def _truncate(text: str, limit: int = _MAX_BODY_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n… truncated ({len(text)} chars total)"


def print_workflow_header(thread_id: str, task: str, workdir: Path, model: str | None) -> None:
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan", justify="right")
    info.add_column()
    info.add_row("Thread", thread_id)
    info.add_row("Task", task)
    info.add_row("Workdir", str(workdir))
    info.add_row("Model", model or "default")
    _console.print()
    _console.print(Panel(info, title="[bold]agentflow[/bold]", border_style="blue"))


def print_engine_input(step_name: str, prompt: str, mode: PermissionMode) -> None:
    subtitle = f"{len(prompt)} chars · mode={mode}"
    body = _truncate(prompt)
    _console.print()
    _console.print(
        Panel(
            body,
            title=f"[bold yellow]{step_name}[/] INPUT",
            subtitle=subtitle,
            border_style="yellow",
        )
    )


def print_engine_output(step_name: str, result: EngineResult) -> None:
    subtitle = f"{len(result.output)} chars · {len(result.tool_calls)} tool calls"
    body = _truncate(result.output)
    _console.print()
    _console.print(
        Panel(
            body,
            title=f"[bold green]{step_name}[/] OUTPUT",
            subtitle=subtitle,
            border_style="green",
        )
    )


def print_step_output(values: dict[str, Any]) -> None:
    trace: list[TraceEntry] = values.get("trace", [])
    if not trace:
        return
    latest = trace[-1]
    _console.print()
    _console.print(Rule(f"[bold]{latest.step}[/bold]  completed in {latest.duration_s:.1f}s"))


def print_next_step(step_name: str) -> None:
    _console.print(f"  Next step: [bold cyan]{step_name}[/bold cyan]")


def prompt_continue_or_abort() -> str:
    try:
        answer: str = Prompt.ask("  \\[c]ontinue / \\[a]bort", console=_console)
        return answer.strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "a"


def print_aborted() -> None:
    _console.print()
    _console.print("[bold red]Aborted.[/bold red]")


def print_usage_error() -> None:
    _console.print("[bold red]Usage:[/] agentflow run <task> [--workdir .] [--model MODEL]")


def print_summary(values: dict[str, Any]) -> None:
    trace: list[TraceEntry] = values.get("trace", [])
    total = sum(entry.duration_s for entry in trace)

    table = Table(title="Trace", show_lines=False, border_style="dim")
    table.add_column("Step", style="bold")
    table.add_column("Duration", justify="right")
    table.add_column("Tool Calls", justify="right")
    for entry in trace:
        table.add_row(entry.step, f"{entry.duration_s:.1f}s", str(entry.tool_call_count))

    summary = Text()
    summary.append("Task: ", style="bold")
    summary.append(values.get("task", ""))
    summary.append("\n")
    summary.append("Steps: ", style="bold")
    summary.append(str(len(trace)))
    summary.append("\n")
    summary.append("Total: ", style="bold")
    summary.append(f"{total:.1f}s")

    grid = Table.grid(padding=(1, 0))
    grid.add_row(summary)
    grid.add_row(table)

    _console.print()
    _console.print(Panel(grid, title="[bold]Workflow Summary[/bold]", border_style="blue"))
    _console.print()
