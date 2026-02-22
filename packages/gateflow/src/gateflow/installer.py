from __future__ import annotations

import re
from pathlib import Path

from gateflow.domain import DomainPack, DomainPackError

_GATEFLOW_PREFIX = "gateflow-"
_STEP_PREFIX = f"{_GATEFLOW_PREFIX}step-"
_RULE_PREFIX = f"{_GATEFLOW_PREFIX}rule-"


def _extract_description(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def _wrap_mdc(content: str, description: str) -> str:
    return f"---\ndescription: {description}\nalwaysApply: false\n---\n\n{content}"


def install(domain_pack_path: Path, workdir: Path) -> list[Path]:
    domain = DomainPack.load(domain_pack_path)
    rules_dir = workdir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    prompts_dir = domain_pack_path / "prompts"
    for step in domain.steps:
        prompt_file = prompts_dir / f"{step.prompt}.md"
        if not prompt_file.exists():
            raise DomainPackError(f"Missing prompt file for step '{step.name}': {prompt_file}")
        content = prompt_file.read_text(encoding="utf-8")
        description = _extract_description(content, f"Gateflow step: {step.name}")
        mdc = _wrap_mdc(content, description)
        target = rules_dir / f"{_STEP_PREFIX}{step.name}.mdc"
        target.write_text(mdc, encoding="utf-8")
        written.append(target)

    src_rules_dir = domain_pack_path / "rules"
    if src_rules_dir.is_dir():
        all_rule_names: set[str] = set()
        for rule_names in domain.rules_mapping.values():
            all_rule_names.update(rule_names)

        for rule_name in sorted(all_rule_names):
            rule_file = src_rules_dir / f"{rule_name}.md"
            if not rule_file.exists():
                raise DomainPackError(f"Missing rule file: {rule_file}")
            content = rule_file.read_text(encoding="utf-8")
            description = _extract_description(content, f"Gateflow rule: {rule_name}")
            mdc = _wrap_mdc(content, description)
            target = rules_dir / f"{_RULE_PREFIX}{rule_name}.mdc"
            target.write_text(mdc, encoding="utf-8")
            written.append(target)

    return written


def uninstall(workdir: Path) -> list[Path]:
    rules_dir = workdir / ".cursor" / "rules"
    if not rules_dir.is_dir():
        return []

    removed: list[Path] = []
    for mdc_file in sorted(rules_dir.glob(f"{_GATEFLOW_PREFIX}*.mdc")):
        mdc_file.unlink()
        removed.append(mdc_file)

    return removed
