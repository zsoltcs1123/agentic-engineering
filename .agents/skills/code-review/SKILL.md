---
name: code-review
description: Reviews code changes for quality issues. Use when asked to "review code", "check my changes", "review my PR", or "quality check".
metadata:
  version: "1.0.0"
---

# Code Review

Reviews code changes for quality issues.

## When to Use

- User asks to "review my changes" or "review the code"
- Called by `dev-cycle` after implementation

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.code-review`.
2. **Get changes**: staged/uncommitted changes or diff.
3. **Review** against loaded rules or general best practices.
4. **Classify severity**: high (must fix), medium (should fix), low (nice to fix).
5. **Verdict**: PASS if no high/medium issues, otherwise ISSUES.

## Output Format

```markdown
# Code Review: {PASS|ISSUES}

## Summary
{Brief description of what was reviewed}

## Issues
{If PASS: "No blocking issues found."}
{If ISSUES: list each with file, line, severity, description, suggestion}
```
