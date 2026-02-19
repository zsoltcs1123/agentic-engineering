---
name: code-review
description: Reviews code changes for quality issues. Use when asked to "review code", "check my changes", "review my PR", "check the diff", or "quality check". Outputs a structured report.
metadata:
  version: "0.1.0"
---

# Code Review

Reviews code changes for quality issues.

## When to Use

- User asks to "review my changes" or "review the code"
- Before committing or creating a PR

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.code-review`. If absent, use your own judgment—focus on bugs, security, maintainability, and idiomatic patterns for the language/framework.
2. **Get changes**: Staged changes, uncommitted changes, or specific files based on context
3. **Review against criteria**: apply loaded rules or your judgment from step 1
4. **Classify severity**:
   - **High**: Bugs, security issues, data loss risks — must fix
   - **Medium**: Poor patterns, violations of rules or best practices — should fix
   - **Low**: Style, minor improvements — nice to fix
5. **Determine verdict**: PASS if no high/medium issues, otherwise ISSUES
6. **Output code review** to chat using format below

## Output Format

```markdown
# Code Review: {PASS|ISSUES}

Date: {YYYY-MM-DD}

## Summary

{Brief description of what was reviewed}

## Issues

{If PASS: "No blocking issues found."}
{If ISSUES: list each issue as below}

### {Issue title}

- File: {filepath}
- Line: {line number}
- Severity: high|medium|low
- Description: {what's wrong}
- Suggestion: {how to fix}
```

## Error Handling

- No changes to review → report: "No staged changes to review"
