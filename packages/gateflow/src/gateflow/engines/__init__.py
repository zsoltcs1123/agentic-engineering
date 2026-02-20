from typing import Literal, Protocol, runtime_checkable

from gateflow.models import EngineResult

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
