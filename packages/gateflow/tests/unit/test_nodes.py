from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from gateflow.domain import DomainPack, StepDefinition
from gateflow.models import EngineResult, GateDecision
from gateflow.nodes import inject_state, make_node


def _make_step(
    name: str, *, gate: bool = False, readonly: bool = False, tools: list[str] | None = None
) -> StepDefinition:
    return StepDefinition(name=name, prompt=name, gate=gate, readonly=readonly, tools=tools or [])


def _make_engine(*, output: str = "done", token_usage: dict[str, Any] | None = None) -> AsyncMock:
    result = EngineResult(
        output=output,
        token_usage=token_usage or {"input_tokens": 10, "output_tokens": 5},
        duration_s=0.42,
    )
    engine = AsyncMock()
    engine.run = AsyncMock(return_value=result)
    return engine


def _write_domain_pack(
    root: Path,
    steps: list[dict[str, Any]],
    *,
    rules: dict[str, list[str]] | None = None,
    rule_files: dict[str, str] | None = None,
) -> Path:
    config: dict[str, Any] = {
        "name": "test-domain",
        "steps": steps,
        "engine": {"default": "mock"},
    }
    if rules:
        config["rules"] = rules

    root.mkdir(parents=True, exist_ok=True)
    (root / "domain.json").write_text(json.dumps(config), encoding="utf-8")

    prompts_dir = root / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for s in steps:
        (prompts_dir / f"{s['prompt']}.md").write_text(f"Prompt for {s['name']}.", encoding="utf-8")

    if rule_files:
        rules_dir = root / "rules"
        rules_dir.mkdir(exist_ok=True)
        for name, text in rule_files.items():
            (rules_dir / f"{name}.md").write_text(text, encoding="utf-8")

    return root


def _base_state(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "task_id": "t-001",
        "task_description": "Implement feature X",
        "working_directory": "/workspace",
        "current_step": "",
        "status": "running",
        "plan": "Step 1: do A. Step 2: do B.",
        "review_result": "",
        "verification_result": "",
        "gate_verdict": "",
        "trace": [],
        "domain_data": {},
    }
    defaults.update(overrides)
    return defaults


@pytest.mark.unit
class TestInjectState:
    def test_injects_task_description_and_working_directory(self) -> None:
        state = _base_state()
        result = inject_state("Base prompt.", state)

        assert "Base prompt." in result
        assert "Implement feature X" in result
        assert "/workspace" in result

    def test_injects_plan(self) -> None:
        state = _base_state()
        result = inject_state("Base prompt.", state)

        assert "Step 1: do A" in result

    def test_injects_domain_data(self) -> None:
        state = _base_state(domain_data={"key": "value"})
        result = inject_state("Base prompt.", state)

        assert '"key": "value"' in result

    def test_skips_empty_fields(self) -> None:
        state = _base_state(task_description="", plan="", domain_data={})
        result = inject_state("Base prompt.", state)

        assert "**Task:**" not in result
        assert "**Plan:**" not in result
        assert "**Domain Data:**" not in result

    def test_returns_prompt_unchanged_when_all_fields_empty(self) -> None:
        state = _base_state(task_description="", plan="", working_directory="", domain_data={})
        result = inject_state("Base prompt.", state)

        assert result == "Base prompt."


