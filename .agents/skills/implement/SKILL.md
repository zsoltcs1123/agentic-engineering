---
name: implement
description: Implements code by following a plan. Use when asked to "implement this plan", "execute the plan", "build this", "code this", or "write the code".
metadata:
  version: "1.0.0"
---

# Implement

Executes an implementation plan through a multi-phase inner loop. Only hands off once everything is green.

## When to Use

- User asks to "implement this plan" or "execute the plan"

## Input

An implementation plan with concrete steps.

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.implement`.
2. **Classify input** (Step 1 below).
3. **Validate the plan** (Step 2 below).
4. **Execute inner loop** (Step 3 below).

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

## Step 3: Execute Inner Loop

All work in this loop must follow the rules loaded in Step 1. The plan defines **what** to build; the rules define **how**.

   1. Write code following the plan steps
   2. Write tests (if applicable)
   3. Run tests & lint — iterate until green
   4. Run verification scenarios (if defined) — iterate until all green
   5. Update documentation following the rules (if needed)
   6. Collect deviations (if any). Follow deviation rules below.

## Deviation Rules

1. **Plan assumptions that don't hold** (API works differently than expected, library behavior differs from docs, signatures don't match) — adapt and keep going, note what the plan assumed vs. what was actually needed under Deviations.
2. **Bugs, missing guards, edge cases** — fix on the spot without stopping, note what was changed and why under Deviations.
3. **Plan's approach is unviable** (required capability doesn't exist, dependency is incompatible, fix would require a fundamentally different design, or adapting one step would invalidate multiple downstream steps) — **STOP**, report as BLOCKED. The plan itself needs revision, not just a local adaptation.

## Output Format

```markdown
## Implementation: {COMPLETE|BLOCKED}

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
