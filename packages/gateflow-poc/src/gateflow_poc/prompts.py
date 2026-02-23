from __future__ import annotations

from gateflow_poc.state import WorkflowState


def build_plan_prompt(state: WorkflowState) -> str:
    return f"Plan the following task. Do NOT implement, only plan.\n\nTask: {state['task']}"


def build_execute_prompt(state: WorkflowState) -> str:
    return (
        f"Implement the following plan. Execute it step by step.\n\n"
        f"Task: {state['task']}\n\n"
        f"Plan:\n{state.get('plan', '')}"
    )


def build_review_prompt(state: WorkflowState) -> str:
    return (
        f"Review the code changes for the following task. "
        f"Use git diff to examine changes. "
        f"Output ONLY a JSON object with keys: "
        f"verdict (PASS/ISSUES), reasoning, evidence, blind_spots, issues.\n\n"
        f"Task: {state['task']}\n\n"
        f"Plan:\n{state.get('plan', '')}"
    )


def build_verify_prompt(state: WorkflowState) -> str:
    return (
        f"Verify the implementation matches the acceptance criteria from the plan. "
        f"Output ONLY a JSON object with keys: "
        f"verdict (PASS/ISSUES), reasoning, evidence, blind_spots, issues.\n\n"
        f"Task: {state['task']}\n\n"
        f"Plan:\n{state.get('plan', '')}"
    )


def build_finalize_prompt(state: WorkflowState) -> str:
    return (
        f"Commit and push the changes for the following task. "
        f"Create a feature branch if on main/master. Use conventional commit format.\n\n"
        f"Task: {state['task']}"
    )
