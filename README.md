# agentic-engineering

Dev repo for agentic engineering systems — orchestration, tooling, and patterns for building AI-driven workflows.

Structured as a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with independent packages under `packages/`.

## Packages

### gateflow

Domain-agnostic quality-gated workflow orchestrator built on [LangGraph](https://langchain-ai.github.io/langgraph/).

- **Quality gates** — review and verification steps that must pass before the workflow continues
- **Pluggable execution engines** — Claude Agent SDK, Cursor CLI, Cursor Cloud API, or raw LLM calls
- **Domain packs** — prompts, rules, and tools that plug into the orchestrator per domain
- **Declarative workflow definition** — steps, gates, and engine overrides declared in JSON

**Status:** Early development. Architecture: [`docs/gateflow-architecture.md`](docs/gateflow-architecture.md).

## Prerequisites

- [Python 3.14+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Quick Start

```bash
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

## Project Structure

```
agentic-engineering/
├── packages/
│   └── gateflow/               # quality-gated workflow orchestrator
│       ├── pyproject.toml
│       └── src/gateflow/
├── tests/                      # tests (organized by package)
│   └── gateflow/
│       ├── unit/
│       └── integration/
├── docs/                       # architecture and design docs
├── .agents/                    # reference system (markdown-driven predecessor)
├── pyproject.toml              # workspace root
└── DEVELOPMENT.md              # tooling and workflow docs
```

[uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) — each package has independent dependencies, shared dev tools in root `pyproject.toml`.

## Documentation

- [Gateflow Architecture](docs/gateflow-architecture.md) — design and migration plan
- [Development Guide](DEVELOPMENT.md) — commands, tooling, conventions
- [Agent Guidance](AGENTS.md) — AI coding agent standards
