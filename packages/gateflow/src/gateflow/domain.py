from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

TrustLevel = Literal["autonomous", "gates_only", "review_all", "cautious"]

_TRUST_LEVEL_STEPS: dict[TrustLevel, set[str]] = {
    "autonomous": set(),
    "gates_only": {"review", "verify"},
    "review_all": {"plan", "execute", "review", "verify"},
    "cautious": {"plan", "execute", "review", "verify", "document", "finalize"},
}


class DomainPackError(Exception):
    pass


class StepDefinition(BaseModel):
    name: str
    prompt: str
    tools: list[str] = Field(default_factory=list)
    gate: bool = False
    readonly: bool = False


class EngineConfig(BaseModel):
    default: str
    overrides: dict[str, str] = Field(default_factory=dict)


class InterruptConfig(BaseModel):
    trust_level: TrustLevel = "autonomous"
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class DomainConfig(BaseModel):
    name: str
    steps: list[StepDefinition] = Field(min_length=1)
    engine: EngineConfig
    interrupts: InterruptConfig = Field(default_factory=InterruptConfig)
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
            prompt_file = prompts_dir / f"{step.prompt}.md"
            if not prompt_file.exists():
                raise DomainPackError(f"Missing prompt file for step '{step.name}': {prompt_file}")

        rules_dir = path / "rules"
        for step_name, rule_names in config.rules.items():
            for rule_name in rule_names:
                rule_file = rules_dir / f"{rule_name}.md"
                if not rule_file.exists():
                    raise DomainPackError(
                        f"Missing rule file '{rule_name}' "
                        f"referenced by step '{step_name}': {rule_file}"
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
    def steps(self) -> list[StepDefinition]:
        return list(self._config.steps)

    @property
    def step_names(self) -> list[str]:
        return [step.name for step in self._config.steps]

    @property
    def name(self) -> str:
        return self._config.name

    def interrupt_after_steps(self) -> list[str]:
        cfg = self._config.interrupts
        base = _TRUST_LEVEL_STEPS[cfg.trust_level]
        effective = (base | set(cfg.add)) - set(cfg.remove)
        return [s.name for s in self._config.steps if s.name in effective]
