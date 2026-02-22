from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.runnables import RunnableConfig

from gateflow import DomainPack, build_graph, create_checkpointer
from gateflow.models import EngineResult


def _make_step(name: str, *, gate: bool = False) -> dict[str, Any]:
    return {"name": name, "prompt": name, "gate": gate}


def _write_domain_pack(
    root: Path,
    steps: list[dict[str, Any]],
    *,
    interrupts: dict[str, Any] | None = None,
) -> Path:
    config: dict[str, Any] = {
        "name": "test-domain",
        "steps": steps,
        "engine": {"default": "raw-llm"},
    }
    if interrupts is not None:
        config["interrupts"] = interrupts
    root.mkdir(parents=True, exist_ok=True)
    (root / "domain.json").write_text(json.dumps(config), encoding="utf-8")
    prompts_dir = root / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for s in steps:
        (prompts_dir / f"{s['prompt']}.md").write_text(f"Prompt for {s['name']}.", encoding="utf-8")
    return root


def _make_engine(responses: list[EngineResult] | None = None) -> AsyncMock:
    engine = AsyncMock()
    if responses:
        engine.run = AsyncMock(side_effect=responses)
    else:
        engine.run = AsyncMock(
            return_value=EngineResult(
                output="stub", token_usage={"input_tokens": 10, "output_tokens": 5}, duration_s=0.1
            )
        )
    return engine


def _result(output: str = "stub") -> EngineResult:
    return EngineResult(
        output=output, token_usage={"input_tokens": 10, "output_tokens": 5}, duration_s=0.1
    )


def _base_input() -> dict[str, Any]:
    return {
        "task_id": "int-001",
        "task_description": "Interrupt test",
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


def _thread(thread_id: str) -> RunnableConfig:
    return RunnableConfig(configurable={"thread_id": thread_id})


@pytest.mark.integration
class TestInterruptPause:
    @pytest.mark.asyncio
    async def test_gates_only_pauses_at_review_not_plan(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("review", gate=False), _make_step("finalize")]
        _write_domain_pack(
            tmp_path / "pack",
            steps,
            interrupts={"trust_level": "gates_only"},
        )
        domain = DomainPack.load(tmp_path / "pack")
        checkpointer = await create_checkpointer(str(tmp_path / "test.db"))
        try:
            engine = _make_engine(
                [_result("plan-out"), _result("review-out"), _result("final-out")]
            )
            graph = build_graph(domain, {"raw-llm": engine}, checkpointer=checkpointer)
            cfg = _thread("pause-test")

            await graph.ainvoke(_base_input(), cfg)

            state = await graph.aget_state(cfg)
            assert state.next == ("finalize",)
            assert engine.run.call_count == 2
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_autonomous_runs_to_completion(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("execute"), _make_step("finalize")]
        _write_domain_pack(
            tmp_path / "pack",
            steps,
            interrupts={"trust_level": "autonomous"},
        )
        domain = DomainPack.load(tmp_path / "pack")
        checkpointer = await create_checkpointer(str(tmp_path / "test.db"))
        try:
            engine = _make_engine([_result("p"), _result("e"), _result("f")])
            graph = build_graph(domain, {"raw-llm": engine}, checkpointer=checkpointer)
            cfg = _thread("auto-test")

            result = await graph.ainvoke(_base_input(), cfg)

            assert result["current_step"] == "finalize"
            assert len(result["trace"]) == 3
            assert engine.run.call_count == 3
        finally:
            await checkpointer.conn.close()


@pytest.mark.integration
class TestInterruptResume:
    @pytest.mark.asyncio
    async def test_resume_after_interrupt_continues_from_correct_step(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("execute"), _make_step("finalize")]
        _write_domain_pack(
            tmp_path / "pack",
            steps,
            interrupts={"trust_level": "cautious"},
        )
        domain = DomainPack.load(tmp_path / "pack")
        checkpointer = await create_checkpointer(str(tmp_path / "test.db"))
        try:
            engine = _make_engine([_result("plan-out"), _result("exec-out"), _result("final-out")])
            graph = build_graph(domain, {"raw-llm": engine}, checkpointer=checkpointer)
            cfg = _thread("resume-test")

            await graph.ainvoke(_base_input(), cfg)
            assert engine.run.call_count == 1

            state = await graph.aget_state(cfg)
            assert state.values["current_step"] == "plan"

            await graph.ainvoke(None, cfg)
            assert engine.run.call_count == 2

            await graph.ainvoke(None, cfg)
            assert engine.run.call_count == 3

            state = await graph.aget_state(cfg)
            assert state.values["current_step"] == "finalize"
            assert len(state.values["trace"]) == 3
        finally:
            await checkpointer.conn.close()

    @pytest.mark.asyncio
    async def test_earlier_results_preserved_after_resume(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("execute")]
        _write_domain_pack(
            tmp_path / "pack",
            steps,
            interrupts={"trust_level": "cautious"},
        )
        domain = DomainPack.load(tmp_path / "pack")
        checkpointer = await create_checkpointer(str(tmp_path / "test.db"))
        try:
            engine = _make_engine([_result("my-plan"), _result("exec-out")])
            graph = build_graph(domain, {"raw-llm": engine}, checkpointer=checkpointer)
            cfg = _thread("preserve-test")

            await graph.ainvoke(_base_input(), cfg)

            state_after_plan = await graph.aget_state(cfg)
            assert state_after_plan.values["plan"] == "my-plan"

            await graph.ainvoke(None, cfg)

            state_final = await graph.aget_state(cfg)
            assert state_final.values["plan"] == "my-plan"
        finally:
            await checkpointer.conn.close()
