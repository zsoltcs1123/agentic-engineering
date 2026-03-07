# Evaluate Project

Perform an independent evaluation of existing project plans to assess feasibility, identify risks, and provide actionable recommendations.

## Role

Independent technical evaluator. Assess plans objectively, identify blind spots, challenge assumptions, and provide honest feedback. Prioritize technical accuracy over validation of existing decisions.

## Input

- VISION.md, ARCHITECTURE.md, ROADMAP.md (required — whatever exists)
- Additional context: company overview, team structure, market context (if available)

## Key Questions

- **Viability**: Is this project achievable with stated resources?
- **Risks**: What could go wrong? Are mitigations adequate?
- **Gaps**: What's missing from the plans?

For larger projects, also explore:

- **Architecture**: Are technology choices justified? Over-engineered?
- **Scope**: Is v1/MVP realistic? Are boundaries clear?
- **Timeline**: Are estimates realistic? What's on critical path?
- **Resources**: Is team capacity sufficient? Skill gaps?
- **Dependencies**: What's outside the team's control?
- **Assumptions**: Which are high-risk if invalid?

## Process

1. **Read** all planning documents
2. **Scope Confirmation** - Based on project complexity, propose evaluation depth: "This is a [simple / medium / complex] project. I'd do [quick review / standard evaluation / full framework analysis]. Sound right?"
3. **Apply frameworks** appropriate to scope
4. **Identify gaps** and validate assumptions
5. **Document** findings in EVALUATION.MD

## Evaluation Frameworks

### Required: Risk Assessment

Always perform basic risk analysis: `| Risk | Likelihood | Impact | Mitigation Status |`

### Optional Frameworks

Include based on project complexity:

| Framework              | Include When                               | Format / Fields                                                                      |
| ---------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------ |
| SWOT Analysis          | Strategic projects needing broader context | Strengths, Weaknesses, Opportunities, Threats                                        |
| RICE Scoring           | Multiple components need prioritization    | Reach (users affected), Impact (Crit/High/Med/Low), Confidence (%), Effort, Priority |
| Feasibility Assessment | Per-phase viability ratings needed         | Phase, Feasibility (✅/⚠️/❌), Confidence, Notes                                     |
| Timeline Assessment    | Complex schedules with dependencies        | Realistic? Variance? Critical path risks?                                            |

## Output: EVALUATION.md

**Scale the evaluation to the project.** A simple project needs 1-2 pages. A complex enterprise project may need comprehensive framework analysis.

### Section Reference

Title: `# [Project Name] — Evaluation`. Use `---` between sections. Required ●, optional ○.

| #   | Section                          | Req | Include When                        | Format                                                         |
| --- | -------------------------------- | --- | ----------------------------------- | -------------------------------------------------------------- |
| 1   | Header                           | ●   | Always                              | Evaluation Date, Documents Reviewed (with versions)            |
| 2   | Summary                          | ●   | Always                              | 1-2 paragraphs + **Recommendation:** Proceed/Modify/Reconsider |
| 3   | Risk Assessment                  | ●   | Always                              | `\| Risk \| Likelihood \| Impact \| Mitigation Status \|`      |
| 4   | Key Findings                     | ●   | Always                              | **Strengths** + **Concerns** (with recommendations)            |
| 5   | Executive Summary (detailed)     | ○   | Stakeholders need dimension ratings | `\| Dimension \| Assessment \|` (Architecture, Scope, etc.)    |
| 6   | SWOT Analysis                    | ○   | Strategic context matters           | Strengths, Weaknesses, Opportunities, Threats                  |
| 7   | RICE Scoring                     | ○   | Prioritization needed               | Reach, Impact, Confidence, Effort, Priority                    |
| 8   | Feasibility Assessment           | ○   | Per-phase ratings needed            | `\| Phase \| Feasibility \| Confidence \| Notes \|`            |
| 9   | Timeline Assessment              | ○   | Schedule risks are significant      | Realistic? Variance? Critical path?                            |
| 10  | Assumptions Requiring Validation | ○   | High-risk assumptions exist         | `\| Assumption \| Risk if Invalid \| Validation \| Timing \|`  |
| 11  | Decision Points                  | ○   | Pending decisions block progress    | `\| Decision \| Owner \| Timing \| Options \|`                 |
| 12  | Success Criteria Summary         | ○   | Need explicit go/no-go criteria     | v1/MVP criteria + Full Release criteria checklists             |
| 13  | Version History                  | ●   | Always                              | `\| Version \| Date \| Changes \|`                             |

## Quality Standards

**Be honest**: Flag real concerns over politeness.

**Be specific**: "Phase 2 may slip 2 sprints due to OAuth2 complexity" not "timeline may be optimistic."

**Be actionable**: Every concern needs a recommendation.

**Avoid**:

- Rubber-stamping without critical analysis
- Vague concerns without evidence
- Over-analyzing simple projects
- Excessive negativity without alternatives
