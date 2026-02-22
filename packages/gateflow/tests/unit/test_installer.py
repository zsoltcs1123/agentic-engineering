from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from gateflow.domain import DomainPackError
from gateflow.installer import install, uninstall


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
        (prompts_dir / f"{s['prompt']}.md").write_text(
            f"# {s['name'].title()}\n\nInstructions for {s['name']}.",
            encoding="utf-8",
        )

    if rule_files:
        rules_dir = root / "rules"
        rules_dir.mkdir(exist_ok=True)
        for name, text in rule_files.items():
            (rules_dir / f"{name}.md").write_text(text, encoding="utf-8")

    return root


@pytest.mark.unit
class TestInstall:
    def test_installs_step_prompts_as_mdc(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [{"name": "plan", "prompt": "plan"}, {"name": "execute", "prompt": "execute"}],
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        written = install(pack, workdir)

        rules_dir = workdir / ".cursor" / "rules"
        assert (rules_dir / "gateflow-step-plan.mdc").exists()
        assert (rules_dir / "gateflow-step-execute.mdc").exists()
        assert len(written) == 2

    def test_step_mdc_contains_frontmatter_and_content(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [{"name": "plan", "prompt": "plan"}],
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        install(pack, workdir)

        content = (workdir / ".cursor" / "rules" / "gateflow-step-plan.mdc").read_text(
            encoding="utf-8"
        )
        assert "alwaysApply: false" in content
        assert "description: Plan" in content
        assert "Instructions for plan." in content

    def test_installs_rule_files_as_mdc(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [{"name": "plan", "prompt": "plan"}],
            rules={"plan": ["python", "testing"]},
            rule_files={"python": "# Python\n\nStandards.", "testing": "# Testing\n\nGuide."},
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        written = install(pack, workdir)

        rules_dir = workdir / ".cursor" / "rules"
        assert (rules_dir / "gateflow-rule-python.mdc").exists()
        assert (rules_dir / "gateflow-rule-testing.mdc").exists()
        assert len(written) == 3

    def test_rule_mdc_contains_frontmatter_and_content(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [{"name": "plan", "prompt": "plan"}],
            rules={"plan": ["python"]},
            rule_files={"python": "# Python Standards\n\nUse type hints."},
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        install(pack, workdir)

        content = (workdir / ".cursor" / "rules" / "gateflow-rule-python.mdc").read_text(
            encoding="utf-8"
        )
        assert "alwaysApply: false" in content
        assert "description: Python Standards" in content
        assert "Use type hints." in content

    def test_creates_cursor_rules_directory(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [{"name": "plan", "prompt": "plan"}],
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        install(pack, workdir)

        assert (workdir / ".cursor" / "rules").is_dir()

    def test_deduplicates_rules_across_steps(self, tmp_path: Path) -> None:
        pack = _write_domain_pack(
            tmp_path / "pack",
            [
                {"name": "plan", "prompt": "plan"},
                {"name": "execute", "prompt": "execute"},
            ],
            rules={"plan": ["python"], "execute": ["python"]},
            rule_files={"python": "# Python\n\nShared rule."},
        )
        workdir = tmp_path / "project"
        workdir.mkdir()

        written = install(pack, workdir)

        rule_files = [p for p in written if "gateflow-rule-" in p.name]
        assert len(rule_files) == 1

    def test_raises_on_missing_prompt_file(self, tmp_path: Path) -> None:
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()
        config = {
            "name": "bad",
            "steps": [{"name": "plan", "prompt": "plan"}],
            "engine": {"default": "mock"},
        }
        (pack_dir / "domain.json").write_text(json.dumps(config), encoding="utf-8")
        (pack_dir / "prompts").mkdir()

        with pytest.raises(DomainPackError):
            install(pack_dir, tmp_path / "project")


@pytest.mark.unit
class TestUninstall:
    def test_removes_gateflow_mdc_files(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / ".cursor" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "gateflow-step-plan.mdc").write_text("x", encoding="utf-8")
        (rules_dir / "gateflow-rule-python.mdc").write_text("y", encoding="utf-8")
        (rules_dir / "other-rule.mdc").write_text("z", encoding="utf-8")

        removed = uninstall(tmp_path)

        assert len(removed) == 2
        assert not (rules_dir / "gateflow-step-plan.mdc").exists()
        assert not (rules_dir / "gateflow-rule-python.mdc").exists()
        assert (rules_dir / "other-rule.mdc").exists()

    def test_returns_empty_when_no_rules_dir(self, tmp_path: Path) -> None:
        removed = uninstall(tmp_path)

        assert removed == []

    def test_returns_empty_when_no_gateflow_files(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / ".cursor" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "other-rule.mdc").write_text("z", encoding="utf-8")

        removed = uninstall(tmp_path)

        assert removed == []
