# Merge Format

Combine detailed tasks and validation checkpoints into a single document, interleaved by dependency order.

## Interleaving Rules

Place each validation checkpoint immediately after the last task it depends on (all tasks in its "After tasks" field must have appeared). When a checkpoint and a task share the same position, the task comes first. Maintain original task numbering — don't renumber when checkpoints are inserted.

## Output Template

```
# Task Plan: [Work Title]

## Summary
[1-2 sentences: what this work delivers]

| #   | Item              | Type       | Depends on |
| --- | ----------------- | ---------- | ---------- |
| 1   | [task title]      | Task       | None       |
| 2   | [task title]      | Task       | 1          |
| VC1 | [checkpoint name] | Checkpoint | 1, 2       |
| 3   | [task title]      | Task       | 2          |

## Tasks & Validation Checkpoints

### 1. [Imperative title]
[1-3 sentence description]

**Steps:**
1. [concrete action]
...

**Implementation requirements:**
- [statically verifiable constraint]

**Verification scenarios:**
- [input/condition] — [expected behavior]

**Depends on:** [task numbers or "None"]

---

### VC1. Validation checkpoint: [short descriptive name]
**After tasks:** [task numbers]
**What to validate:** [integration behavior]
**Validation scenarios:**
- [action on running system] — [expected observable result]

---
```

Tasks use the full detail format from task-detailing.md. Checkpoints use the checkpoint format from validation-checkpoints.md. Follow the interleaving order from the summary table.
