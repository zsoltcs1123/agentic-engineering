from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gateflow import DomainPack, DomainPackError
from gateflow.domain import StepDefinition


def _make_step(name: str, *, gate: bool = False, readonly: bool = False) -> dict[str, Any]:
    return {"name": name, "prompt": name, "gate": gate, "readonly": readonly}


def _write_domain_pack(
    root: Path,
    *,
    config: dict[str, Any] | None = None,
    steps: list[dict[str, Any]] | None = None,
    prompts: dict[str, str] | None = None,
    rules: dict[str, str] | None = None,
) -> Path:
    if steps is None:
        steps = [_make_step("plan"), _make_step("execute")]
    if config is None:
        config = {
            "name": "test-domain",
            "steps": steps,
            "engine": {"default": "raw-llm"},
        }

    root.mkdir(parents=True, exist_ok=True)
    (root / "domain.json").write_text(json.dumps(config), encoding="utf-8")

    prompts_dir = root / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    if prompts is None:
        prompts = {s["prompt"]: f"Prompt for {s['name']}." for s in steps}
    for name, text in prompts.items():
        (prompts_dir / f"{name}.md").write_text(text, encoding="utf-8")

    if rules:
        rules_dir = root / "rules"
        rules_dir.mkdir(exist_ok=True)
        for name, text in rules.items():
            (rules_dir / f"{name}.md").write_text(text, encoding="utf-8")

    return root


@pytest.mark.unit
class TestLoad:
    def test_raises_when_config_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(DomainPackError, match="Missing config file"):
            DomainPack.load(tmp_path)

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "domain.json").write_text("not json{", encoding="utf-8")
        with pytest.raises(DomainPackError, match="Invalid JSON"):
            DomainPack.load(tmp_path)

    def test_raises_on_missing_required_fields(self, tmp_path: Path) -> None:
        (tmp_path / "domain.json").write_text('{"name": "x"}', encoding="utf-8")
        with pytest.raises(DomainPackError, match="Invalid config"):
            DomainPack.load(tmp_path)

    def test_raises_when_prompt_file_missing(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        steps = [_make_step("plan"), _make_step("execute")]
        _write_domain_pack(pack_dir, steps=steps, prompts={"plan": "p"})

        with pytest.raises(DomainPackError, match="Missing prompt file for step 'execute'"):
            DomainPack.load(pack_dir)

    def test_raises_when_referenced_rule_file_missing(self, tmp_path: Path) -> None:
        steps = [_make_step("plan")]
        config = {
            "name": "test",
            "steps": steps,
            "engine": {"default": "raw-llm"},
            "rules": {"plan": ["nonexistent"]},
        }
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir, config=config, steps=steps)

        with pytest.raises(DomainPackError, match="Missing rule file 'nonexistent'"):
            DomainPack.load(pack_dir)

    def test_loads_valid_pack(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir)

        pack = DomainPack.load(pack_dir)

        assert pack.name == "test-domain"
        assert pack.step_names == ["plan", "execute"]

    def test_loads_gate_flag(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("review", gate=True)]
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir, steps=steps)

        pack = DomainPack.load(pack_dir)

        assert pack.steps[0].gate is False
        assert pack.steps[1].gate is True


@pytest.mark.unit
class TestBuildPrompt:
    def test_returns_base_prompt_when_no_rules(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir, prompts={"plan": "Plan base.", "execute": "Exec."})
        pack = DomainPack.load(pack_dir)

        result = pack.build_prompt("plan")

        assert result == "Plan base."

    def test_concatenates_base_and_rule_texts(self, tmp_path: Path) -> None:
        steps = [_make_step("plan")]
        config = {
            "name": "test",
            "steps": steps,
            "engine": {"default": "raw-llm"},
            "rules": {"plan": ["python", "testing"]},
        }
        pack_dir = tmp_path / "pack"
        _write_domain_pack(
            pack_dir,
            config=config,
            steps=steps,
            prompts={"plan": "Base prompt."},
            rules={"python": "Python rules.", "testing": "Testing rules."},
        )
        pack = DomainPack.load(pack_dir)

        result = pack.build_prompt("plan")

        assert result == "Base prompt.\n\nPython rules.\n\nTesting rules."

    def test_raises_for_unknown_step(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir)
        pack = DomainPack.load(pack_dir)

        with pytest.raises(DomainPackError, match="Missing prompt file for step 'unknown'"):
            pack.build_prompt("unknown")


@pytest.mark.unit
class TestResolveEngine:
    def test_returns_default_for_non_overridden_step(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir)
        pack = DomainPack.load(pack_dir)

        assert pack.resolve_engine("plan") == "raw-llm"

    def test_returns_override_when_configured(self, tmp_path: Path) -> None:
        steps = [_make_step("plan"), _make_step("execute")]
        config = {
            "name": "test",
            "steps": steps,
            "engine": {"default": "raw-llm", "overrides": {"execute": "cursor-cli"}},
        }
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir, config=config)
        pack = DomainPack.load(pack_dir)

        assert pack.resolve_engine("execute") == "cursor-cli"
        assert pack.resolve_engine("plan") == "raw-llm"


@pytest.mark.unit
class TestSteps:
    def test_returns_ordered_step_definitions(self, tmp_path: Path) -> None:
        steps = [
            _make_step("define"),
            _make_step("plan"),
            _make_step("execute"),
            _make_step("review"),
        ]
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir, steps=steps)
        pack = DomainPack.load(pack_dir)

        assert pack.step_names == ["define", "plan", "execute", "review"]
        assert all(isinstance(s, StepDefinition) for s in pack.steps)

    def test_returns_copy_not_reference(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        _write_domain_pack(pack_dir)
        pack = DomainPack.load(pack_dir)

        returned = pack.steps
        returned.append(StepDefinition(name="injected", prompt="injected"))
        assert len(pack.steps) == 2
