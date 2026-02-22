from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gateflow import DomainPack


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


_ALL_STEPS = [
    _make_step("plan"),
    _make_step("execute"),
    _make_step("review", gate=True),
    _make_step("verify", gate=True),
    _make_step("document"),
    _make_step("finalize"),
]


@pytest.mark.unit
class TestTrustLevelResolution:
    def test_autonomous_produces_no_interrupts(self, tmp_path: Path) -> None:
        _write_domain_pack(tmp_path, _ALL_STEPS, interrupts={"trust_level": "autonomous"})
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == []

    def test_gates_only_interrupts_at_review_and_verify(self, tmp_path: Path) -> None:
        _write_domain_pack(tmp_path, _ALL_STEPS, interrupts={"trust_level": "gates_only"})
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == ["review", "verify"]

    def test_review_all_interrupts_at_plan_execute_review_verify(self, tmp_path: Path) -> None:
        _write_domain_pack(tmp_path, _ALL_STEPS, interrupts={"trust_level": "review_all"})
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == ["plan", "execute", "review", "verify"]

    def test_cautious_interrupts_at_every_step(self, tmp_path: Path) -> None:
        _write_domain_pack(tmp_path, _ALL_STEPS, interrupts={"trust_level": "cautious"})
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == [
            "plan",
            "execute",
            "review",
            "verify",
            "document",
            "finalize",
        ]

    def test_default_is_autonomous_when_interrupts_absent(self, tmp_path: Path) -> None:
        _write_domain_pack(tmp_path, _ALL_STEPS)
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == []


@pytest.mark.unit
class TestInterruptOverrides:
    def test_add_extends_base_set(self, tmp_path: Path) -> None:
        _write_domain_pack(
            tmp_path,
            _ALL_STEPS,
            interrupts={"trust_level": "gates_only", "add": ["plan"]},
        )
        pack = DomainPack.load(tmp_path)

        result = pack.interrupt_after_steps()
        assert "plan" in result
        assert "review" in result
        assert "verify" in result

    def test_remove_shrinks_base_set(self, tmp_path: Path) -> None:
        _write_domain_pack(
            tmp_path,
            _ALL_STEPS,
            interrupts={"trust_level": "cautious", "remove": ["finalize"]},
        )
        pack = DomainPack.load(tmp_path)

        result = pack.interrupt_after_steps()
        assert "finalize" not in result
        assert "plan" in result

    def test_add_and_remove_together(self, tmp_path: Path) -> None:
        _write_domain_pack(
            tmp_path,
            _ALL_STEPS,
            interrupts={"trust_level": "gates_only", "add": ["plan"], "remove": ["review"]},
        )
        pack = DomainPack.load(tmp_path)

        result = pack.interrupt_after_steps()
        assert result == ["plan", "verify"]

    def test_ignores_steps_not_in_domain(self, tmp_path: Path) -> None:
        small_steps = [_make_step("plan"), _make_step("execute")]
        _write_domain_pack(
            tmp_path,
            small_steps,
            interrupts={"trust_level": "cautious"},
        )
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == ["plan", "execute"]

    def test_add_nonexistent_step_ignored(self, tmp_path: Path) -> None:
        small_steps = [_make_step("plan"), _make_step("execute")]
        _write_domain_pack(
            tmp_path,
            small_steps,
            interrupts={"trust_level": "autonomous", "add": ["nonexistent"]},
        )
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == []

    def test_preserves_step_order(self, tmp_path: Path) -> None:
        steps = [_make_step("finalize"), _make_step("plan"), _make_step("review", gate=True)]
        _write_domain_pack(
            tmp_path,
            steps,
            interrupts={"trust_level": "cautious"},
        )
        pack = DomainPack.load(tmp_path)

        assert pack.interrupt_after_steps() == ["finalize", "plan", "review"]


@pytest.mark.unit
class TestInterruptConfigValidation:
    def test_rejects_invalid_trust_level(self, tmp_path: Path) -> None:
        steps = [_make_step("plan")]
        config = {
            "name": "test",
            "steps": steps,
            "engine": {"default": "raw-llm"},
            "interrupts": {"trust_level": "yolo"},
        }
        root = tmp_path / "pack"
        root.mkdir(parents=True)
        (root / "domain.json").write_text(json.dumps(config), encoding="utf-8")
        (root / "prompts").mkdir()
        (root / "prompts" / "plan.md").write_text("p", encoding="utf-8")

        with pytest.raises(Exception, match="Invalid config"):
            DomainPack.load(root)
