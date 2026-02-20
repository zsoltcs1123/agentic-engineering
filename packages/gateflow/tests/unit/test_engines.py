import pytest

from gateflow.engines import ExecutionEngine, PermissionMode
from gateflow.models import EngineResult


class _ConformingEngine:
    async def run(
        self,
        prompt: str,
        working_directory: str,
        allowed_tools: list[str],
        permission_mode: PermissionMode,
    ) -> EngineResult:
        return EngineResult(output="ok")


class _NonConformingEngine:
    pass


@pytest.mark.unit
def test_conforming_class_recognised_as_execution_engine():
    assert isinstance(_ConformingEngine(), ExecutionEngine)


@pytest.mark.unit
def test_non_conforming_class_not_recognised_as_execution_engine():
    assert not isinstance(_NonConformingEngine(), ExecutionEngine)
