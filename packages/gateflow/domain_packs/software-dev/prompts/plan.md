# Plan

Create a structured implementation plan for the given task. Analyze the codebase before planning.

## Procedure

1. **Clarify requirements**: If the task description is ambiguous, state your assumptions explicitly.
2. **Analyze codebase**:
   - Find similar patterns in the codebase
   - Identify files likely to be affected
   - Check for relevant conventions or abstractions
   - If the task has subtasks, ensure all subtasks are covered by the steps. If no subtasks, derive steps directly from the description.
3. **Create plan** using the format below.

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

## Important

Do NOT implement. Only plan.
