---
name: document
description: Updates project documentation after code changes. Use when asked to "update docs", "sync documentation", or "document my changes".
metadata:
  version: "1.0.0"
---

# Document

Keeps documentation in sync with code changes.

## When to Use

- After making user-facing changes
- User asks to "update docs" or "document changes"

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.document`.
2. **Get changes**: staged/uncommitted changes.
3. **Identify affected docs** and update them.
4. **Scope**: README, API docs, architecture docs, config examples. Not auto-generated docs or changelog.

## Output Format

```markdown
## Document: {UPDATED|SKIPPED}

{If UPDATED:}
Files updated:
- {filepath}: {what was changed}

{If SKIPPED:}
No documentation updates needed.
```
