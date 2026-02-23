from __future__ import annotations

from pathlib import Path

PREFIX = "gateflow-poc-"

STEP_RULES: dict[str, tuple[str, str]] = {
    "plan": (
        "Plan step: create a structured implementation plan",
        """\
# Plan

Create a structured implementation plan for the given task. Analyze the codebase before planning.

## Procedure

1. Clarify requirements: state assumptions explicitly if task is ambiguous.
2. Analyze codebase: find similar patterns, identify affected files, check conventions.
3. Create plan with: Summary, Approach, Files to Modify, Steps, Acceptance Criteria, Risks.

## Important

Do NOT implement. Only plan.
""",
    ),
    "execute": (
        "Execute step: implement code following the plan",
        """\
# Implement

Execute the implementation plan by writing code.

## Procedure

1. Follow the plan's steps in order.
2. Check each acceptance criterion as you go.
3. Handle errors explicitly. Fix lint/test issues as they arise.
4. Output a brief report of what was changed.

## Deviation Rules

- Bugs, missing validation, blocking issues: fix inline, note in output.
- Architectural changes: STOP, report as BLOCKED with proposed change.

## Important

Execute the existing plan. Do not create a new plan.
""",
    ),
    "review": (
        "Review step: review code changes for quality issues",
        """\
# Code Review

Review code changes for quality issues.

## Procedure

1. Examine the diff of all changes (use git diff).
2. Review for: bugs, security, maintainability, idiomatic patterns.
3. Classify severity: High (bugs, security), Medium (poor patterns), Low (style).
4. Verdict: PASS if no high/medium issues, otherwise ISSUES.

## Output Format

Output ONLY a JSON object:

```json
{
  "verdict": "PASS or ISSUES",
  "reasoning": "Brief summary",
  "evidence": ["Specific observations"],
  "blind_spots": ["Things you could not verify"],
  "issues": ["severity: file:line - description"]
}
```
""",
    ),
    "verify": (
        "Verify step: check implementation matches acceptance criteria",
        """\
# Code Verification

Verify that code changes match the acceptance criteria from the plan.

## Procedure

1. Extract acceptance criteria from the plan.
2. Examine all code changes.
3. Check every criterion is addressed.
4. Verdict: PASS if all criteria met, ISSUES if not.

## Output Format

Output ONLY a JSON object:

```json
{
  "verdict": "PASS or ISSUES",
  "reasoning": "Brief summary",
  "evidence": ["Criterion checked and result"],
  "blind_spots": ["Things you could not verify"],
  "issues": ["Unmet criterion or problem"]
}
```
""",
    ),
    "finalize": (
        "Finalize step: commit changes and create a pull request",
        """\
# Finalize

Commit changes and create a pull request.

## Procedure

1. Create a feature branch if on main/master.
2. Run git status and git diff to review.
3. Stage relevant files. Exclude secrets.
4. Commit with conventional commit format (feat/fix/refactor/docs/test/chore).
5. Push branch to remote with -u flag.
6. Create PR via gh pr create.

## Important

- Never commit secrets
- Never force push
- Review diff before committing
""",
    ),
}

DOMAIN_RULES: dict[str, tuple[str, str]] = {
    "python": (
        "Python development standards (3.14+)",
        """\
# Python Development Standards

Python version: 3.14+

## Style

- Type hints on everything
- Absolute imports only
- No docstrings unless public API
- No comments unless non-obvious logic
- Functional over OO when appropriate

## Design

- Dataclasses for data models
- Explicit error handling with proper exception types
- Composition over inheritance
- YAGNI: don't add functionality until needed
""",
    ),
    "python-testing": (
        "Python testing standards",
        """\
# Testing Standards

## Organization

- Mirror source structure in tests/
- Markers: @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.slow

## Style

- Descriptive names: test_<subject>_<behavior>_when_<condition>
- Mock external dependencies
- Test behavior, not implementation
- Use parametrize for boundary values
- Don't test language features, only our logic
""",
    ),
}


def _wrap_mdc(content: str, description: str) -> str:
    return f"---\ndescription: {description}\nalwaysApply: false\n---\n\n{content}"


def install(workdir: Path) -> list[Path]:
    rules_dir = workdir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    for name, (description, content) in STEP_RULES.items():
        target = rules_dir / f"{PREFIX}step-{name}.mdc"
        target.write_text(_wrap_mdc(content, description), encoding="utf-8")
        written.append(target)

    for name, (description, content) in DOMAIN_RULES.items():
        target = rules_dir / f"{PREFIX}rule-{name}.mdc"
        target.write_text(_wrap_mdc(content, description), encoding="utf-8")
        written.append(target)

    return written


def uninstall(workdir: Path) -> list[Path]:
    rules_dir = workdir / ".cursor" / "rules"
    if not rules_dir.is_dir():
        return []

    removed: list[Path] = []
    for mdc_file in sorted(rules_dir.glob(f"{PREFIX}*.mdc")):
        mdc_file.unlink()
        removed.append(mdc_file)
    return removed
