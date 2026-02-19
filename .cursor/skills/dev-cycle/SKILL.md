---
name: dev-cycle
description: Orchestrates the full development cycle for a task. Use when asked to "run dev-cycle", "complete task-XXX", "execute task", or "work on task".
metadata:
  version: "0.4.0"
---

# Dev Cycle

Orchestrates the complete development workflow for a task. Owns all state management and artifact storage.

## When to Use

- User asks to "run dev-cycle for task-XXX"
- User asks to "dev-cycle: {user request}" with a new task
- Running end-to-end task completion

## Input

- **Task ID** (e.g., `task-001`) — resumes from current state
- OR **User request** — creates task first, then runs from PENDING

User request can be messy or informal. The `create-task` skill synthesizes a clean description.

## Workflow

```
Plan → Implement → Review → Verify → Document → Commit → Push-PR
```

Linear flow. On any gate failure (Review or Verify), stop and report. User fixes manually and re-runs.

## Procedure

See `.agents/AGENTS.md` for path conventions.

### 0. Resolve Task Context

1. **Load config**: Read `.agents/config.json`. Load rules from `skillRules.dev-cycle` if present.
2. **Check for task-organization rule**: If a loaded rule defines custom storage, ID format, or grouping, follow that convention instead of the defaults described below.
3. **Detect input type**:
   - If matches a known task ID pattern → existing task, go to step 5
   - Otherwise → new task from user request, go to step 4
4. **Create task** (if user request provided):
   - Run `create-task` skill with user request
   - `create-task` synthesizes a clean description from the request
   - Use returned task ID
5. **Locate task**: Find the task by `id` in the tasks file to determine current state

### 1. Resume from Current State

Skip completed steps based on state:

| State       | Start At                                  |
| ----------- | ----------------------------------------- |
| PENDING     | Plan                                      |
| PLANNED     | Implement                                 |
| IMPLEMENTED | Review                                    |
| REVIEWED    | Verify                                    |
| VERIFIED    | Document                                  |
| DOCUMENTED  | Commit                                    |
| COMMITTED   | Push-PR                                   |
| PR_CREATED  | Already complete — output status and exit |

### 2. Execute Steps

#### Plan (subagent)

- Delegate to a subagent running the `plan` skill with task description (readonly)
- Save returned plan to `.agents/artifacts/{task-id}/{task-id}-plan.md`
- Update task state in tasks file → PLANNED

#### Implement (subagent)

- Delegate to a subagent running the `implement` skill with plan file path (needs write access)
- Update task state in tasks file → IMPLEMENTED

#### Review (Gate, subagent)

- Delegate to a subagent running the `code-review` skill (readonly)
- Save returned review to `.agents/artifacts/{task-id}/{task-id}-review.md`
- **If PASS**: Update task state in tasks file → REVIEWED
- **If ISSUES**: STOP. Report issues. User fixes and re-runs dev-cycle.

#### Verify (Gate, subagent)

- Read acceptance criteria from `.agents/artifacts/{task-id}/{task-id}-plan.md`
- Delegate to a subagent running the `code-verification` skill with the criteria (readonly)
- Save returned verification to `.agents/artifacts/{task-id}/{task-id}-verification.md`
- **If PASS**: Update task state in tasks file → VERIFIED
- **If ISSUES**: STOP. Report issues. User fixes and re-runs dev-cycle.

#### Document

- Run `documentation-update` skill
- Update task state in tasks file → DOCUMENTED

#### Commit

- Run `commit` skill
- Update task state in tasks file → COMMITTED
- Record commit hash in stateHistory

#### Push-PR

- Run `push-pr` skill
- Update task state in tasks file → PR_CREATED
- Record PR URL in stateHistory

## Default Storage

When no task-organization rule is present:

- **Tasks file**: `.agents/artifacts/tasks.json`
- **Task ID pattern**: `task-YYY` (e.g., `task-001`)

## State Tracking

Find the task by `id` in the tasks file and update in place after each step:

```json
{
  "id": "task-001",
  "description": "Add user authentication",
  "state": "REVIEWED",
  "stateHistory": [
    { "state": "PENDING", "timestamp": "..." },
    { "state": "PLANNED", "timestamp": "..." },
    { "state": "IMPLEMENTED", "timestamp": "..." },
    { "state": "REVIEWED", "timestamp": "...", "result": "PASS" }
  ]
}
```

For gates, include `result: "PASS"` or `result: "ISSUES"` in history.
For commit, include `commit: "{hash}"`.
For push-pr, include `pr: "{url}"`.

## Artifact Paths

Workflow artifacts live in a per-task folder under artifacts root:

```
.agents/artifacts/{task-id}/
├── {task-id}-plan.md
├── {task-id}-review.md
└── {task-id}-verification.md
```

Create the `.agents/artifacts/{task-id}/` folder on first artifact write.

## Error Handling

- Tasks file missing → create with empty array
- Task not found in tasks file → append with PENDING state
- Gate returns ISSUES → stop, report, exit (no automatic retry)

## On Failure

When a gate fails:

1. State stays at previous value (IMPLEMENTED for Review, REVIEWED for Verify)
2. Report the issues to user
3. User fixes manually
4. User re-runs `dev-cycle` — it resumes from current state

## Output Format

```markdown
## Dev Cycle: {COMPLETE|STOPPED|FAILED}

Task: {task-id}
Final State: {state}

{If COMPLETE:}

- PR: {pr-url}

{If STOPPED (gate failure):}

- Gate: {Review|Verify}
- Issues: see {task-id}-review.md or {task-id}-verification.md

{If FAILED:}

- Error: {error-message}
```

## Subagent Strategy

Run Plan, Implement, Review, and Verify in isolated subagents. Each subagent receives only the skill instructions and its scoped input — no prior conversation context leaks in.

| Step      | Input                                        | Write access |
| --------- | -------------------------------------------- | ------------ |
| Plan      | Task description, relevant codebase context  | No           |
| Implement | Plan file path, full codebase access         | Yes          |
| Review    | Diff of changes                              | No           |
| Verify    | Plan acceptance criteria, current code state | No           |

**How to delegate**: Read the target skill's SKILL.md and pass its full content plus the required input as the subagent's prompt. Use whatever subagent/subprocess mechanism the host agent framework provides (e.g., Cursor Task tool, Claude sub-conversation, Copilot child agent). The subagent's returned message is the skill output. Save artifacts and update state in the orchestrator context, not inside the subagent.
