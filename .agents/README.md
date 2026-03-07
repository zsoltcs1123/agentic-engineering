# Agentic Dev System — Execution Layer

Portable, composable execution skills for AI-assisted development. Works with Cursor, Claude Code, Codex, or any agent that reads markdown.

## Principles

1. **Portable** — no vendor lock-in; any markdown-reading agent works
2. **Composable** — every skill works standalone or as part of `dev-cycle`
3. **Lean context** — brief pointers; details live in rules

## Skills

| Skill         | Purpose                                          |
| ------------- | ------------------------------------------------ |
| `dev-cycle`   | Orchestrates the full execution pipeline          |
| `implement`   | Write code, tests, run lint/tests/verifications   |
| `code-review` | Review changes for quality issues                 |
| `document`    | Update project documentation                      |
| `finalize`    | Commit, optionally push + open PR                 |
| `ci-debug`    | Diagnose failed CI runs                           |

## Pipeline

```
Implement → Review → [loop if issues] → Document → Finalize
```

`dev-cycle` drives this sequence from an existing implementation plan (Cursor plan-mode output or a file).

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
