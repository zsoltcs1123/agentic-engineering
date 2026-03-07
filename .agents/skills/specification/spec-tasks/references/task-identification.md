# Task Identification

Extract, validate, and order the full list of tasks from a unit of work.

## Process

### Extract Task Candidates

Scan the input for distinct pieces of work. Look for:

- Explicit items the user listed
- Implicit work required by explicit items (e.g., "set up CI" implies configuring a runner, writing pipeline config, adding status checks)
- Setup/teardown work not mentioned but necessary
- Integration points between components

### Right-Size the List

Each task should be a single, coherent unit of work. Estimate step count for sizing only — do not define steps at this stage.

| Signal          | Too Big                    | Right-Sized            | Too Granular                  |
| --------------- | -------------------------- | ---------------------- | ----------------------------- |
| Est. step count | >7 implementation steps    | 3-7 steps              | 1-2 steps or none             |
| Scope           | Multiple concerns          | Single concern         | Partial concern               |
| Description     | Needs sub-breakdown        | Self-contained         | Trivial / obvious             |
| Review          | Hard to review as one unit | Reviewable as one unit | Not worth a standalone review |

**If a candidate is too big:** split along natural seams — by component, by layer, by concern.
**If candidates are too granular:** merge related ones into a single coherent task.

### Order Logically

Arrange tasks so that:

1. **Foundation first** — infrastructure, setup, data models before features
2. **Dependencies respected** — no task references something a later task creates
3. **Progressive building** — each task builds on prior work toward a working whole
4. **Integration points grouped** — tasks that connect components sit near each other

When two tasks have no dependency, prefer the order that gives earlier feedback or reduces risk.

### Validate and Present

Before presenting the task list, verify that:

- No gaps — completing all tasks delivers the full scope
- No overlaps — each piece of work lives in exactly one task
- Logical ordering holds — no forward dependencies
- Each task is right-sized (single concern, estimated 3-7 steps)

Present the task list in compact format:

```
1. [Title] — [one-line description] (depends on: None)
2. [Title] — [one-line description] (depends on: 1)
3. [Title] — [one-line description] (depends on: 1, 2)
```
