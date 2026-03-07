---
name: spec-milestone
description: Decomposes a software development unit of work into logically ordered tasks with implementation details, then derives validation checkpoints at integration boundaries, producing a single combined task plan document. Use when the user wants a full task plan with validations, says "spec milestone", "plan dev tasks", "break this down with validations", or provides a feature/epic/phase to decompose end-to-end.
metadata:
  author: zs
  version: "1.0"
---

# Spec Milestone

Decompose a software development unit of work into logically ordered tasks with validation checkpoints at integration boundaries. Produces a single combined document.

## Communication Style

- Concise, specific, clear
- Ask before assuming on key decisions
- Make educated assumptions on minor details — state them
- Flag risks early
- Challenge unrealistic scope

## Example Flow

Input: "Add password reset to our auth service"
→ Step 2 produces: `1. Token schema + migration — 2. Reset request endpoint — 3. Reset confirmation endpoint — 4. Email notification integration`
→ Step 4 derives: `VC1 (after 1,2): request endpoint stores valid token — VC2 (after 2,3,4): full reset flow with email`
→ Step 6 merges into a single document: summary table (tasks + checkpoints interleaved), then full task details and checkpoint definitions in dependency order.

## When Activated

1. Classify input
2. Identify tasks
3. Confirm task plan with user
4. Derive validation checkpoints
5. Detail tasks
6. Merge and output

## Step 1: Classify Input

The skill can be invoked with anything. Figure out what you're looking at and respond helpfully.

**Classify the input (in priority order):**

1. **Actionable dev work** — enough context to decompose. Proceed to Step 2.
2. **Actionable but underspecified** — recognizably dev work but missing key decisions. Ask targeted questions, wait for answers, then proceed to Step 2.
3. **Not decomposable** — non-dev work, a goal without scope, a question, or off-topic. Respond helpfully, explain the skill decomposes software dev work into tasks, and stop.

Be adaptive: try to work with what's given, ask clarifying questions when ambiguous, only stop when the input genuinely can't be turned into a task plan.

## Step 2: Identify Tasks

Extract task candidates from the input, right-size them (3-7 steps each), order logically, and present a compact numbered list for confirmation.

**Scale check:** If the work decomposes into more than ~12 tasks, suggest splitting into phases before proceeding. If it produces fewer than 4 tasks, note that validation checkpoints may add little value and offer to skip Step 4.

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

## Step 4: Derive Validation Checkpoints

Analyze the confirmed task list to identify integration boundaries where cross-task validation is needed.

Load and follow [references/validation-checkpoints.md](references/validation-checkpoints.md).

Present the checkpoints and wait for user confirmation. The user may add, remove, or adjust checkpoints. Repeat until confirmed, then proceed to Step 5.

## Step 5: Detail Tasks

Define implementation steps, implementation requirements, verification scenarios, and dependencies for each confirmed task.

Load and follow [references/task-detailing.md](references/task-detailing.md).

## Step 6: Output

Merge the detailed tasks and validation checkpoints into a single combined document.

Load and follow [references/merge-format.md](references/merge-format.md).
