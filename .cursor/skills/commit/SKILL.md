---
name: commit
description: Stages and commits changes with a descriptive message. Use when asked to "commit changes", "commit my work", "save my changes", or "git commit".
metadata:
  version: "0.1.0"
---

# Commit

Stages and commits code changes.

## When to Use

- User asks to "commit changes" or "commit my work"
- Changes are ready to be recorded

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.commit`. If absent, use default format below.
2. **Create feature branch**: If on main/master, run `git checkout -b {task-id}`. Never commit directly to main/master.
3. **Review changes**: Run `git status` to see pending changes
4. **Stage changes**: `git add` relevant files (exclude secrets)
5. **Compose message**: Use user-provided message if given, otherwise auto-generate following rules or default format
6. **Commit**: Create commit with message and push to remote
7. **Output**: Report using format below

## Commit Message Format (Default)

```
{type}: {short description}

{Optional body with details}
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## Output Format

```markdown
## Commit: {SUCCESS|SKIPPED}

{If SUCCESS:}

- Hash: {commit-hash}
- Message: {commit-message}
- Files: {count} files changed

{If SKIPPED:}
No changes to commit.
```

## Error Handling

- Nothing to commit → SKIPPED
- Secret files detected (.env, credentials, keys) → warn and exclude from commit

## Important

- Never commit files containing secrets
- Never force push or amend unless explicitly requested
- Review diff before committing
