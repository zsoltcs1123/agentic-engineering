---
name: push-pr
description: Pushes branch to remote and creates a pull request. Use when asked to "push and create PR", "open a pull request", "submit for review", or "create a PR".
metadata:
  version: "0.2.0"
---

# Push and Create PR

Pushes the current branch and creates a pull request.

## When to Use

- User asks to "push and create PR" or "open a pull request"
- Ready to submit work for review

## Prerequisites

- GitHub CLI (`gh`) available
- Changes committed to local branch

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.push-pr`. If absent, use your own judgment.
2. **Check for existing PR**: If PR exists for branch, return existing URL
3. **Push branch** to remote with `-u` flag
4. **Create pull request** via `gh pr create`:
   - Title: From user, branch name, or commit message
   - Body: From user or auto-generated summary of changes
   - Base: main/master (or configured default)
5. **Output**: Report using format below

## PR Body Format (Default)

```markdown
## Summary

{Auto-generated from commits or provided description}

## Changes

{List of modified files}
```

## Output Format

```markdown
## Push-PR: {SUCCESS|EXISTS|FAILED}

- Branch: {branch-name}
- PR: {pr-url or N/A if failed}
- Title: {pr-title}

{If FAILED:}

- Error: {error-message}
- Suggestion: {how to resolve}
```

## Error Handling

- Not on a branch → FAILED: "Cannot push from detached HEAD"
- Push rejected → FAILED: "Push rejected. Pull or rebase required."
- No commits to push → EXISTS or skip: "Branch is up to date with remote"

## Important

- Never force push unless explicitly requested
- Warn if branch is behind base (may need rebase)
- Never push secrets or credentials
