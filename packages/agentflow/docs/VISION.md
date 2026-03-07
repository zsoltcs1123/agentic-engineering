# Agentflow — Vision

## Problem Statement

**Who**: Solo developer building AI-assisted software development workflows.

**Current state**: Two failed attempts at solving the same problem:

1. **Markdown-driven dev-cycle** (`.agents/skills/`): Orchestration logic encoded as markdown interpreted by an LLM at runtime. No observability, no enforced output schemas, no real parallelism, unreliable deterministic operations (git, file I/O) expressed as natural language.

2. **Gateflow** (`packages/gateflow/`): LangGraph-based orchestrator with domain packs, pluggable engines, gate decisions, trust levels, and declarative step definitions. Architecturally sound but LLM-generated and too complex to maintain or evolve. The abstraction surface area grew faster than understanding.

3. **Agentflow v0** (`packages/agentflow/`): Clean reimplementation with 3 hardcoded steps (plan → implement → review), Cursor CLI engine, SQLite checkpointing, Rich terminal UI. Deliberately minimal — a solid foundation, but insufficient for reliable software delivery.

**Pain points**:

- 3 steps are not enough. Code that is implemented and reviewed but never verified against acceptance criteria, never documented, and never committed is incomplete work.
- Steps are hardcoded. Every project has different quality requirements — a throwaway script doesn't need verification; a production service does.
- No gate concept. Review produces output but can't block progress. There's no structured pass/fail decision.
- Only one agent backend (Cursor CLI). No path to Claude Code, Claude SDK, or future agents.
- No rules injection. Consumer projects can't bring their own coding standards, testing rules, or domain conventions.
- No observability beyond Rich console output and basic trace entries.

---

## Vision & Success

**Vision**: A configurable, gated workflow orchestrator that takes a software development task list and executes tasks sequentially and unattended — each task flowing through a customizable pipeline of steps with quality gates that enforce standards before progressing.

**Success looks like**:

- A developer defines a task list, configures their pipeline, provides project-specific rules, and walks away. Agentflow executes each task through the full cycle, stopping only when a gate fails or human intervention is configured.
- Adding a new step or removing an existing one is a configuration change, not a code change.
- Switching from Cursor CLI to Claude Code is an engine swap, not a rewrite.
- A failing review gate produces a structured decision with evidence, not a wall of text.

**Metrics**:

| Metric                                         | Target                                                        |
| ---------------------------------------------- | ------------------------------------------------------------- |
| Steps configurable without code changes        | Yes — via workflow definition                                 |
| Gate failures produce structured decisions     | `GateDecision` with verdict (PASS/BLOCK), reasoning, evidence |
| Engine swap requires zero workflow changes     | Yes — engine is orthogonal to steps                           |
| Consumer project can inject rules              | Yes — rules directory loaded at runtime                       |
| LangGraph Studio compatible                    | Yes — graph inspectable and debuggable in Studio              |
| Task list execution is unattended (happy path) | Yes — gates and interrupts handle the unhappy path            |

---

## Scope

### In Scope (v1)

- **Configurable step pipeline**: Steps defined in a workflow definition file (YAML or JSON). Default pipeline: Plan → Implement → Review → Verify → Document → Commit.
- **Gate model**: Steps can be marked as gates. Gates produce structured `GateDecision` (PASS/BLOCK). BLOCK halts progression.
- **Per-step configuration**: Gate flag, interrupt flag, engine override, permission mode (readonly/write), prompt reference.
- **Rules injection**: Consumer projects provide a rules directory. Rules are loaded and appended to step prompts at runtime.
- **Engine protocol**: `ExecutionEngine` protocol with Cursor CLI as the first implementation.
- **Prompt assembly**: Step prompts loaded from files. Rules appended per-step based on configuration.
- **Context flow**: State accumulates across steps. Steps declare which prior step outputs they need as inputs. The orchestrator auto-injects declared inputs into prompts and validates that dependencies refer to earlier steps.
- **Human-in-the-loop**: Configurable interrupt points. Trust levels (autonomous, gates_only, cautious).
- **Observability**: Structured trace per run — step timing, gate decisions, engine used. LangGraph Studio compatibility for visual debugging.
- **CLI**: `agentflow run <task>` with workflow config path, workdir, model options.
- **Library API**: Programmatic `build_graph()` + `ainvoke()` for embedding in other tools.
- **Checkpointing**: SQLite-based checkpoint/resume via LangGraph.

