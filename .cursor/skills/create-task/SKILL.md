---
name: create-task
description: Creates a standardized task from any input. Use when asked to "create task", "add task", or "new task". Appends to tasks.json.
metadata:
  version: "0.3.0"
---

# Create Task

Creates a standardized task from user input. Synthesizes a clean description from potentially messy or informal requests.

## When to Use

- User asks to "create task" or "add task"
- Called by `dev-cycle` when given a user request instead of task ID

## When NOT to Use

- Deep task analysis or implementation planning → use `plan`
- Updating existing task state → modify the task entry in `tasks.json` directly

## Task Fields

**Required (system)** — always present, cannot be removed:

- `id`: Generated automatically
- `title`: Short, human-readable name for the task
- `description`: Synthesized from user input (clean, actionable summary)
- `state`: Always starts as `PENDING`

**User-defined** — additional fields from `.agents/config.json` → `tasks.fields`:

- Read the config to discover extra fields (e.g., `priority`)
- For each user-defined field, try to infer from context
- If cannot infer, ask user to provide

## Procedure

1. **Load config**: Read `.agents/config.json` → `tasks.fields` for all fields. Also load rules from `skillRules.create-task` if present.
2. **Check for task-organization rule**: If a loaded rule defines custom storage, ID format, or grouping, follow that convention instead of the defaults described below.
3. **Synthesize description**:
   - User input may be messy, informal, or vague
   - Extract the core intent and synthesize a clean, actionable description
   - If truly ambiguous (multiple interpretations), ask user to clarify
4. **Break into subtasks** (if applicable):
   - If the task involves multiple logical chunks, list them as subtasks
   - Subtasks must be in logical execution order
   - Read `maxSubtasks` from `.agents/config.json` → `tasks.maxSubtasks` (default: 7)
   - If subtask count exceeds the limit, tell user the task is too large and suggest how to split it. Do not proceed.
   - Simple tasks may have no subtasks — that's fine
5. **Gather user-defined fields**:
   - For each field in config beyond the required ones:
     - Try to infer from context or user input
     - If cannot infer, ask user
   - Continue until all fields have values
6. **Generate task ID**: Scan tasks file to find next available sequential ID
7. **Create artifacts**:
   - Read the tasks file (create with empty array `[]` if missing)
   - Append the new task object to the array
   - Write the updated array back
8. **Output**: Report using format below

## Default Storage

When no task-organization rule is present:

- **Tasks file**: `.agents/artifacts/tasks.json` (single array of all tasks)
- **ID format**: `task-001`, `task-002`, ... (zero-padded sequential)
- **ID generation**: Scan `tasks.json` for the highest existing number, increment by one

## Task Object Format

```json
{
  "id": "task-001",
  "title": "Configure devcontainer",
  "description": "Setup devcontainer",
  "subtasks": [
    "Configure base image",
    "Configure extensions",
    "Configure shell",
    "Mount filesystem"
  ],
  "state": "PENDING",
  "stateHistory": [{ "state": "PENDING", "timestamp": "..." }]
}
```

The `subtasks` array is optional — omit it for simple tasks with no subtasks.

## Output Format

```markdown
## Task Created: {task-id}

- Title: {title}
- Description: {description}
  {For each user-defined field:}
- {field}: {value}
```

## Error Handling

- Missing required info → ask user (do not guess)
- Ambiguous description → ask user to clarify

## Guidelines

- Keep descriptions actionable and specific
- Do not perform deep analysis — that's `plan`'s responsibility
- Single logical unit of work
- Completable in one session
- Subtasks should be in logical execution order
- If task exceeds the configured subtask limit, split into separate tasks
