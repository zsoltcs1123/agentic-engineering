---
name: spec-project
description: Guide users through creating project planning documents (VISION.md, ARCHITECTURE.md, ROADMAP.md, EVALUATION.md). Use when: planning a new project, defining architecture, creating roadmaps, evaluating feasibility, writing technical specs, or when user mentions "vision doc", "architecture doc", "roadmap", or "project evaluation".
metadata:
  author: zs
  version: "1.5"
---

# Spec Project

Guide users through creating, updating, or evaluating project planning documents.

## When Activated

Determine user intent and route to the appropriate workflow:

| User Intent                    | Action                                                                            |
| ------------------------------ | --------------------------------------------------------------------------------- |
| "Start planning a new project" | → Create Vision                                                                   |
| "Design the architecture"      | → Create Architecture (requires VISION.md)                                        |
| "Create a roadmap"             | → Create Roadmap (requires VISION.md + ARCHITECTURE.md)                           |
| "Evaluate/review this project" | → Evaluate                                                                        |
| "Update [document]"            | → Update                                                                          |
| Unclear intent                 | Ask: "Do you want to **create**, **update**, or **evaluate** planning documents?" |

## Documents

| Document        | Purpose                                                    | Prerequisites                  |
| --------------- | ---------------------------------------------------------- | ------------------------------ |
| VISION.md       | Problem, vision, constraints, success criteria             | None                           |
| ARCHITECTURE.md | Technical structure, components, data models, tech choices | VISION.md                      |
| ROADMAP.md      | Phased implementation plan                                 | VISION.md, ARCHITECTURE.md     |
| EVALUATION.md   | Independent feasibility assessment                         | All planning docs              |

## Workflows

### Create

**Sequence matters.** Create documents in order: VISION → ARCHITECTURE → ROADMAP.

For each document:

1. Read the reference file (see table below) and follow its instructions
2. End with Version History section

| Document        | Reference                                                          |
| --------------- | ------------------------------------------------------------------ |
| VISION.md       | [references/plan-vision.md](references/plan-vision.md)             |
| ARCHITECTURE.md | [references/plan-architecture.md](references/plan-architecture.md) |
| ROADMAP.md      | [references/plan-roadmap.md](references/plan-roadmap.md)           |

### Evaluate

Independent assessment of project feasibility and risks.

1. Load all existing planning documents (VISION.md, ARCHITECTURE.md, ROADMAP.md)
2. Read [references/evaluate-project.md](references/evaluate-project.md) and follow its instructions
3. Output EVALUATION.md with Version History section

### Update

1. Read the target document fully
2. Read the corresponding reference file to validate structure
3. Clarify scope with user if needed
4. Apply changes while maintaining section structure from reference
5. Bump version for: new sections, major rewrites, scope changes. Skip for typos/formatting.

### Re-evaluate

After planning documents change:

1. Read updated planning documents
2. Compare against previous evaluation
3. Reassess affected sections
4. Update EVALUATION.md and bump version

## Version History

**Mandatory** for all created documents:

```markdown
## Version History

| Version | Date       | Description     |
| ------- | ---------- | --------------- |
| 1.0     | YYYY-MM-DD | Initial version |
```

Bump version for significant changes. Skip for typos/formatting.

## Communication Style

- **Concise**: Minimal words, maximum meaning
- **Specific**: Concrete details over vague statements
- **Clear**: Plain language; avoid jargon
- **Actionable**: Practical, implementable guidance

**Behaviors:**

- Ask clarifying questions before assuming
- Present options when multiple valid approaches exist
- Explain reasoning behind recommendations
- Flag risks early
- Maintain consistency across documents
