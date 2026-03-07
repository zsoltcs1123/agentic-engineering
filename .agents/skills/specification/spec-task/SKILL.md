---
name: spec-task
description: Details a single task-sized unit of work into implementation steps, requirements, and verification scenarios. Pushes back on inputs that are milestone-level. Use when the user wants to detail a specific task, says "spec this task", "detail this task", or provides a single task to flesh out.
metadata:
  author: zs
  version: "0.1"
---

# Spec Task

Detail a single task-sized unit of work into implementation steps, implementation requirements, and verification scenarios.

## When to Use

- Detailing a new task that wasn't part of a milestone breakdown
- Re-specifying a task that needs more detail
- Adding a task to an existing plan

## Input

A single task description — something completable in a focused session (3-7 implementation steps).

### Input Validation

Before proceeding, validate that the input is task-sized:

- **Too large** (milestone-level): multiple concerns, would need 8+ steps, or contains words like "system", "module", "full flow". Examples: "build authentication system", "implement the payment module". → Push back: explain this is milestone-level work, suggest using `spec-milestone` to decompose first.
- **Too small** (sub-task): a single obvious action, 1-2 steps at most. Examples: "add a column to the users table", "rename the function". → Push back: this doesn't need a spec, just do it.
- **Right-sized**: a single coherent concern, estimated 3-7 steps. → Proceed.

## Output

TODO: Define the detailing process, output format, and quality standards.

Intended output: a task spec with steps, implementation requirements, verification scenarios, and dependencies — matching the format used by `spec-tasks` and `spec-milestone`.
