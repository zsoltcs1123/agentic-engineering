from typing import Literal, Protocol, runtime_checkable

from gateflow.engines.raw_llm import RawLLMEngine
from gateflow.models import EngineError, EngineResult

PermissionMode = Literal["readonly", "acceptEdits", "default"]


@runtime_checkable
class ExecutionEngine(Protocol):
    async def run(
        self,
        prompt: str,
        working_directory: str,
        allowed_tools: list[str],
        permission_mode: PermissionMode,
    ) -> EngineResult: ...


__all__ = [
    "EngineError",
    "ExecutionEngine",
    "PermissionMode",
    "RawLLMEngine",
]
