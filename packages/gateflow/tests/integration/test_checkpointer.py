from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from gateflow import DomainPack, build_graph, create_checkpointer
from gateflow.models import EngineResult, GateDecision


def _make_step(name: str, *, gate: bool = False) -> dict[str, Any]:
    return {"name": name, "prompt": name, "gate": gate}


def _write_domain_pack(root: Path, steps: list[dict[str, Any]]) -> Path:
    config = {
        "name": "test-domain",
        "steps": steps,
        "engine": {"default": "raw-llm"},
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "domain.json").write_text(json.dumps(config), encoding="utf-8")
    prompts_dir = root / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for s in steps:
        (prompts_dir / f"{s['prompt']}.md").write_text(f"Prompt for {s['name']}.", encoding="utf-8")
    return root


def _make_engine(output: str = "stub") -> AsyncMock:
    engine = AsyncMock()
    engine.run = AsyncMock(
        return_value=EngineResult(
            output=output,
            token_usage={"input_tokens": 10, "output_tokens": 5},
            duration_s=0.1,
        )
    )
    return engine


def _gate_pass_engine() -> AsyncMock:
    decision = GateDecision(verdict="PASS", reasoning="ok", evidence=["all good"], blind_spots=[])
    return _make_engine(output=decision.model_dump_json())


def _base_input() -> dict[str, Any]:
    return {
        "task_id": "t-001",
        "task_description": "Test task",
        "working_directory": "/tmp/test",
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
class TestCheckpointerRunToCompletion:
    @pytest.mark.asyncio
    async def test_checkpoint_db_exists_after_run(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("execute"), _make_step("finalize")]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _make_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)

            await graph.ainvoke(_base_input(), _thread_config("thread-1"))

            db_file = Path(db_path)
            assert db_file.exists()
            assert db_file.stat().st_size > 0
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_all_steps_execute_with_checkpointer(self, tmp_path: Path) -> None:
        steps = [
            _make_step("plan"),
            _make_step("review", gate=True),
            _make_step("finalize"),
        ]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _gate_pass_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("thread-1"))

            assert result["current_step"] == "finalize"
            assert len(result["trace"]) == 3
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestCheckpointerResume:
    @pytest.mark.asyncio
    async def test_resume_continues_from_interrupt_point(self, tmp_path: Path) -> None:
        steps = [
            _make_step("plan"),
            _make_step("execute"),
            _make_step("review", gate=True),
            _make_step("finalize"),
        ]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _gate_pass_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)
            thread = _thread_config("thread-resume")

            await graph.ainvoke(_base_input(), thread)

            state = await graph.aget_state(thread)
            assert len(state.values["trace"]) == 4

            call_count_after_first_run = engines["raw-llm"].run.call_count

            await graph.ainvoke(None, thread)

            assert engines["raw-llm"].run.call_count == call_count_after_first_run
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_interrupt_and_resume_preserves_earlier_results(self, tmp_path: Path) -> None:
        steps = [
            _make_step("plan"),
            _make_step("execute"),
            _make_step("review", gate=True),
            _make_step("finalize"),
        ]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _gate_pass_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)
            thread = _thread_config("thread-interrupt")

            await graph.ainvoke(_base_input(), thread)

            state = await graph.aget_state(thread)
            assert state.values["plan"] != ""
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestCheckpointerNewThread:
    @pytest.mark.asyncio
    async def test_new_thread_starts_from_beginning(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("finalize")]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _make_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)

            result = await graph.ainvoke(_base_input(), _thread_config("new-thread"))

            assert len(result["trace"]) == 2
            assert result["current_step"] == "finalize"
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_separate_threads_have_independent_state(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("finalize")]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        db_path = str(tmp_path / "checkpoints.db")
        checkpointer = await create_checkpointer(db_path)
        try:
            engines = {"raw-llm": _make_engine()}
            graph = build_graph(domain, engines, checkpointer=checkpointer)

            input_a = _base_input()
            input_a["task_id"] = "task-a"
            input_b = _base_input()
            input_b["task_id"] = "task-b"

            await graph.ainvoke(input_a, _thread_config("thread-a"))
            await graph.ainvoke(input_b, _thread_config("thread-b"))

            state_a = await graph.aget_state(_thread_config("thread-a"))
            state_b = await graph.aget_state(_thread_config("thread-b"))
            assert state_a.values["task_id"] == "task-a"
            assert state_b.values["task_id"] == "task-b"
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestCreateCheckpointer:
    @pytest.mark.asyncio
    async def test_returns_async_sqlite_saver(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "test.db")
        saver = await create_checkpointer(db_path)
        try:
            assert isinstance(saver, AsyncSqliteSaver)
        finally:
            await saver.conn.close()
