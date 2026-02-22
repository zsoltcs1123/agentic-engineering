# Implement

Execute the implementation plan by writing code.

## Procedure

1. **Get the plan** from the context provided below.
2. **Verify plan is current**: If the plan references files that no longer exist, warn and adapt your approach.
3. **Implement step by step**:
   - Follow the plan's steps in order
   - Check each acceptance criterion as you go
   - Handle errors explicitly — don't swallow exceptions
   - Fix lint/test issues as they arise
4. **Output** a report using the format below.

## Deviation Rules

During implementation, deviations from the plan are expected. Apply these rules:

1. **Bugs, missing validation, blocking issues** — fix inline, note in output under Deviations.
2. **Architectural changes** (new DB tables, switching libraries, breaking API changes) — STOP, report as BLOCKED with proposed change.

All deviations must appear in the output report.

## Output Format

```markdown
## Implementation: {COMPLETE|BLOCKED}

### Changes Made

- {file}: {what was changed}

### Acceptance Criteria

- [x] {criterion met}
- [ ] {criterion not met — if BLOCKED}

### Deviations

- {deviation description — what changed and why}

Or: "None — plan executed as written."

### Notes

{Issues encountered or reason for BLOCKED status}
```

## Important

Execute the existing plan. Do not create a new plan unless the current one is fundamentally broken.
