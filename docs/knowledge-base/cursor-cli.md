# Cursor CLI

Integration facts and limitations for the Cursor CLI (`agent` command) as used by `CursorCLIEngine`.

Source: [Cursor CLI docs](https://cursor.com/docs/cli/overview), [headless usage](https://cursor.com/docs/cli/headless), [parameters reference](https://cursor.com/docs/cli/reference/parameters).

## Binary

The CLI binary is `agent`, not `cursor`. Installed via `curl https://cursor.com/install -fsS | bash` (macOS/Linux/WSL) or `irm 'https://cursor.com/install?win32=true' | iex` (Windows PowerShell).

## Authentication

`CURSOR_API_KEY` env var or `-a, --api-key <key>` flag.

## Non-interactive (print) mode

`-p, --print` enables headless operation. Without it, the CLI starts an interactive TUI.

## Output formats

| Format | Flag | Behavior |
|---|---|---|
| `text` | `--output-format text` (default) | Final answer only, plain text |
| `json` | `--output-format json` | Single JSON blob on completion |
| `stream-json` | `--output-format stream-json` | NDJSON — one JSON object per line, includes tool call events |

`stream-json` is the richest for programmatic use. Add `--stream-partial-output` for character-level text deltas.

## stream-json event types

| `type` | `subtype` | Payload |
|---|---|---|
| `system` | `init` | `model` |
| `user` | — | `message.content[].text` (echoed prompt) |
| `assistant` | — | `message.content[].text` (incremental LLM output) |
| `tool_call` | `started` | `tool_call.<name>ToolCall.args` |
| `tool_call` | `completed` | `tool_call.<name>ToolCall.result` |
| `result` | `success` / error | `duration_ms` |

Known tool call keys: `shellToolCall`, `readToolCall`, `editToolCall`, `writeToolCall`, `deleteToolCall`, `grepToolCall`, `globToolCall`, `lsToolCall`, `todoToolCall`, `updateTodosToolCall`.

## Permission mapping

| PermissionMode | CLI flags | Effect |
|---|---|---|
| `acceptEdits` | `--force` | Agent modifies files without confirmation |
| `readonly` | `--mode ask` | Read-only exploration, no changes |
| `default` | (none) | Agent mode, but changes proposed not applied without `--force` |

## Tool restrictions

The CLI has **no per-invocation `--allowed-tools` flag**. Tool restrictions are controlled at the project level via `.cursor/` configuration. The `allowed_tools` parameter in `ExecutionEngine.run()` is accepted for protocol conformance but has no effect on the CLI invocation.

## Token usage

stream-json events **do not expose token counts**. `EngineResult.token_usage` is always `None` for `CursorCLIEngine`.

## Session resume

`--resume [chatId]` is available for resuming previous conversations. Not currently wired in `CursorCLIEngine` — potential future enhancement for multi-turn conversations within a workflow step.

## Modes

`--mode agent` (default), `--mode plan`, `--mode ask`. Same modes as the IDE editor.
