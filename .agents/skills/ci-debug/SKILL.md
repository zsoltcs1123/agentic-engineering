---
name: ci-debug
description: Fetches and diagnoses failed CI runs using gh CLI. Use when asked to "check CI", "why did CI fail", "debug CI", "check my pipeline", "what happened in CI", or "check my last ci".
metadata:
  version: "0.1.0"
---

# CI Debug

Fetches failed GitHub Actions CI logs and diagnoses the failure.

## When to Use

- User asks why CI failed or wants to check a pipeline run
- A PR has a failing status check

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status` to verify)
- Repository has GitHub Actions workflows (`.github/workflows/ci.yml`)

## Procedure

1. **Detect branch**: If the user didn't specify a branch or run ID, get the current branch:

   ```bash
   git branch --show-current
   ```

2. **List recent runs**: Fetch the last 5 runs for the branch:

   ```bash
   gh run list --branch <branch> --limit 5 --json databaseId,status,conclusion,event,headBranch,createdAt,name
   ```

   If the user asked about a specific PR, use `--event pull_request` or look up the PR's head branch.

3. **Pick the failed run**: Select the most recent run with `conclusion: "failure"`. If the user specified a run ID, use that instead. If no failures found, report that all recent runs passed.

4. **Get the run summary** to understand which jobs/steps failed:

   ```bash
   gh run view <run-id>
   ```

5. **Fetch failed logs** — this is the key step, returns only output from failed steps:

   ```bash
   gh run view <run-id> --log-failed
   ```

   If the output is very large (truncated or hard to parse), narrow to a specific job:

   ```bash
   gh run view <run-id> --log-failed --job <job-id>
   ```

6. **Read the CI workflow** file to understand the pipeline structure:

   Read `.github/workflows/ci.yml` to understand what the steps do. Key things to look for:
   - Did the **Nx** step fail and the **Scripts fallback** run? (check for the `::warning::Nx failed` annotation)
   - Which target failed: build, lint, or test?
   - Was it an affected run or a full run?

7. **Diagnose**: Cross-reference the error in the logs with the codebase. Common patterns:
   - Build errors → read the file/line mentioned in the compiler output
   - Test failures → read the failing test and the code it tests
   - Lint errors → read the file and the rule violation
   - Dependency issues → check `package.json` / `Directory.Packages.props`
   - Nx issues → check `nx.json` and `project.json` files

8. **Output** the diagnosis using the format below.

## Output Format

```markdown
## CI Debug

**Run:** <run-id> (<branch>, <event>, <timestamp>)
**Status:** failure
**Failed step:** <step-name>

### Error

<Relevant error output from the logs — keep it concise, max ~50 lines>

### Diagnosis

<What went wrong and why>

### Suggested Fix

<Specific actions to resolve the failure — file paths, code changes, commands>
```

## Edge Cases

- **No failed runs found** → report that all recent runs passed, show the latest run status
- **`gh` not authenticated** → tell the user to run `gh auth login`
- **Multiple failures in one run** → report all failed steps, diagnose each
- **Logs too large** → use `--job` flag to narrow scope, or extract only the error lines
- **Run is still in progress** → report status as "in_progress", offer to wait or check back later
