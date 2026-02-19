# Development Guide

All commands use `uv run`. Works on all platforms.

## Commands

```bash
uv run ruff format .                   # Format code
uv run ruff check .                    # Lint
uv run ruff check --fix .              # Lint + auto-fix
uv run mypy .                          # Type check
uv run pytest                          # Run all tests
uv run pytest -m unit                  # Unit tests only
uv run pytest -m integration           # Integration tests only
uv run pytest --cov=packages           # Tests with coverage
uv run pre-commit run --all-files      # Run all pre-commit hooks
```

A `Makefile` is included for Linux/macOS convenience (`make check`, `make test`, etc.). It wraps the same `uv run` commands.

## Testing

Tests live at the repo root under `tests/`, organized by package.

```
tests/
└── gateflow/
    ├── unit/
    └── integration/
```

**Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.api`

**Configuration**: `pytest.ini`

## Pre-commit Hooks

Run automatically on `git commit`:

- ruff format + check
- mypy
- pytest (unit)
- commitizen (commit message validation)
- detect-secrets
- file validation (YAML, JSON, TOML)

**Configuration**: `.pre-commit-config.yaml`

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `build:`, `ci:`, `perf:`, `style:`

```bash
uv run cz bump    # Version bump (analyzes commits, updates version, creates tag)
```

**Configuration**: `pyproject.toml` → `[tool.commitizen]`

## Configuration Files

| File                      | Purpose                                               |
| ------------------------- | ----------------------------------------------------- |
| `pyproject.toml`          | Workspace root, shared dev deps, commitizen, coverage |
| `ruff.toml`               | Linting and formatting                                |
| `mypy.ini`                | Type checking                                         |
| `pytest.ini`              | Test discovery and markers                            |
| `.pre-commit-config.yaml` | Pre-commit hooks                                      |
| `.editorconfig`           | Editor formatting consistency                         |
| `.secrets.baseline`       | Secret detection false positives                      |

## GitHub Actions

Both workflows are disabled by default (manual trigger via `workflow_dispatch` only):

- **CI** (`.github/workflows/ci.yml`) — lint, type check, test
- **Dependency Updates** (`.github/workflows/dependency-updates.yml`) — creates PRs for outdated deps

Uncomment `push`/`pull_request` or `schedule` triggers to enable.
