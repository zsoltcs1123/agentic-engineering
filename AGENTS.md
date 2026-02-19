# AGENTS.md

> Baseline guidance for AI coding agents. For detailed standards see `.cursor/rules/`.

## Repo

**agentic-engineering** — uv workspace for agentic engineering systems. Packages under `packages/`, each with own `pyproject.toml`.

- **Python**: 3.14+
- **Package Manager**: uv (workspaces)

## Current Package: gateflow

Quality-gated workflow orchestrator built on LangGraph.

- **Location**: `packages/gateflow/`
- **Architecture**: `docs/gateflow-architecture.md`
- **Reference system**: `.agents/` (markdown-driven predecessor)

## Commands

Always use `uv run`. Do not use `make`.

```bash
uv run ruff format .                  # Format
uv run ruff check .                   # Lint
uv run mypy .                         # Type check
uv run pytest                         # Test
uv run pre-commit run --all-files     # All pre-commit hooks
```

## Development Loop

After making changes, run all checks (`ruff format`, `ruff check`, `mypy`, `pytest`). If any check fails, fix the issue and re-run **all** checks. Repeat until every check passes before considering the task done.
