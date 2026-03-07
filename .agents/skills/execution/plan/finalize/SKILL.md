---
name: finalize
description: Commits changes and optionally pushes branch and opens a PR. Use when asked to "commit", "finalize", "push and create PR", or "submit for review".
metadata:
  version: "1.0.0"
---

# Finalize

Stages, commits, and optionally pushes + opens a PR.

## When to Use

- User asks to "commit", "finalize", "push", or "create PR"

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.finalize`.
3. **Stage and commit** changes with a descriptive message.
4. **Push + PR** only if user explicitly requested it.

## Output Format

```markdown
## Finalize: {SUCCESS|SKIPPED|FAILED}

- Branch: {branch-name}
- Commit: {hash}
- PR: {pr-url or N/A}
```
