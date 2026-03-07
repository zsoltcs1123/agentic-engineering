# Plan Architecture

Create ARCHITECTURE.md defining high-level technical structure, components, and technology choices.

## Role

Technical architect focusing on high-level structure. Challenge technology choices, flag risks, avoid over-engineering.

## Input

- VISION.md (required)
- Context provided by the user in chat, files, or other resources

## Key Questions

- **Components**: What are the main components? How do they interact?
- **Data**: What flows through the system? Where stored?
- **Tech Stack**: What technologies? Why?

For larger projects, also explore:

- **Alternatives**: What other technologies were considered?
- **Scale**: Expected load? Growth? Performance requirements?
- **Security**: Auth? Authorization? Data sensitivity? Compliance?
- **Integrations**: External systems? APIs? Third-party services?
- **Infrastructure**: Hosting? Deployment models? Monitoring?
- **Resilience**: Offline capability? Cache strategy? Fallback behavior?
- **Testing**: Unit/Integration/E2E? Environments? Critical scenarios?

## Process

1. **Context Gathering** - Read VISION.md; understand scope, constraints, and requirements
2. **Scope Confirmation** - Based on VISION.md, propose which optional sections apply (e.g., "This looks like a standard web app — I'd skip multi-tenancy and offline resilience but include security and deployment. Sound right?"). Adjust based on user feedback.
3. **Design** - Define components, data flow, integration points
4. **Selection** - Propose tech stack with rationale and tradeoffs
5. **Documentation** - Create ARCHITECTURE.md with agreed sections

## Output: ARCHITECTURE.md

**Scale the document to the project.** A simple project needs 1-2 pages. An enterprise system may need 10+. Only include sections that add value.

### Section Reference

Title: `# [Project Name] — Architecture`. Use `---` between sections. Required ●, optional ○.

| #   | Section                       | Req | Include When                          | Format                                                                  |
| --- | ----------------------------- | --- | ------------------------------------- | ----------------------------------------------------------------------- |
| 1   | System Overview               | ●   | Always                                | 1-2 paragraphs + ASCII diagram if >3 components + `**Core principle:**` |
| 2   | Technology Stack              | ●   | Always                                | `\| Layer \| Technology \| Rationale \|`                                |
| 3   | Alternatives Considered       | ○   | Major tech choices with alternatives  | `\| Choice \| Alternative \| Why Rejected \|`                           |
| 4   | Components & Responsibilities | ●   | Always                                | Subsection per component with description or table                      |
| 5   | Data Architecture             | ●   | Always                                | Where data lives; include Data Flow if complex                          |
| 6   | Multi-Tenancy Model           | ○   | SaaS or multi-tenant deployments      | Tenant/site isolation strategy                                          |
| 7   | APIs & Integrations           | ○   | External systems or multiple services | Internal APIs + External Integrations tables                            |
| 8   | Security & Compliance         | ○   | Auth complexity, sensitive data       | Auth Flow + Authorization + Data Protection                             |
| 9   | Infrastructure & Deployment   | ○   | Multiple deployment models            | Deployment Models + Resource Requirements tables                        |
| 10  | Scalability & Performance     | ○   | High-load or perf requirements        | Target Scale + Scaling Strategy tables                                  |
| 11  | Offline Resilience            | ○   | Must work without connectivity        | Cache strategy + behavior by scenario                                   |
| 12  | Observability                 | ○   | Production systems needing monitoring | `\| Component \| Technology \| Purpose \|`                              |
| 13  | Testing Strategy              | ○   | Complex test requirements             | `\| Level \| Scope \| Tools \|`                                         |
| 14  | Key Decisions & Tradeoffs     | ●   | Always                                | `\| Decision \| Rationale \| Tradeoff \|`                               |
| 15  | Future Considerations         | ○   | Known evolution paths                 | `\| Item \| Trigger \| Approach \|`                                     |
| 16  | Version History               | ●   | Always                                | `\| Version \| Date \| Changes \|`                                      |

## Quality Standards

**Every decision must have:** rationale and tradeoffs acknowledged.

**Avoid:**

- Over-engineering for hypothetical scale
- Hype-driven technology choices
- Including optional sections that add no value
- Copying the full template when a simpler doc suffices
