---
name: spec-tasks
description: Decomposes a software development unit of work into logically ordered tasks with implementation details and verification scenarios. Use when the user wants to break down development work into tasks, says "break this down", "spec the tasks", "plan the tasks", "what needs to be done for this", or provides a feature/epic/phase to decompose.
metadata:
  author: zs
  version: "1.0"
---

# Spec Tasks

Decompose a software development unit of work into logically ordered, right-sized, executable tasks.

## Communication Style

- Concise, specific, clear
- Ask before assuming on key decisions
- Make educated assumptions on minor details — state them
- Flag risks early
- Challenge unrealistic scope

## When Activated

1. Classify input
2. Identify tasks
3. Confirm task plan with user
4. Detail each task
5. Present the result

## Step 1: Classify Input

The skill can be invoked with anything. Figure out what you're looking at and respond helpfully.

**Classify the input (in priority order):**

1. **Actionable dev work** — a feature, change, or deliverable with enough context to decompose. Proceed to Step 2.
2. **Actionable but underspecified** — recognizably dev work but missing key decisions or context. Ask targeted questions ("I'm assuming X — correct?"), wait for answers, then proceed to Step 2.
3. **Non-dev work** — the input describes work but not software development (e.g., "plan the office move"). Explain that this skill is for software dev tasks. Stop.
4. **Goal without scope** — a desired outcome with no actionable path (e.g., "improve performance"). Explain why it's not decomposable yet, suggest how to reframe it into concrete work. Stop.
5. **Question, not work** — the input asks something rather than requesting decomposition (e.g., "should we use Redis?"). Answer briefly if possible, explain the skill is for breaking down work. Stop.
6. **Completely off-topic** — unrelated to any kind of work. State what the skill does, ask for a unit of work to decompose. Stop.

Be adaptive: try to work with what's given, ask clarifying questions when ambiguous, only stop when the input genuinely can't be turned into a task plan.

## Step 2: Identify Tasks

Extract task candidates from the input, right-size them (3-7 steps each), order logically, and present a compact numbered list for confirmation.

Load and follow [references/task-identification.md](references/task-identification.md).

Present the list and wait for user confirmation (Step 3).

## Step 3: Confirm Task Plan

After the task list is presented, **stop and wait for the user's response**.

The user may:

- **Approve** — proceed to Step 4
- **Reorder** — move tasks to a different position
- **Merge** — consolidate multiple tasks into one
- **Split** — break a task into smaller ones
- **Add or remove** — introduce new tasks or drop existing ones

If the user requests changes, apply them, re-validate ordering and dependencies, and present the updated list. Repeat until confirmed.

## Step 4: Detail Tasks

Define implementation steps, implementation requirements, verification scenarios, and dependencies for each confirmed task.

Load and follow [references/task-detailing.md](references/task-detailing.md).

## Step 5: Output

Present the fully detailed breakdown using this template:

```
# Task Plan: [Work Title]

## Summary
[1-2 sentences: what this work delivers]

| # | Task | Depends on |
| --- | --- | --- |
| 1 | [title] | None |
| 2 | [title] | 1 |
| 3 | [title] | 1, 2 |

## Tasks

### 1. [Imperative title]
[1-3 sentence description]

**Steps:**
1. [concrete action]
2. [concrete action]
3. [concrete action]

**Implementation requirements:**
- [statically verifiable constraint — checkable by reading the code]

**Verification scenarios:**
- [input/condition] — [expected behavior]

**Depends on:** [task numbers or "None"]

---

### 2. [Imperative title]
...
```