@pytest.mark.unit
class TestMakeNodePromptAssembly:
    @pytest.mark.asyncio
    async def test_prompt_contains_base_text_and_injected_state(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("plan")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        await node_fn(state)

        prompt_sent = engine.run.call_args.kwargs["prompt"]
        assert "Prompt for plan." in prompt_sent
        assert "Implement feature X" in prompt_sent
        assert "/workspace" in prompt_sent

    @pytest.mark.asyncio
    async def test_forwards_tools_to_engine(self, tmp_path: Path) -> None:
        steps = [{"name": "execute", "prompt": "execute"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("execute", tools=["Read", "Edit"])
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        await node_fn(state)

        assert engine.run.call_args.kwargs["allowed_tools"] == ["Read", "Edit"]

    @pytest.mark.asyncio
    async def test_readonly_step_sends_readonly_permission(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("plan", readonly=True)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        await node_fn(state)

        assert engine.run.call_args.kwargs["permission_mode"] == "readonly"

    @pytest.mark.asyncio
    async def test_non_readonly_step_sends_accept_edits_permission(self, tmp_path: Path) -> None:
        steps = [{"name": "execute", "prompt": "execute"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("execute", readonly=False)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        await node_fn(state)

        assert engine.run.call_args.kwargs["permission_mode"] == "acceptEdits"


@pytest.mark.unit
class TestMakeNodeStateUpdate:
    @pytest.mark.asyncio
    async def test_plan_step_writes_to_plan_field(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output="The plan is X.")
        step = _make_step("plan")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["plan"] == "The plan is X."

    @pytest.mark.asyncio
    async def test_review_step_writes_to_review_result_field(self, tmp_path: Path) -> None:
        decision = GateDecision(
            verdict="PASS", reasoning="ok", evidence=["all good"], blind_spots=[]
        )
        steps = [{"name": "review", "prompt": "review", "gate": True}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output=decision.model_dump_json())
        step = _make_step("review", gate=True)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["review_result"] == decision.model_dump_json()

    @pytest.mark.asyncio
    async def test_verify_step_writes_to_verification_result_field(self, tmp_path: Path) -> None:
        steps = [{"name": "verify", "prompt": "verify"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output="Verified OK.")
        step = _make_step("verify")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["verification_result"] == "Verified OK."

    @pytest.mark.asyncio
    async def test_unknown_step_writes_to_domain_data(self, tmp_path: Path) -> None:
        steps = [{"name": "finalize", "prompt": "finalize"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output="Finalized.")
        step = _make_step("finalize")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["domain_data"]["finalize"] == "Finalized."

    @pytest.mark.asyncio
    async def test_sets_current_step(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("plan")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["current_step"] == "plan"


@pytest.mark.unit
class TestMakeNodeGateDecision:
    @pytest.mark.asyncio
    async def test_gate_pass_sets_verdict(self, tmp_path: Path) -> None:
        decision = GateDecision(
            verdict="PASS", reasoning="looks good", evidence=["tests pass"], blind_spots=[]
        )
        steps = [{"name": "review", "prompt": "review", "gate": True}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output=decision.model_dump_json())
        step = _make_step("review", gate=True)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["gate_verdict"] == "PASS"

    @pytest.mark.asyncio
    async def test_gate_issues_sets_verdict_and_stores_decision(self, tmp_path: Path) -> None:
        decision = GateDecision(
            verdict="ISSUES",
            reasoning="found problems",
            evidence=["lint errors"],
            blind_spots=[],
            issues=["missing import"],
        )
        steps = [{"name": "review", "prompt": "review", "gate": True}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output=decision.model_dump_json())
        step = _make_step("review", gate=True)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["gate_verdict"] == "ISSUES"
        stored = json.loads(update["review_result"])
        assert stored["issues"] == ["missing import"]

    @pytest.mark.asyncio
    async def test_gate_unparseable_output_fails_safe_to_issues(self, tmp_path: Path) -> None:
        steps = [{"name": "review", "prompt": "review", "gate": True}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(output="not valid json at all")
        step = _make_step("review", gate=True)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert update["gate_verdict"] == "ISSUES"
        stored = json.loads(update["review_result"])
        assert any("Parse error" in issue for issue in stored["issues"])

    @pytest.mark.asyncio
    async def test_non_gate_step_does_not_set_verdict(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine()
        step = _make_step("plan", gate=False)
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert "gate_verdict" not in update


@pytest.mark.unit
class TestMakeNodeTrace:
    @pytest.mark.asyncio
    async def test_appends_trace_entry(self, tmp_path: Path) -> None:
        steps = [{"name": "plan", "prompt": "plan"}]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")
        engine = _make_engine(
            output="planned", token_usage={"input_tokens": 20, "output_tokens": 10}
        )
        step = _make_step("plan")
        state = _base_state()

        node_fn = make_node(step, domain, engine)
        update = await node_fn(state)

        assert len(update["trace"]) == 1
        entry = update["trace"][0]
        assert entry["step"] == "plan"
        assert entry["output"] == "planned"
        assert entry["token_usage"] == {"input_tokens": 20, "output_tokens": 10}
        assert entry["duration_s"] == pytest.approx(0.42)

    @pytest.mark.asyncio
    async def test_three_sequential_nodes_produce_three_trace_entries(self, tmp_path: Path) -> None:
        step_defs = [
            {"name": "plan", "prompt": "plan"},
            {"name": "execute", "prompt": "execute"},
            {"name": "finalize", "prompt": "finalize"},
        ]
        _write_domain_pack(tmp_path / "pack", step_defs)
        domain = DomainPack.load(tmp_path / "pack")

        all_traces: list[dict[str, Any]] = []
        for step_dict in step_defs:
            engine = _make_engine(output=f"output-{step_dict['name']}")
            step = _make_step(step_dict["name"])
            state = _base_state(trace=list(all_traces))

            node_fn = make_node(step, domain, engine)
            update = await node_fn(state)
            all_traces.extend(update["trace"])

        assert len(all_traces) == 3
        assert [e["step"] for e in all_traces] == ["plan", "execute", "finalize"]
