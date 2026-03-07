# Agentic Dev System

## Rules Loading

1. Load rules from `config.json` → `skillRules` for the active skill
2. If a `task-organization` rule is loaded, follow its storage conventions
3. Otherwise: find task by `id` in `.agents/artifacts/tasks.json`
4. If tasks file missing → create with empty array

### State Updates

## Output Limits

- Log/error output: max 50 lines
