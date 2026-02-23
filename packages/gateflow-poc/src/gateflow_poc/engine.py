from __future__ import annotations

import asyncio
import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

PermissionMode = Literal["readonly", "acceptEdits", "default"]


@dataclass
class EngineResult:
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    duration_s: float = 0.0


class EngineError(Exception):
    pass


def _extract_tool_name(tool_call_data: dict[str, Any]) -> str:
    for key in tool_call_data:
        if key.endswith("ToolCall"):
            return key.removesuffix("ToolCall")
    return "unknown"


def _parse_events(raw_lines: list[str]) -> tuple[str, list[dict[str, Any]], float]:
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    duration_s: float = 0.0
    pending_tools: dict[str, dict[str, Any]] = {}

    for raw in raw_lines:
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))

        elif event_type == "tool_call":
            subtype = event.get("subtype")
            tc_data = event.get("tool_call", {})
            tool_name = _extract_tool_name(tc_data)
            tool_key = tc_data.get(f"{tool_name}ToolCall", {})

            if subtype == "started":
                entry: dict[str, Any] = {
                    "tool": tool_name,
                    "args": tool_key.get("args", {}),
                }
                pending_tools[tool_name] = entry
                tool_calls.append(entry)
            elif subtype == "completed" and tool_name in pending_tools:
                result_data = tool_key.get("result", {})
                pending_tools[tool_name]["result"] = result_data
                del pending_tools[tool_name]

        elif event_type == "result":
            duration_ms = event.get("duration_ms", 0)
            duration_s = duration_ms / 1000.0

    return "".join(text_parts), tool_calls, duration_s


class CursorCLI:
    def __init__(self, *, agent_path: str = "agent", model: str | None = None) -> None:
        resolved = shutil.which(agent_path)
        if resolved is None:
            raise EngineError(f"Cursor CLI '{agent_path}' not found on PATH")
        self._agent_path = resolved
        self._model = model

    def _build_args(self, mode: PermissionMode) -> list[str]:
        args = [self._agent_path, "-p", "--output-format", "stream-json"]
        if mode == "acceptEdits":
            args.append("--force")
        elif mode == "readonly":
            args.extend(["--mode", "ask"])
        if self._model:
            args.extend(["--model", self._model])
        return args

    async def run(
        self,
        prompt: str,
        *,
        working_directory: str,
        mode: PermissionMode = "readonly",
        step_name: str = "unknown",
    ) -> EngineResult:
        args = self._build_args(mode)

        log_dir = Path(working_directory) / ".gateflow-poc" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = log_dir / f"{step_name}-prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        print(f"\n--- [{step_name}] prompt ({len(prompt)} chars, mode={mode}) ---")
        print(prompt)
        print(f"--- /{step_name} ---\n")

        start = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=working_directory,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await proc.communicate(input=prompt.encode("utf-8"))
        except FileNotFoundError as exc:
            raise EngineError(f"Cursor CLI not found at '{self._agent_path}': {exc}") from exc
        except OSError as exc:
            raise EngineError(f"Failed to start Cursor CLI: {exc}") from exc
        fallback_duration = time.monotonic() - start

        stdout_text = stdout_bytes.decode(errors="replace")
        stderr_text = stderr_bytes.decode(errors="replace").strip()

        raw_out_file = log_dir / f"{step_name}-raw-stdout.txt"
        raw_out_file.write_text(stdout_text, encoding="utf-8")
        if stderr_text:
            raw_err_file = log_dir / f"{step_name}-raw-stderr.txt"
            raw_err_file.write_text(stderr_text, encoding="utf-8")

        print(f"[{step_name}] exit={proc.returncode or 0} duration={fallback_duration:.1f}s")

        if proc.returncode != 0:
            raise EngineError(f"Cursor CLI exited with code {proc.returncode}: {stderr_text}")

        raw_lines = stdout_text.splitlines()
        output, tool_calls, duration_s = _parse_events(raw_lines)

        print(f"[{step_name}] output={len(output)} chars, tool_calls={len(tool_calls)}")

        return EngineResult(
            output=output,
            tool_calls=tool_calls,
            duration_s=duration_s or fallback_duration,
        )
