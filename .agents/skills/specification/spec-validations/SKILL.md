---
name: spec-validations
description: Derives validation checkpoints at integration boundaries from a software development task list with dependencies. Use when the user has a completed task breakdown and wants to identify where cross-task integration checks should occur, says "spec validations", "plan validations", "what should we validate", or wants integration test points for a set of tasks.
metadata:
  author: zs
  version: "1.0"
---

# Spec Validations

Derive validation checkpoints at integration boundaries from a software development task list.

## Communication Style

- Concise, specific, clear
- State inferred dependencies explicitly — ask for confirmation when uncertain
- Flag tasks with no clear integration surface

## When Activated

1. Classify input
2. Build dependency graph
3. Derive checkpoints
4. Present the result

## Step 1: Classify Input

The skill can be invoked with anything. Figure out what you're looking at and respond helpfully.

**Classify the input (in priority order):**

1. **Structured task list with dependencies** — numbered tasks, explicit dependency info. Proceed to Step 2.
2. **Structured task list, no dependencies** — tasks present but dependencies implicit/missing. Infer from ordering and content, state inferences, then proceed to Step 2.
3. **Unstructured work items** — rough description, not formally structured. Extract tasks, propose ordering + dependencies, then proceed to Step 2.
4. **Too few tasks** — fewer than 2 tasks; no integration boundaries possible. Suggest decomposing first. Stop.
5. **Non-dev work** — not software development. Explain skill scope. Stop.
6. **Not a task list** — question, feature description, code, or unrelated. Explain what the skill needs. Stop.

## Step 2: Build Dependency Graph

Map the tasks and their dependencies into a directed graph. Identify:

- **Convergence points** — where multiple independent tasks feed into a downstream task
- **Integration boundaries** — where a task first consumes the output of another task
- **Milestone clusters** — groups of tasks that together deliver a testable capability

Not every dependency edge is an integration boundary. A checkpoint is warranted when:

- Multiple tasks converge (their outputs must work together)
- A task crosses a system boundary (e.g., backend consumes a data model, UI calls an API)
- A cluster of tasks completes a user-visible or system-visible capability

Single linear chains (A -> B -> C where each just extends the previous) typically need a checkpoint only at the end, not at every link.

## Step 3: Derive Checkpoints

For each identified integration boundary, define a validation checkpoint using the format in Step 4.

Each validation action must state its automation feasibility:

- **full** — end-to-end autonomous (curl, CLI, script, DB query)
- **partial** — can invoke but human verifies outcome (visual UI, email content, third-party side effect)
- **human-only** — manual interaction required (OAuth flow, physical device, subjective judgment)

### Rules

- Only produce checkpoints at real integration boundaries, not for every task
- Concrete actions against the running system, not abstract checks
- State the expected _observable_ result
- Order chronologically (earliest integration boundary first)
- Don't duplicate per-task verification — checkpoints test how tasks work _together_
- Aim for roughly 1 checkpoint per 3-4 tasks; fewer for linear chains, more for highly convergent graphs

## Step 4: Output

Present the full validation plan. The user may iterate — correcting inferred dependencies, adding/removing checkpoints, or adjusting scope. Apply changes and re-present.

Use this template:

```
# Validation Checkpoints: [Work Title]

## Summary
[1-2 sentences: what these checkpoints cover and how many integration boundaries were identified]

## Task Dependency Graph
| # | Task | Depends on |
| --- | --- | --- |
| 1 | [title] | None |
| 2 | [title] | 1 |
| 3 | [title] | 1, 2 |

## Checkpoints

### Checkpoint 1: [short descriptive name]
**After tasks:** [task numbers]
**What to validate:** [integration behavior]
**How to validate:**
- [action] — [expected result] — Automation: [level]
- [action] — [expected result] — Automation: [level]

---

### Checkpoint 2: [short descriptive name]
...
```
