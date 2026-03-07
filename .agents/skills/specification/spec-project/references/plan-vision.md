# Plan Vision

Create VISION.md defining the core problem, vision, and strategic direction for the project.

## Role

Strategic planning consultant. Guide users to articulate the problem, vision, and direction before technical implementation. Challenge vague statements, validate assumptions, flag risks early.

## Input

- Context provided by the user in chat, files, or other resources

## Key Questions

1. **Problem**: What specific problem are you solving? Who has it?
2. **Vision**: What does success look like?
3. **Scope**: What's in v1? What's out?
4. **Constraints**: Time/budget? Technical limits? Team size?

For larger projects, also explore:

- **Business Context**: Domain, market, compliance requirements
- **Users & Stakeholders**: Roles, needs, decision-makers
- **Success Metrics**: How will you measure success?
- **Risks**: What could go wrong?

## Process

1. **Discovery** - Ask clarifying questions; understand project scale
2. **Scope Confirmation** - Propose document depth: "This seems like a [simple tool / standard app / enterprise system]. I'd include [sections]. Sound right?"
3. **Analysis** - Synthesize into clear problem statement, define scope boundaries
4. **Documentation** - Create VISION.MD with agreed sections

## Output: VISION.md

**Scale the document to the project.** A weekend project needs half a page. An enterprise system may need 5+.

### Section Reference

Title: `# [Project Name] — Vision`. Use `---` between sections. Required ●, optional ○.

| #   | Section              | Req | Include When                           | Format                                                           |
| --- | -------------------- | --- | -------------------------------------- | ---------------------------------------------------------------- |
| 1   | Executive Summary    | ○   | Enterprise; stakeholders need overview | 1-2 paragraphs                                                   |
| 2   | Problem Statement    | ●   | Always                                 | Who / current state / pain points                                |
| 3   | Vision & Success     | ●   | Always                                 | `**Vision:**` → `**Success looks like:**` → `**Metrics:**` table |
| 4   | Scope                | ●   | Always                                 | In Scope / Out of Scope / Future subsections                     |
| 5   | Users & Stakeholders | ○   | Multiple roles or decision-makers      | `\| Role \| Needs \| Notes \|`                                   |
| 6   | Dependencies         | ○   | External systems/services required     | `\| Dependency \| Version \| Risk \|`                            |
| 7   | Constraints          | ○   | Tech/business/design limits exist      | Technical / Business / Design subsections                        |
| 8   | Risks & Mitigations  | ○   | High-stakes; known unknowns            | `\| Risk \| Likelihood \| Impact \| Mitigation \|`               |
| 9   | Assumptions          | ○   | Unvalidated beliefs driving decisions  | `\| Assumption \| Validation Needed \|`                          |
| 10  | Open Questions       | ○   | Blockers needing resolution            | `\| Question \| Owner \| Due \|`                                 |
| 11  | Decision Log         | ○   | Track key decisions over time          | `\| Date \| Decision \| Rationale \|`                            |
| 12  | Version History      | ●   | Always                                 | `\| Version \| Date \| Changes \|`                               |

## Quality Standards

**Every statement must be:** specific and validated.

**Avoid:**

- Buzzwords without definitions
- Unmeasurable success criteria
- Including optional sections that add no value
- Over-documenting simple projects
