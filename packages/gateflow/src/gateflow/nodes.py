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


def inject_state(prompt: str, state: WorkflowState) -> str:
    sections: list[str] = []

    task = state.get("task_description", "")
    if task:
        sections.append(f"**Task:** {task}")

    wd = state.get("working_directory", "")
    if wd:
        sections.append(f"**Working Directory:** {wd}")

    plan = state.get("plan", "")
    if plan:
        sections.append(f"**Plan:**\n{plan}")

    domain_data = state.get("domain_data")
    if domain_data:
        sections.append(f"**Domain Data:**\n{json.dumps(domain_data, indent=2)}")

    if not sections:
        return prompt

    context_block = "\n\n".join(sections)
    return f"{prompt}\n\n---\n## Context\n\n{context_block}\n---"


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
    step: StepDefinition, result: EngineResult, state: WorkflowState
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
        "output": result.output[:200],
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
        base_prompt = domain.build_prompt(step.prompt)
        prompt = inject_state(base_prompt, state)
        permission_mode: PermissionMode = "readonly" if step.readonly else "acceptEdits"
        result = await engine.run(
            prompt=prompt,
            working_directory=state["working_directory"],
            allowed_tools=step.tools,
            permission_mode=permission_mode,
        )
        return _update_state(step, result, state)

    node.__name__ = step.name
    node.__qualname__ = step.name
    return node
