from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from gateflow.domain import DomainPack, StepDefinition
from gateflow.engines import ExecutionEngine, PermissionMode
from gateflow.models import EngineResult, GateDecision
from gateflow.state import WorkflowState

_STATE_FIELD_MAP: dict[str, str] = {
    "plan": "plan",
    "review": "review_result",
    "verify": "verification_result",
}


def build_rule_mentions(step_name: str, domain: DomainPack) -> str:
    mentions = [f"@gateflow-step-{step_name}"]
    for rule_name in domain.rule_names_for_step(step_name):
        mentions.append(f"@gateflow-rule-{rule_name}")
    return " ".join(mentions)


def build_task_context(state: WorkflowState) -> str:
    sections: list[str] = []

    task = state.get("task_description", "")
    if task:
        sections.append(f"Task: {task}")

    wd = state.get("working_directory", "")
    if wd:
        sections.append(f"Working directory: {wd}")

    plan = state.get("plan", "")
    if plan:
        sections.append(f"Plan:\n{plan}")

    domain_data = state.get("domain_data")
    if domain_data:
        sections.append(f"Context:\n{json.dumps(domain_data, indent=2)}")

    if not sections:
        return ""

    return "\n\n".join(sections)


def _state_field_for_step(step_name: str) -> str | None:
    return _STATE_FIELD_MAP.get(step_name)


def _parse_gate_decision(output: str) -> GateDecision:
    try:
        raw = json.loads(output)
        return GateDecision.model_validate(raw)
    except Exception as exc:
        return GateDecision(
            verdict="ISSUES",
            reasoning="Failed to parse gate decision from engine output.",
            evidence=[],
            blind_spots=[],
            issues=[f"Parse error: {exc}"],
        )


def _update_state(
    step: StepDefinition,
    result: EngineResult,
    state: WorkflowState,
    *,
    prompt: str = "",
) -> dict[str, Any]:
    update: dict[str, Any] = {"current_step": step.name}

    field = _state_field_for_step(step.name)
    if field is not None:
        update[field] = result.output
    else:
        existing = dict(state.get("domain_data") or {})
        existing[step.name] = result.output
        update["domain_data"] = existing

    if step.gate:
        decision = _parse_gate_decision(result.output)
        update["gate_verdict"] = decision.verdict
        if decision.verdict == "ISSUES":
            update["review_result"] = decision.model_dump_json()

    trace_entry: dict[str, Any] = {
        "step": step.name,
        "prompt": prompt,
        "output": result.output,
        "token_usage": result.token_usage,
        "duration_s": result.duration_s,
    }
    update["trace"] = [trace_entry]

    return update


def make_node(
    step: StepDefinition,
    domain: DomainPack,
    engine: ExecutionEngine,
) -> Callable[[WorkflowState], Awaitable[dict[str, Any]]]:
    async def node(state: WorkflowState) -> dict[str, Any]:
        context = build_task_context(state)
        prompt = context or step.name
        permission_mode: PermissionMode = "readonly" if step.readonly else "acceptEdits"
        result = await engine.run(
            prompt=prompt,
            working_directory=state["working_directory"],
            allowed_tools=step.tools,
            permission_mode=permission_mode,
        )
        return _update_state(step, result, state, prompt=prompt)

    node.__name__ = step.name
    node.__qualname__ = step.name
    return node
