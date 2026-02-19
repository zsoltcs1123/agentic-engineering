---
name: implement
description: Implements code by following a plan. Use when asked to "implement this plan", "execute the plan", "build this", "code this", or "write the code".
metadata:
  version: "0.1.0"
---

# Implement Task

Executes an implementation plan by writing code.

## When to Use

- User asks to "implement this plan" or "execute the plan"
- A plan exists and is ready for execution

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.implement`. If absent, use your own judgment.
2. **Get the plan**: From user input, plan file, or conversation context
3. **Verify plan is current**: If plan references files that no longer exist, warn and adapt approach
4. **Implement step by step**:
   - Follow the plan's steps in order
   - Check each acceptance criterion as you go
   - Handle errors explicitly — don't swallow exceptions
   - Fix lint/test issues as they arise
5. **Output**: Report using format below

## Deviation Rules

During implementation, deviations from the plan are expected. Apply these rules:

1. **Bugs, missing validation, blocking issues** — fix inline, note in output under Deviations
2. **Architectural changes** (new DB tables, switching libraries, breaking API changes) — STOP, report as BLOCKED with proposed change

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

## Error Handling

- No plan provided → ask user for plan or clarification
- Plan is stale → warn and adapt: "Plan references outdated files. Adapting approach."
- Blocked by missing dependency → BLOCKED with explanation

## Important

Execute the existing plan. Do not create a new plan unless the current one is fundamentally broken.
