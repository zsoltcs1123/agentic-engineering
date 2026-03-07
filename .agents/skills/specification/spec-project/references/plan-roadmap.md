# Plan Roadmap

Create ROADMAP.md breaking the project into logical phases with clear deliverables and sequencing.

## Role

Implementation strategist. Guide users to sequence work effectively, identify dependencies, and plan iterative delivery. Challenge unrealistic breakdowns.

## Input

- VISION.md and ARCHITECTURE.md (required)
- Context provided by the user in chat, files, or other resources

## Key Questions

- **Phases**: What are the logical phases? What does each deliver?
- **Sequencing**: What must be built first? What can be parallel?
- **Milestones**: How do you know a phase is complete?

For larger projects, also explore:

- **Releases**: How do phases group into releases (v1, v2)?
- **Dependencies**: External blockers? Team dependencies?
- **Risks**: What could derail each phase? Mitigation?
- **Learning**: What does each phase teach you?
- **Constraints**: Team size, tooling, parallelization limits?

## Process

1. **Context Gathering** - Read VISION.md and ARCHITECTURE.md; understand scope
2. **Scope Confirmation** - Based on project complexity, propose roadmap depth: "This looks like a [simple / multi-phase / enterprise] project. I'd include [sections]. Sound right?"
3. **Phase Definition** - Break into logical phases, define deliverables
4. **Sequencing** - Determine order, find parallel opportunities
5. **Documentation** - Create ROADMAP.md with agreed sections

## Output: ROADMAP.md

**Scale the document to the project.** A simple project needs a phase list. An enterprise project may need detailed breakdowns with risk analysis.

### Section Reference

Title: `# [Project Name] — Roadmap`. Use `---` between sections. Required ●, optional ○.

| #   | Section                       | Req | Include When                              | Format                                               |
| --- | ----------------------------- | --- | ----------------------------------------- | ---------------------------------------------------- |
| 1   | Overview                      | ●   | Always                                    | 1-2 paragraphs: scope, sequencing rationale          |
| 2   | Phase Summary                 | ●   | Always                                    | `\| Phase \| Name \| Key Outcome \|`                 |
| 3   | Phase Details                 | ●   | Always                                    | Per-phase: **Goal**, **Deliverables**, **Done when** |
| 4   | Development Constraints       | ○   | Team size, estimation units matter        | Team size, estimation unit, buffer policy            |
| 5   | Timeline Summary              | ○   | Multiple releases with duration estimates | `\| Release \| Phases \| Duration \| Team \|`        |
| 6   | Release Scopes                | ○   | Grouping phases into v1, v2, etc.         | Per-release: Phases, Scope, Milestone                |
| 7   | Parallel Opportunities        | ○   | Team can work on multiple things at once  | `\| Activity \| Can Run Parallel With \|`            |
| 8   | External Dependencies         | ○   | Blockers outside your control             | `\| Dependency \| Needed By \| Risk \|`              |
| 9   | Milestones & Success Criteria | ○   | Need formal checkpoints                   | Milestone list with criteria                         |
| 10  | Risk & Mitigation             | ○   | High-stakes phases with known risks       | `\| Phase \| Risk \| Likelihood \| Mitigation \|`    |
| 11  | Learning Points               | ○   | Phases inform subsequent decisions        | `\| Phase \| What We Learn \| Informs \|`            |
| 12  | Future Phases                 | ○   | Known work deferred beyond current scope  | `\| Phase \| Focus \| Trigger \|`                    |
| 13  | Version History               | ●   | Always                                    | `\| Version \| Date \| Changes \|`                   |

## Quality Standards

**Each phase must have:** goal, deliverables, done criteria.

**Avoid:**

- Phases too large (>4 sprints) or too granular (<1 sprint)
- Over-documenting simple projects
- Risks without mitigation
- Ignoring parallelization opportunities