### Out of Scope

- Multiple domain support (finance, research, etc.) — software development only for now.
- Parallel task execution / workspace isolation (git worktrees, concurrent runs).
- Custom web UI or dashboard.
- Token budget management / cost tracking.
- Scenario-based external evaluation (holdout sets, satisfaction scoring).
- Cursor Cloud API engine.
- Publishing to PyPI.

### Future

- Claude Code / Claude SDK engine implementations.
- Parallel task execution with workspace isolation.
- Token/cost tracking and budget guards.
- Autonomous readiness validation (refuse autonomous mode if specification is insufficient).
- Pyramid summaries for context management on long pipelines.
- Filesystem-as-memory convention for cross-task context (`.agentflow/memory/`).
- Additional domain support if the abstraction proves portable.
- Plugin system for custom step types beyond prompt-and-respond.

---

## Constraints

| Constraint        | Detail                                                                              |
| ----------------- | ----------------------------------------------------------------------------------- |
| Python version    | 3.14+                                                                               |
| Package manager   | uv (workspace member under `packages/agentflow/`)                                   |
| Core dependency   | LangGraph (StateGraph, checkpointing, interrupts)                                   |
| Team size         | Solo developer                                                                      |
| Agent maturity    | Cursor CLI is beta; Claude Code SDK is GA but untested in this context              |
| Network           | Agent shell runs behind corporate proxy — no outbound network in agent shell        |
| Complexity budget | Gateflow failed because it was too complex. Every addition must justify its weight. |

---

## Risks & Mitigations

| Risk                                                      | Likelihood | Impact | Mitigation                                                                                                                       |
| --------------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Over-engineering (repeating gateflow's mistake)           | High       | High   | Implement incrementally. Each phase must produce a working system. No speculative abstractions.                                  |
| LangGraph API instability                                 | Medium     | Medium | Pin versions. Isolate LangGraph behind internal interfaces where practical.                                                      |
| Gate decisions are unreliable (LLM doesn't follow schema) | Medium     | High   | Parse with fallback — malformed output defaults to ISSUES. Validate with structured output / JSON mode where engines support it. |
| Cursor CLI output format changes                          | Medium     | Medium | Isolate parsing behind engine protocol. Single place to fix.                                                                     |
| Context window limits on later steps                      | Medium     | Medium | Design context injection per step — only pass what's needed, not everything.                                                     |
| Scope creep from "one more step" additions                | High       | Medium | Workflow definition is declarative. Adding a step is config, not code — reduces pressure to bake things into the core.           |

---

## Open Questions

| #   | Question                                                                              | Notes                                                                                                                                                                                                                                                            |
| --- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | YAML or JSON for workflow definition?                                                 | YAML is more readable for humans. JSON is simpler to parse. Gateflow used JSON.                                                                                                                                                                                  |
| 2   | Should gate failure halt the entire task or allow human override and resume?          | Current plan: halt. But "modify state and resume" via LangGraph checkpointing is possible.                                                                                                                                                                       |
| 3   | ~~How should the Document step access context from all previous steps?~~              | Resolved: steps declare `inputs` (list of prior step names). The prompt assembler auto-injects those outputs. All outputs also accumulate in `step_outputs` for undeclared access.                                                                               |
| 4   | Should prompts live in the agentflow package (defaults) or only in consumer projects? | Could ship sensible defaults that consumers override.                                                                                                                                                                                                            |
| 5   | What is the boundary between agentflow config and Cursor rules (`.cursor/rules/`)?    | Rules in `.cursor/rules/` are picked up by Cursor automatically. Agentflow rules are injected into prompts. These could overlap or conflict.                                                                                                                     |
| 6   | ~~How should gate failure retry loops work?~~                                         | Resolved: StrongDM Attractor model — `max_retries` + `retry_target` + `goal_gate` on `StepDefinition`. BLOCK loops back to retry_target with issues in context. Now roadmap Phase 5. See [patterns doc](../../docs/strongdm/strongdm-patterns-for-agentflow.md). |

---

## Version History

| Version | Date       | Description                                                                                                 |
| ------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| 1.0     | 2026-02-23 | Initial version                                                                                             |
| 1.1     | 2026-02-23 | Added step dependency model (inputs field) to scope and resolved open question #3                           |
| 1.2     | 2026-02-25 | Retry/convergence promoted from future to roadmap Phase 5; added StrongDM-informed patterns to future scope |
