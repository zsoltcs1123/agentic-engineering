# AGENTS.md

> Baseline guidance for AI coding agents. For detailed standards see `.cursor/rules/`.

## Repo

**agentic-engineering** — uv workspace for agentic engineering systems. Packages under `packages/`, each with own `pyproject.toml`.

- **Python**: 3.14+
- **Package Manager**: uv (workspaces)

## Packages

# gateflow

Quality-gated workflow orchestrator built on LangGraph.

- **Location**: `packages/gateflow/`
- **Architecture**: `docs/gateflow-architecture.md`
- **Reference system**: `.agents/` (markdown-driven predecessor)

This project currently serves as a reference only. Its implementation is LLM generated and too complex to make changes in. I am reimplementing something similar in `agentflow` package - taking a slow and cautious route.

# agentflow

I want to reimplement `gateflow` package step-by-step in a much more focused way.

# gateflow-poc

Can be largely ignored. Minimal POC: LangGraph orchestrator over Cursor CLI agent.

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

## Environment Constraints

- **Network**: Agent shell runs behind a corporate proxy that blocks outbound connections. Commands requiring network access (e.g., `pre-commit run`, `git fetch`, `pip install`) will fail in the agent shell. Run these in the user's terminal instead.
- **pre-commit**: Do not run `pre-commit run` from the agent shell. Validate changes with `ruff format`, `ruff check`, `mypy`, and `pytest` directly — these work without network access.
