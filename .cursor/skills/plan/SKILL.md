---
name: plan
description: Creates a structured implementation plan for a coding task. Use when asked to "plan this feature", "create a plan", "how should I approach this", or "design this".
metadata:
  version: "0.1.0"
---

# Plan

Creates a structured implementation plan before coding begins.

## When to Use

- User asks to "plan this feature" or "create a plan"
- Before implementing any non-trivial change

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.plan`. If absent, use your own judgment.
2. **Clarify requirements**: If description is ambiguous, ask before proceeding.
3. **Analyze codebase**:
   - Find similar patterns in the codebase
   - Identify files likely to be affected
   - Check for relevant conventions or abstractions
   - If task has subtasks, ensure all subtasks are covered by the steps. If no subtasks, derive steps directly from the description.
4. **Create plan** using the format below
5. **Output plan** to chat

## Plan Format

```markdown
# Plan: {title}

Date: {YYYY-MM-DD}

## Summary

{One sentence describing what this accomplishes}

## Approach

{High-level strategy — why this approach over alternatives}

## Files to Modify

| File   | Change         |
| ------ | -------------- |
| {path} | {what and why} |

## Steps

1. {Step with enough detail to execute}
2. {Next step}

## Dependencies

- {What must exist or be true before starting}

## Acceptance Criteria

- [ ] {How to verify this is complete}

## Risks

| Risk    | Mitigation      |
| ------- | --------------- |
| {Issue} | {How to handle} |
```

## Error Handling

- Ambiguous requirements → ask user to clarify before proceeding

## Important

Do NOT implement. Only plan.
