# Agentic Dev System

Portable, composable skills for AI-assisted development. Works with Cursor, Claude Code, Codex, or any agent that reads markdown.

## Principles

1. **Portable** — no vendor lock-in; any markdown-reading agent works
2. **Composable** — every skill works standalone or as part of a pipeline
3. **Lean context** — brief pointers; details live in rules and references

## Skills

### Specification Layer

Successive refinement from broad intent to executable plans. See [WORKFLOW.md](WORKFLOW.md) for the full pipeline.

| Skill              | Level     | Purpose                                              |
| ------------------ | --------- | ---------------------------------------------------- |
| `spec-project`     | Blueprint | Create vision, architecture, roadmap, evaluation     |
| `spec-milestone`   | Milestone | Decompose work into tasks + validation checkpoints   |
| `spec-tasks`       | Milestone | Decompose work into tasks (without validations)      |
| `spec-validations` | Milestone | Derive validation checkpoints from a task list       |
| `spec-task`        | Task      | Detail a single task with steps and requirements     |
| `plan-exec`        | Plan      | Codebase-aware implementation planning               |

### Execution Layer

Drives spec artifacts to shipped code. See [WORKFLOW.md](WORKFLOW.md) for the full pipeline.

| Skill         | Purpose                                          |
| ------------- | ------------------------------------------------ |
| `dev-cycle`   | Orchestrates the full execution pipeline          |
| `implement`   | Write code, tests, run lint/tests/verifications   |
| `code-review` | Review changes for quality issues                 |
| `document`    | Update project documentation                      |
| `finalize`    | Commit, optionally push + open PR                 |

### Standalone

| Skill      | Purpose                 |
| ---------- | ----------------------- |
| `ci-debug` | Diagnose failed CI runs |

## Execution Pipeline

```
Implement → Review → [loop if issues] → Document → Finalize
```

`dev-cycle` drives this sequence from an existing implementation plan.

## Rules

Optional, user-defined markdown files in `.agents/rules/`. Mapped to skills via `config.json` → `skillRules`:

```json
"skillRules": {
  "implement": ["get-docs"],
  "finalize": ["commit"]
}
```

Skills load their mapped rules at runtime. Missing files are silently skipped.

## Installation

```bash
# Linux/macOS
.agents/cursor-install.sh

# Windows (PowerShell)
.agents/cursor-install.ps1
```

Creates symlinks in `.cursor/skills/` and generates `.cursor/rules/*.mdc` from `.agents/rules/*.md`.
