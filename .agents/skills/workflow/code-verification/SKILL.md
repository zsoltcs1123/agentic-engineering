---
name: code-verification
description: Verifies code changes match specified criteria or a plan. Use when asked to "verify changes", "check against plan", "verify my implementation", or "does this match the requirements".
metadata:
  version: "0.1.0"
---

# Code Verification

Verifies code changes match acceptance criteria or an implementation plan.

## When to Use

- User asks to "verify my changes" or "check against the plan"
- After code-review passes
- Before marking work complete

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.code-verification`. If absent, use your own judgment.
2. **Get criteria**: From user input, plan file, or none (general verification). If absent, verify general coherence and correctness.
3. **Get changes**: Staged changes, uncommitted changes, or specific files based on context
4. **Verify**:
   - If criteria provided: check all items addressed, flag unplanned changes, confirm approach matches
   - If no criteria: verify changes are coherent, complete, and correct
5. **Determine verdict**:
   - **PASS**: All criteria met (or changes are coherent if no criteria)
   - **ISSUES**: Missing items, unplanned changes, or problems found
6. **Output report** to chat using format below

## Output Format

```markdown
# Verification: {PASS|ISSUES}

Date: {YYYY-MM-DD}

## Criteria

{If criteria provided: checklist with [x] for met, [ ] for unmet}
{If no criteria: "General coherence check"}

## Issues

{If PASS: "No issues found."}
{If ISSUES: list each as below}

### Missing: {criterion}

{What's missing from implementation}

### Unplanned: {change}

{Change not in criteria — needs justification or removal}

### Mismatch: {item}

- Expected: {what was expected}
- Actual: {what was implemented}
```

## Error Handling

- No changes to verify → report: "No changes to verify"
