# Code Review

Review the code changes for quality issues.

## Procedure

1. **Get changes**: Examine the diff of all changes made during implementation.
2. **Review against criteria**: Focus on bugs, security, maintainability, and idiomatic patterns for the language/framework. Apply any rules provided below.
3. **Classify severity**:
   - **High**: Bugs, security issues, data loss risks — must fix
   - **Medium**: Poor patterns, violations of rules or best practices — should fix
   - **Low**: Style, minor improvements — nice to fix
4. **Determine verdict**: PASS if no high/medium issues, otherwise ISSUES.

## Output Format

You MUST output ONLY a JSON object matching this exact schema. No markdown, no explanation — just the JSON.

```json
{
  "verdict": "PASS or ISSUES",
  "reasoning": "Brief summary of the review",
  "evidence": [
    "Specific observation supporting the verdict"
  ],
  "blind_spots": [
    "Anything you could not verify"
  ],
  "issues": [
    "severity: file:line — description (only if verdict is ISSUES, empty list if PASS)"
  ]
}
```

- `verdict`: Must be exactly `"PASS"` or `"ISSUES"`.
- `reasoning`: One or two sentences summarizing the overall quality.
- `evidence`: List of specific observations (files checked, patterns found, tests verified).
- `blind_spots`: List of things you could not fully verify (e.g., runtime behavior, external integrations).
- `issues`: List of issues found. Empty list `[]` if verdict is PASS. Each issue should include severity, location, and description.
