---
name: dev-cycle
description: Orchestrates the full development cycle from an existing plan. Use when asked to "run dev-cycle", or "dev-cycle".
metadata:
  version: "1.0.0"
---

# Dev Cycle

Orchestrates execution from an existing implementation plan.

## When to Use

- User says "dev-cycle"

## Input

An implementation plan — either:

1. Already in conversation context
2. A file path to an implementation spec

## Pipeline

```
Implement (subagent) → Review (subagent) → [loop if ISSUES, max 2] → Document → Finalize
```

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.dev-cycle`.
2. **Resolve plan**: from conversation context or file path.
3. **Implement** (subagent, write access): delegate to `implement` skill with the plan.
4. **Review** (subagent, readonly): delegate to `code-review` skill.
   - If PASS → continue.
   - If ISSUES → loop back to Implement with review feedback. Max 2 review iterations; after that, stop and report.
5. **Document**: delegate to `document` skill.
6. **Finalize**: delegate to `finalize` skill. Push+PR only if user requested it.

## Subagent Strategy

Each step runs in an isolated subagent with only the skill instructions and scoped input.

| Step      | Input                        | Write access |
| --------- | ---------------------------- | ------------ |
| Implement | Plan content                 | Yes          |
| Review    | Diff of changes              | No           |
| Document  | Current changes              | Yes          |
| Finalize  | —                            | Yes          |

## Output Format

```markdown
## Dev Cycle: {COMPLETE|STOPPED|FAILED}

{If COMPLETE:}
- Commit: {hash}
- PR: {pr-url or N/A}

{If STOPPED (review gate):}
- Gate: Review
- Iterations: {n}/{max}
- Issues: {summary}

{If FAILED:}
- Error: {error-message}
```
