# Validation Checkpoints

Derive validation checkpoints at integration boundaries from the confirmed task list.

## Build Dependency Graph

Map the tasks and their dependencies into a directed graph. Identify:

- **Convergence points** — where multiple independent tasks feed into a downstream task
- **Integration boundaries** — where a task first consumes the output of another task
- **Milestone clusters** — groups of tasks that together deliver a testable capability

Not every dependency edge is an integration boundary. A checkpoint is warranted when:

- Multiple tasks converge (their outputs must work together)
- A task crosses a system boundary (e.g., backend consumes a data model, UI calls an API)
- A cluster of tasks completes a user-visible or system-visible capability

Single linear chains (A -> B -> C where each just extends the previous) typically need a checkpoint only at the end, not at every link.

## Derive Checkpoints

For each identified integration boundary, define a validation checkpoint.

### Rules

- Only produce checkpoints at real integration boundaries, not for every task
- Concrete actions against the running system, not abstract checks
- State the expected _observable_ result
- Order chronologically (earliest integration boundary first)
- Don't duplicate per-task verification — checkpoints test how tasks work _together_
- Aim for roughly 1 checkpoint per 3-4 tasks; fewer for linear chains, more for highly convergent graphs

### Format

For each checkpoint, define:

```
### VC[N]. Validation checkpoint: [short descriptive name]
**After tasks:** [task numbers]
**What to validate:** [integration behavior being tested]
**Validation scenarios:**
- [action on running system] — [expected observable result]
- [action on running system] — [expected observable result]
```

## Present for Confirmation

Present the checkpoints as a numbered list (VC1, VC2, ...) and wait for user confirmation. The user may:

- **Approve** — proceed
- **Add** — insert checkpoints at additional integration boundaries
- **Remove** — drop checkpoints that aren't needed
- **Adjust** — change scope, scenarios, or ordering

Apply changes and re-present until confirmed.
