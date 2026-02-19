# AGENTS.md

## Paths

- Task state: `.agents/artifacts/tasks.json` (default, overridable by task-organization rule)
- Workflow artifacts: `.agents/artifacts/{task-id}/`
- Task ID: `task-YYY` (default, e.g., `task-001`)

## Task Resolution

1. Load rules from `.agents/config.json` → `skillRules` for the active skill
2. If a `task-organization` rule is loaded, follow its storage conventions (file location, ID format, grouping)
3. Otherwise use defaults: find task by `id` in `.agents/artifacts/tasks.json`
4. If tasks file missing → create with empty array

## Artifact Naming

Workflow artifacts are stored in `.agents/artifacts/{task-id}/`:

| File         | Pattern                     |
| ------------ | --------------------------- |
| Plan         | `{task-id}-plan.md`         |
| Review       | `{task-id}-review.md`       |
| Verification | `{task-id}-verification.md` |

## Rules Loading

Skills load rules from `.agents/config.json` → `skillRules.{skill-name}`:

1. Look up skill name in `skillRules`
2. Load each rule file from `.agents/rules/{rule-name}.md`
3. If file doesn't exist, skip (rules are optional)

## State Updates (dev-cycle)

When updating a task in the tasks file:

1. Find the task object by ID in the array
2. Set `state` to new value
3. Append to `stateHistory` with timestamp
4. Gates: include `result: "PASS"|"ISSUES"`
5. Commit: include `commit: "{hash}"`
6. Push-PR: include `pr: "{url}"`

If task not found in tasks file: append with current state, log warning.

## Output Limits

- Log/error output: max 50 lines
