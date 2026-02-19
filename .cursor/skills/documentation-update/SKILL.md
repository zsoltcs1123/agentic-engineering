---
name: documentation-update
description: Updates project documentation after code changes. Use when asked to "update docs", "sync documentation", "document my changes", or "update the README".
metadata:
  version: "0.1.0"
---

# Documentation Update

Keeps documentation in sync with code changes.

## When to Use

- User asks to "update docs" or "sync documentation"
- After making user-facing changes

## Procedure

1. **Load rules** from `.agents/config.json` → `skillRules.documentation-update`. If absent, use your judgment.
2. **Get changes**: Staged changes, uncommitted changes, or specific files based on context
3. **Identify affected docs**: README, API docs, architecture docs, config examples
4. **Determine updates needed**:
   - New features → add documentation
   - Changed behavior → update existing docs
   - Removed features → remove or mark deprecated
5. **Update docs**: Keep changes minimal and focused on what changed
6. **Output**: Report using format below

## Scope

**Update if affected**:

- README.md
- API documentation
- Architecture docs
- Configuration examples

**Do NOT update**:

- Auto-generated docs (regenerate instead)
- Changelog (handled separately)
- Version numbers (handled by release process)

## Output Format

```markdown
## Documentation Update: {UPDATED|SKIPPED}

{If UPDATED:}
Files updated:

- {filepath}: {what was changed}

{If SKIPPED:}
No documentation updates needed.
```

## Error Handling

- No docs exist → SKIPPED with: "No documentation files found"
- No changes require docs → SKIPPED with: "No changes require documentation updates"

## Important

Only update what's affected by the code changes. Don't rewrite unrelated sections.
