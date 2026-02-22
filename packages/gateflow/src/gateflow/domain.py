from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class DomainPackError(Exception):
    pass


class EngineConfig(BaseModel):
    default: str
    overrides: dict[str, str] = Field(default_factory=dict)


class DomainConfig(BaseModel):
    name: str
    steps: list[str] = Field(min_length=1)
    engine: EngineConfig
    rules: dict[str, list[str]] = Field(default_factory=dict)


class DomainPack:
    def __init__(self, path: Path, config: DomainConfig) -> None:
        self._path = path
        self._config = config

    @staticmethod
    def load(path: Path) -> DomainPack:
        config_file = path / "domain.json"
        if not config_file.exists():
            raise DomainPackError(f"Missing config file: {config_file}")

        try:
            raw = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DomainPackError(f"Invalid JSON in {config_file}: {exc}") from exc

        try:
            config = DomainConfig.model_validate(raw)
        except Exception as exc:
            raise DomainPackError(f"Invalid config in {config_file}: {exc}") from exc

        prompts_dir = path / "prompts"
        for step in config.steps:
            prompt_file = prompts_dir / f"{step}.md"
            if not prompt_file.exists():
                raise DomainPackError(f"Missing prompt file for step '{step}': {prompt_file}")

        rules_dir = path / "rules"
        for step, rule_names in config.rules.items():
            for rule_name in rule_names:
                rule_file = rules_dir / f"{rule_name}.md"
                if not rule_file.exists():
                    raise DomainPackError(
                        f"Missing rule file '{rule_name}' referenced by step '{step}': {rule_file}"
                    )

        return DomainPack(path, config)

    def build_prompt(self, step: str) -> str:
        prompt_file = self._path / "prompts" / f"{step}.md"
        if not prompt_file.exists():
            raise DomainPackError(f"Missing prompt file for step '{step}': {prompt_file}")

        base = prompt_file.read_text(encoding="utf-8")
        rule_names = self._config.rules.get(step, [])
        if not rule_names:
            return base

        rule_texts = [
            (self._path / "rules" / f"{name}.md").read_text(encoding="utf-8") for name in rule_names
        ]
        return base + "\n\n" + "\n\n".join(rule_texts)

    def resolve_engine(self, step: str) -> str:
        return self._config.engine.overrides.get(step, self._config.engine.default)

    @property
    def steps(self) -> list[str]:
        return list(self._config.steps)

    @property
    def name(self) -> str:
        return self._config.name
