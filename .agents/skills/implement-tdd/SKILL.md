---
name: implement-tdd
description: Implements code using test-driven development. Use when asked to "TDD this", "implement with TDD", "test-first", or "red-green-refactor".
metadata:
  version: "1.0.0"
---

# Implement (TDD)

Executes an implementation plan using test-driven development. Tests are written first from the plan; code is written only to make them pass.

## When to Use

- User asks to "TDD this", "implement with TDD", or "test-first"

## Input

An implementation plan with concrete steps.

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.implement`.
2. **Classify input** (Step 1 below).
3. **Validate the plan** (Step 2 below).
4. **Execute TDD loop** (Step 3 below).

## Step 1: Classify Input

The skill can be invoked with anything. Figure out what you're looking at and respond helpfully.

**Classify the input (in priority order):**

1. **Valid plan** — contains a summary/description, concrete steps, implementation requirements, and verification scenarios. Proceed to Step 2.
2. **Plan-like but incomplete** — recognizably a plan but missing required elements (see Step 2). List what is missing, ask the user to complete it. **STOP.**
3. **Not a plan** — the input is a feature request, question, idea, or raw requirements without an execution plan. Explain that this skill executes plans, not creates them. Suggest using the plan skill first. **STOP.**
4. **No input / off-topic** — nothing actionable provided. State what the skill expects and stop. **STOP.**

## Step 2: Validate Plan

A plan is valid only when **all** of the following elements are present:

- A description or summary
- Concrete steps to be executed
- Implementation requirements
- Verification scenarios

If any element is missing → **STOP** and report exactly what is missing.

## Step 3: Execute TDD Loop

All work in this loop must follow the rules loaded in Step 1. The plan defines **what** to build; the rules define **how**.

For each plan step:

   1. **Red** — write failing tests derived from the step's implementation requirements and verification scenarios. Run tests, confirm they fail for the right reasons.
   2. **Green** — write the minimal code to make the failing tests pass. Nothing more.
   3. **Refactor** — clean up the code while keeping tests green. Apply coding standards from loaded rules.
   4. **Lint** — run linter, fix issues, re-run tests to confirm still green.

After all steps:

   5. Run verification scenarios — iterate until all green.
   6. Update documentation following the rules (if needed).
   7. Collect deviations (if any). Follow deviation rules below.

## Deviation Rules

1. **Plan assumptions that don't hold** (API works differently than expected, library behavior differs from docs, signatures don't match) — adapt and keep going, note what the plan assumed vs. what was actually needed under Deviations.
2. **Bugs, missing guards, edge cases** — fix on the spot without stopping, note what was changed and why under Deviations.
3. **Plan's approach is unviable** (required capability doesn't exist, dependency is incompatible, fix would require a fundamentally different design, or adapting one step would invalidate multiple downstream steps) — **STOP**, report as BLOCKED. The plan itself needs revision, not just a local adaptation.

## Output Format

```markdown
## Implementation (TDD): {COMPLETE|BLOCKED}

### Changes Made

- {file}: {what was changed}

### Tests Written

- {file}: {what is tested}

### Verification Results

- [x] {scenario passed}
- [ ] {scenario failed}

### Deviations

- {description — what changed and why}
  Or: "None — plan executed as written."

### Notes

{Issues encountered, if any}
```
