from __future__ import annotations

import asyncio
import shutil
import time

from agentflow.engine.parsing import parse_events
from agentflow.engine.types import EngineError, EngineResult, PermissionMode


class CursorCLI:
    def __init__(self, *, agent_path: str = "agent", model: str | None = None) -> None:
        resolved = shutil.which(agent_path)
        if resolved is None:
            raise EngineError(f"Cursor CLI '{agent_path}' not found on PATH")
        self._agent_path = resolved
        self._model = model

    async def run(
        self,
        prompt: str,
        *,
        working_directory: str,
        mode: PermissionMode = "readonly",
    ) -> EngineResult:
        args = self._build_args(mode)
        stdout_text, elapsed = await self._execute(args, prompt, working_directory)
        return self._parse_output(stdout_text, elapsed)

    def _build_args(self, mode: PermissionMode) -> list[str]:
        args = [self._agent_path, "-p", "--output-format", "stream-json"]
        if mode == "acceptEdits":
            args.append("--force")
        elif mode == "readonly":
            args.extend(["--mode", "ask"])
        if self._model:
            args.extend(["--model", self._model])
        return args

    async def _execute(
        self, args: list[str], prompt: str, working_directory: str
    ) -> tuple[str, float]:
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
        elapsed = time.monotonic() - start

        if proc.returncode != 0:
            stderr_text = stderr_bytes.decode(errors="replace").strip()
            raise EngineError(f"Cursor CLI exited with code {proc.returncode}: {stderr_text}")

        return stdout_bytes.decode(errors="replace"), elapsed

    def _parse_output(self, stdout_text: str, elapsed: float) -> EngineResult:
        output, tool_calls, duration_s = parse_events(stdout_text.splitlines())
        return EngineResult(
            output=output,
            tool_calls=tool_calls,
            duration_s=duration_s or elapsed,
        )
