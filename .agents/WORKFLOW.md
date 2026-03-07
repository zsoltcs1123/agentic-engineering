# Agentic Development Workflow

How work flows from strategic intent to shipped code.

Inspired by Nate's [four-discipline model](https://natesnewsletter.substack.com/p/prompting-just-split-into-4-different): Prompt Craft, Context Engineering, Intent Engineering, Specification Engineering. Each discipline maps to a concrete mechanism:

| Discipline                | Mechanism                                                                  |
| ------------------------- | -------------------------------------------------------------------------- |
| Prompt Craft              | Reusable skill definitions in `.agents/skills/` and `.cursor/skills/`      |
| Context Engineering       | `AGENTS.md` table-of-contents pattern, `docs/`, cursor rules, Context7 MCP |
| Intent Engineering        | `PRINCIPLES.md` — tradeoff hierarchy, escalation triggers, quality bar     |
| Specification Engineering | Four-level refinement chain (Specification Layer below)                    |

---

## Specification Layer

Successive refinement from broad intent to agent-executable steps. Each level adds the detail the next consumer needs. Four control points prevent spec-to-execution information loss; each level is independently tunable.

| Level     | Artifact                                                        | Skill                                                       |
| --------- | --------------------------------------------------------------- | ----------------------------------------------------------- |
| Blueprint | Full product spec or roadmap                                    | `spec-project`                                              |
| Milestone | One phase/module — task list + validation suite                 | `spec-milestone`, `spec-tasks`, `spec-validations`          |
| Task      | Single task — description, requirements, verification scenarios | `spec-task`                                                 |
| Plan      | Structured executable plan — codebase-aware, file-level steps   | `plan-exec`                                                 |

Pipeline: Blueprint &rarr; Milestone &rarr; Task &rarr; Plan.

---

## Execution Layer

Four execution levels mirroring the spec levels. Each wraps the one below — its only added responsibility is orchestration (prepare or iterate, then delegate down).

| Level             | Input                        | What it does                                         | Skill       |
| ----------------- | ---------------------------- | ---------------------------------------------------- | ----------- |
| Execute Plan      | Structured plan              | Runs the plan to a shipped commit.                   | `dev-cycle` |
| Execute Task      | Task entry                   | Creates a structured plan, then calls Execute Plan.  | (planned)   |
| Execute Milestone | Task list + validation suite | Iterates each task via Execute Task, then validates. | (planned)   |
| Execute Blueprint | Full product spec / roadmap  | Iterates each milestone via Execute Milestone.       | (planned)   |

Pipeline: Execute Blueprint &rarr; Execute Milestone &rarr; Execute Task &rarr; Execute Plan.

### Execute Plan (innermost)

Takes a structured plan and drives it to a shipped commit. One feedback loop: Review can send work back to Implement.

| Step      | What happens                                                                                                               | Skill         |
| --------- | -------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Implement | Write code and tests. Iterate until tests and lint are green. Run verification scenarios. Update knowledge base if needed. | `implement`   |
| Review    | Run code review. If issues found, loop back to Implement. Repeat until clean.                                              | `code-review` |
| Document  | Write or update project documentation.                                                                                     | `document`    |
| Finalize  | Commit. Optionally push and open PR.                                                                                       | `finalize`    |

---
