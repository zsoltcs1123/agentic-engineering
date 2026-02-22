from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.runnables import RunnableConfig

from gateflow import DomainPack, build_graph, create_checkpointer
from gateflow.models import EngineResult, GateDecision

_SOFTWARE_DEV_PACK = Path(__file__).resolve().parents[2] / "domain_packs" / "software-dev"

_STEP_NAMES = ["plan", "execute", "review", "verify", "document", "finalize"]

_GATE_PASS = GateDecision(verdict="PASS", reasoning="ok", evidence=["looks good"], blind_spots=[])

_GATE_ISSUES = GateDecision(
    verdict="ISSUES",
    reasoning="bug found",
    evidence=["failing test"],
    blind_spots=[],
    issues=["bug found"],
)


def _result(output: str = "stub") -> EngineResult:
    return EngineResult(
        output=output,
        token_usage={"input_tokens": 10, "output_tokens": 5},
        duration_s=0.1,
    )


def _all_pass_responses() -> list[EngineResult]:
    responses: list[EngineResult] = []
    for name in _STEP_NAMES:
        if name in ("review", "verify"):
            responses.append(_result(_GATE_PASS.model_dump_json()))
        else:
            responses.append(_result(f"{name}-output"))
    return responses


def _issues_at_review_responses() -> list[EngineResult]:
    return [
        _result("plan-output"),
        _result("execute-output"),
        _result(_GATE_ISSUES.model_dump_json()),
    ]


def _make_engine(responses: list[EngineResult]) -> AsyncMock:
    engine = AsyncMock()
    engine.run = AsyncMock(side_effect=responses)
    return engine


def _base_input() -> dict[str, Any]:
    return {
        "task_id": "e2e-001",
        "task_description": "E2E test task",
        "working_directory": "/tmp/e2e",
        "current_step": "",
        "status": "running",
        "plan": "",
        "review_result": "",
        "verification_result": "",
        "gate_verdict": "",
        "trace": [],
        "domain_data": {},
    }


def _thread_config(thread_id: str) -> RunnableConfig:
    return RunnableConfig(configurable={"thread_id": thread_id})


@pytest.mark.integration
class TestFullCompletion:
    @pytest.mark.asyncio
    async def test_all_gates_pass_produces_completed_state(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_all_pass_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("full-run"))

            assert result["current_step"] == "finalize"
            assert len(result["trace"]) == len(_STEP_NAMES)
            executed = [entry["step"] for entry in result["trace"]]
            assert executed == _STEP_NAMES
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_all_state_fields_populated_after_full_run(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_all_pass_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("fields-run"))

            assert result["plan"] == "plan-output"
            assert result["review_result"] != ""
            assert result["verification_result"] != ""
            assert "execute" in result["domain_data"]
            assert "document" in result["domain_data"]
            assert "finalize" in result["domain_data"]
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestGateHalt:
    @pytest.mark.asyncio
    async def test_issues_at_review_halts_execution(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_issues_at_review_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("halt-run"))

            assert result["gate_verdict"] == "ISSUES"
            assert len(result["trace"]) == 3
            executed = [entry["step"] for entry in result["trace"]]
            assert executed == ["plan", "execute", "review"]
            assert engine.run.call_count == 3
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_steps_after_halted_gate_not_executed(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_issues_at_review_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("halt-verify"))

            assert result["verification_result"] == ""
            assert "document" not in result.get("domain_data", {})
            assert "finalize" not in result.get("domain_data", {})
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestCheckpointResume:
    @pytest.mark.asyncio
    async def test_resume_completed_thread_does_not_rerun(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_all_pass_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)
            thread = _thread_config("resume-thread")

            await graph.ainvoke(_base_input(), thread)
            calls_after_first = engine.run.call_count

            await graph.ainvoke(None, thread)

            assert engine.run.call_count == calls_after_first
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_resume_preserves_state_from_first_run(self, tmp_path: Path) -> None:
        domain = DomainPack.load(_SOFTWARE_DEV_PACK)
        checkpointer = await create_checkpointer(str(tmp_path / "e2e.db"))
        try:
            engine = _make_engine(_all_pass_responses())
            graph = build_graph(domain, {"cursor-cli": engine}, checkpointer=checkpointer)
            thread = _thread_config("preserve-thread")

            await graph.ainvoke(_base_input(), thread)
            state_before = await graph.aget_state(thread)

            await graph.ainvoke(None, thread)
            state_after = await graph.aget_state(thread)

            assert state_after.values["plan"] == state_before.values["plan"]
            assert state_after.values["trace"] == state_before.values["trace"]
            assert state_after.values["task_id"] == "e2e-001"
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestOrchestratorDomainAgnostic:
    def test_orchestrator_source_has_no_domain_specific_strings(self) -> None:
        orchestrator_dir = Path(__file__).resolve().parents[2] / "src" / "gateflow"
        source_files = [
            orchestrator_dir / "graph.py",
            orchestrator_dir / "nodes.py",
            orchestrator_dir / "state.py",
            orchestrator_dir / "models.py",
            orchestrator_dir / "checkpointer.py",
        ]
        forbidden = ["software-dev", "cursor-cli", "raw-llm", "anthropic"]
        for src_file in source_files:
            content = src_file.read_text(encoding="utf-8")
            for term in forbidden:
                assert term not in content, (
                    f"Orchestrator file {src_file.name} contains domain-specific string '{term}'"
                )
