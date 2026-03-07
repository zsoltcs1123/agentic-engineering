---
name: plan-exec
description: Creates a codebase-aware, file-level implementation plan from a task spec. The only specification skill that reads code. Use when the user wants to plan the exact implementation, says "plan the execution", "create an impl plan", "plan this task", or needs a structured plan for the implement skill.
metadata:
  author: zs
  version: "0.1"
---

# Plan Exec

Create a structured, codebase-aware implementation plan from a task specification. This is the bridge between abstract task specs and concrete code changes.

## When to Use

- Turning a task spec (from `spec-task` or `spec-milestone` output) into an executable plan
- Creating a plan that the `implement` skill can directly execute

## Input

A task specification containing: description, implementation steps, implementation requirements, and verification scenarios.

## What Makes This Different

All other specification skills are abstract — they work without codebase knowledge. `plan-exec` is the only spec skill that reads the actual code. It resolves abstract steps into:

- Exact files to create or modify
- Specific functions/classes to change
- Dependency versions to add
- Test file locations and patterns to follow
- Project conventions to respect

## Output

TODO: Define the codebase analysis process, plan structure, and quality standards.

Intended output: a structured implementation plan matching what the `implement` skill expects — summary, concrete file-level steps, implementation requirements, and verification scenarios.
