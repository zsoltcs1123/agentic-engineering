from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from gateflow import DomainPack, build_graph
from gateflow.graph import gate_router
from gateflow.models import EngineResult


def _mock_engines() -> dict[str, AsyncMock]:
    engine = AsyncMock()
    engine.run = AsyncMock(return_value=EngineResult(output="stub"))
    return {"raw-llm": engine}


def _make_step(name: str, *, gate: bool = False, readonly: bool = False) -> dict[str, Any]:
    return {"name": name, "prompt": name, "gate": gate, "readonly": readonly}


def _write_domain_pack(
    root: Path,
    steps: list[dict[str, Any]],
) -> Path:
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


def _node_names(graph: Any) -> set[str]:
    drawable = graph.get_graph()
    return {n.name for n in drawable.nodes.values()} - {"__start__", "__end__"}


def _edges_from(graph: Any, source: str) -> list[dict[str, Any]]:
    drawable = graph.get_graph()
    return [
        {"target": e.target, "conditional": e.conditional}
        for e in drawable.edges
        if e.source == source
    ]


@pytest.mark.unit
class TestBuildGraphTopology:
    def test_three_steps_with_one_gate(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("review", gate=True), _make_step("execute")]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        compiled = build_graph(domain, _mock_engines())

        assert _node_names(compiled) == {"plan", "review", "execute"}

        plan_edges = _edges_from(compiled, "plan")
        assert len(plan_edges) == 1
        assert plan_edges[0]["target"] == "review"
        assert plan_edges[0]["conditional"] is False

        review_edges = _edges_from(compiled, "review")
        assert len(review_edges) == 2
        targets = {e["target"] for e in review_edges}
        assert targets == {"execute", "__end__"}
        assert all(e["conditional"] for e in review_edges)

    def test_single_step_domain(self, tmp_path: Path) -> None:
        steps = [_make_step("plan")]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        compiled = build_graph(domain, _mock_engines())

        assert _node_names(compiled) == {"plan"}
        plan_edges = _edges_from(compiled, "plan")
        assert len(plan_edges) == 1
        assert plan_edges[0]["target"] == "__end__"

    def test_two_consecutive_gate_steps(self, tmp_path: Path) -> None:
        steps = [
            _make_step("review", gate=True),
            _make_step("verify", gate=True),
            _make_step("finalize"),
        ]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        compiled = build_graph(domain, _mock_engines())

        review_edges = _edges_from(compiled, "review")
        assert len(review_edges) == 2
        assert {e["target"] for e in review_edges} == {"verify", "__end__"}
        assert all(e["conditional"] for e in review_edges)

        verify_edges = _edges_from(compiled, "verify")
        assert len(verify_edges) == 2
        assert {e["target"] for e in verify_edges} == {"finalize", "__end__"}
        assert all(e["conditional"] for e in verify_edges)

    def test_compiles_without_errors(self, tmp_path: Path) -> None:
        steps = [
            _make_step("plan"),
            _make_step("execute"),
            _make_step("review", gate=True),
            _make_step("verify", gate=True),
            _make_step("document"),
            _make_step("finalize"),
        ]
        _write_domain_pack(tmp_path / "pack", steps)
        domain = DomainPack.load(tmp_path / "pack")

        compiled = build_graph(domain, _mock_engines())

        assert compiled is not None


@pytest.mark.unit
class TestGateRouter:
    def test_returns_pass_when_verdict_is_pass(self) -> None:
        state = {"gate_verdict": "PASS"}
        assert gate_router(state) == "pass"  # type: ignore[arg-type]

    def test_returns_issues_when_verdict_is_issues(self) -> None:
        state = {"gate_verdict": "ISSUES"}
        assert gate_router(state) == "issues"  # type: ignore[arg-type]

    def test_defaults_to_pass_when_verdict_missing(self) -> None:
        state: dict[str, Any] = {}
        assert gate_router(state) == "pass"  # type: ignore[arg-type]
