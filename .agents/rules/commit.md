# Commit Rules

Format: `{type}({scope}): {description}` — type and scope are mandatory.

Description: imperative mood, lowercase start, no trailing period, max 72 chars.
Body (optional): wrap at 72 chars, explain _why_ not _what_.

## Types

`feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`

## Scopes

| Scope      | When                                   |
| ---------- | -------------------------------------- |
| `platform` | Shared infra, auth, deployment, Docker |
| `idx`      | IDX (MES) application                  |
| `energy`   | Energy application                     |
| `gateway`  | API gateway                            |
| `deps`     | Pure dependency bumps only             |
| `agents`   | Agentic dev system (.agents/)          |

Multiple scopes affected → pick the primary one.

## Pre-commit Hooks

Never use `--no-verify`. If a hook fails, fix and commit again.
