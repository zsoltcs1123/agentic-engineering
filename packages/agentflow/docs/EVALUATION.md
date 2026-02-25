# Agentflow — Evaluation

**Evaluation Date**: 2026-02-25 (re-evaluation)
**Documents Reviewed**: FOUNDATION.md (v1.2), ARCHITECTURE.md (v1.2), ROADMAP.md (v1.2)
**External Input**: [StrongDM patterns for agentflow](../../docs/strongdm/strongdm-patterns-for-agentflow.md)

---

## Summary

Agentflow is a well-scoped, incrementally planned workflow orchestrator for gated AI-assisted software development. The foundation is honest about past failures, the architecture avoids the over-engineering that killed Gateflow, and the roadmap sequences work correctly — each phase produces a working system.

The main risk is not technical. It's motivational: this is a solo project with an 8-phase roadmap and a hardcoded 3-step prototype. The gap between "where I am" and "Phase 8" is large. The project also faces a positioning question: the market is moving fast, with Copilot Orchestra, Zenflow, Rigour Labs, StrongDM's Software Factory, and the Ralph Wiggum Loop pattern all targeting the same problem space from different angles. Agentflow's value is narrow but defensible — it's your tool, shaped to your workflow, built to be understood.

StrongDM's production Software Factory provides external validation for agentflow's core pattern (configurable pipeline with quality gates and pluggable execution) and contributed a concrete design for the retry/convergence model now in Phase 5. The factory's Attractor spec confirms that the pipeline-with-gates-and-retry architecture works at production scale.

**Recommendation**: Proceed, but scope ruthlessly. Phases 1–5 are the real product — Phase 5 (retry/convergence) is the inflection point where the pipeline can self-correct. Phases 6–8 are nice-to-haves that should only happen if 1–5 prove genuinely useful in daily work. If after Phase 5 you're not using it daily, stop.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation Status |
| --- | --- | --- | --- |
| Motivation decay (solo, long roadmap, no users) | High | High | Partially mitigated — incremental phases help, but no external accountability. Consider: use it yourself after each phase or kill it. |
| Over-engineering repeat (Gateflow 2.0) | Medium | High | Well mitigated in docs. The "every addition must justify its weight" constraint is good. Hold the line. |
| LLM gate reliability (structured JSON from agents) | Medium | High | Conservative fallback (malformed → BLOCK) is correct. But untested. This will be the hardest real-world problem. |
| Cursor CLI instability / output format changes | Medium | Medium | Mitigated — isolated behind engine interface. |
| YAML workflow config becomes its own complexity | Medium | Medium | Not mitigated. No validation beyond "step names unique." Config debugging is a known pain point in declarative systems. |
| ~~No tests in current codebase~~ | ~~High~~ | ~~Medium~~ | Resolved. Test suite now exists: 5 unit test files + 2 integration test files covering graph, CLI, parsing, display, cursor CLI, graph execution, and checkpointing. |
| Context window limits on later steps | Medium | Medium | Partially mitigated. `inputs` declaration helps. Pyramid summaries planned as future phase for large outputs. |
| Market overtake — better tools ship before Phase 8 | Medium | Low | Acceptable. This is a learning project with personal utility. Not a product play. |

---

## Key Findings

### Strengths

1. **Honest post-mortem drives design.** The foundation doesn't hide the two prior failures. Gateflow's failure mode (abstraction surface area grew faster than understanding) directly shapes constraints. This is the most important quality of the plan.

2. **Correct sequencing.** The roadmap dependency graph is right: you can't test engines without a configurable pipeline, and you can't observe gates that don't exist. No phase depends on a future phase.

3. **Separation of concerns is clean.** Orchestrator knows nothing about domain. Prompts, rules, and workflow definitions are consumer-provided. The architecture box diagram is simple and correct.

4. **LangGraph is the right foundation.** Checkpointing, interrupts, conditional edges, Studio compatibility — all of these would be months of DIY work. The framework fits the problem.

5. **Engine protocol is minimal.** `run(prompt, working_directory, mode) -> EngineResult` is the right surface area. Easy to implement for new backends.

6. **External validation from StrongDM's Software Factory.** The most documented production example of fully autonomous software development uses the same core pattern: configurable pipeline, quality gates, pluggable execution, convergence loops. Agentflow's architecture aligns with a system running in production at scale. The Attractor spec also provided a concrete, proven design for retry/convergence (now Phase 5).

### Concerns

1. ~~**Zero tests on a working system is a structural problem.**~~ Resolved. Test suite now covers graph construction, CLI, output parsing, display, cursor CLI engine, graph execution (integration), and checkpointing (integration). The Phase 0 recommendation was followed.

2. **Gate reliability is the load-bearing assumption.** The entire value proposition depends on LLMs producing structured JSON gate decisions reliably. The conservative fallback (malformed → BLOCK) is correct, but in practice this means agents that don't follow instructions will halt every run. No experimentation data exists. **Recommendation**: Build a small test harness in Phase 2 that runs 20+ gate prompts against a real LLM and measures parse success rate. Know the failure rate before building the rest of the system on top of it.

3. **"Configurable" can become "complicated."** The workflow YAML is simple now, but it has `steps`, `gate`, `interrupt`, `readonly`, `engine`, `rules`, `inputs`, `trust_level`, `rules_dir`, `prompts_dir`. That's already 10+ config knobs. Each knob has interaction effects (trust_level × per-step interrupt, default_engine × per-step engine). **Recommendation**: Ship Phase 1 with the minimum viable config. Defer `trust_level`, per-step `engine` override, and `interrupt` flag to later phases. Add them when you need them, not when the architecture says you can.

4. **No dog-fooding plan.** The roadmap doesn't say when you start using Agentflow to develop Agentflow. This is the most powerful validation possible for a developer tool. **Recommendation**: After Phase 3 (prompt/rules assembly), use Agentflow to execute tasks on itself. If it's not useful at that point, reassess.

5. **The "Document" and "Commit" steps are speculative.** They sound reasonable but haven't been validated. Auto-documentation often produces noise. Auto-commit without verification is risky. **Recommendation**: Keep them in the default pipeline but make the Phase 6 validation criterion "did these steps add value on 5+ real tasks?" not just "do they execute?"

---

## Feasibility Assessment

| Phase | Feasibility | Confidence | Notes |
| --- | --- | --- | --- |
| 1 — Workflow Definition | ✅ | 90% | Straightforward dataclass + YAML parsing. Well understood. |
| 2 — Gate Model | ✅ | 75% | Implementation is simple. LLM reliability for structured JSON output is the unknown. |
| 3 — Prompt & Rules Assembly | ✅ | 85% | File loading + string concat. The `inputs` resolution is the only non-trivial part. |
| 4 — Engine Protocol | ✅ | 90% | CursorCLI already matches the protocol shape. Mostly formalization. |
| 5 — Retry/Convergence + Goal Gates | ⚠️ | 70% | Graph topology is well-defined (conditional edges + retry counter). Risk: retry loops are only useful if gates converge — wasted retries if gate quality is poor. StrongDM's Attractor validates the pattern at scale, which raises confidence vs. designing from scratch. |
| 6 — Extended Pipeline | ⚠️ | 60% | Depends on gate quality (Phase 2), prompt quality (Phase 3), and retry convergence (Phase 5) actually working in practice. `agentflow init` adds scope. |
| 7 — Observability & Studio | ⚠️ | 65% | LangGraph Studio compatibility is "verify" not "build," but getting real debugging value requires a working system to debug. |
| 8 — Claude Code Engine | ✅ | 80% | If the protocol holds, this is a new subprocess wrapper. Claude Code CLI is GA. |

---

## Assumptions Requiring Validation

| Assumption | Risk if Invalid | Validation | Timing |
| --- | --- | --- | --- |
| LLMs can reliably produce structured JSON gate decisions | Core value proposition collapses — gates either always block (false negatives) or always pass (useless) | Test harness: 20+ gate prompts, measure parse success rate | Phase 2 |
| YAML config + dataclass validation is sufficient (no Pydantic) | Config errors surface at runtime with bad messages | Deliberately test malformed YAML edge cases | Phase 1 |
| Cursor CLI output format is stable enough to parse | Engine breaks silently | Pin Cursor CLI version, add output format regression tests | Ongoing |
| Declared `inputs` + string concat is sufficient for context injection | Steps get insufficient/wrong context, prompts are brittle | Use on real tasks and evaluate prompt quality | Phase 3 |
| Solo developer can sustain 8-phase roadmap | Project dies at Phase 3 | Dog-food after each phase. Kill or continue based on real utility. | Continuous |
| Retry loops converge (agents improve on retry, not just repeat failures) | Phase 5 retry loops waste compute without improving output | Measure convergence rate: what % of retries eventually pass? | Phase 5 |

---

## Decision Points

| Decision | Owner | Timing | Options |
| --- | --- | --- | --- |
| ~~Should Phase 0 (tests for current system) precede Phase 1?~~ | You | ~~Now~~ | Decided: Yes. Tests written (5 unit + 2 integration). Phase 0 complete. |
| When to start dog-fooding? | You | After Phase 3 | (a) Phase 3. (b) Phase 4. (c) Phase 5. Earlier is better. |
| Kill criteria for the project | You | Define now, evaluate after Phase 5 | If not using daily after Phase 5, stop. |
| ~~Retry loops: never, or gated on data?~~ | You | ~~After Phase 2~~ | Decided: Phase 5 implements retry/convergence using StrongDM Attractor model (`max_retries` + `retry_target` + `goal_gate`). Go/no-go gated on Phase 2 gate reliability data. |

---

## Market & Positioning Context

### Is this just a Ralph Wiggum Loop?

No. The Ralph Wiggum Loop is a single-agent retry pattern: execute → verify → fix → repeat until done. It's a loop, not a pipeline. It has no concept of multiple specialized steps, no quality gates between steps, no structured decisions, no cross-step context flow, no engine abstraction, and no checkpointing.

Agentflow is structurally different: it's a **multi-step pipeline with typed state, quality gates, and pluggable execution**. The Ralph Loop could be one *mechanism within* Agentflow (a future "gate retry loop" feature), but Agentflow itself is an orchestrator, not a retry wrapper.

That said — the Ralph Loop solves a real problem (iteration fatigue) that Agentflow now addresses directly. Phase 5 (Retry/Convergence + Goal Gates) adds retry loops: a gate BLOCK routes back to a target step with the failure issues injected into context, up to `max_retries` attempts. This is the same convergence pattern, formalized as pipeline topology rather than a single-agent loop.

### What exists on the market?

| Tool | Overlap | Difference |
| --- | --- | --- |
| **Copilot Orchestra** (GitHub) | Multi-agent pipeline with planning, implementation, review subagents. Mandatory quality gates and TDD enforcement. | Tied to GitHub Copilot. Not configurable by the consumer. Opinionated pipeline. |
| **Zenflow** (Zencoder) | Spec-driven workflows, parallel multi-agent, verification gates. | Enterprise SaaS. Multi-repo focus. Not a library you control. |
| **Rigour Labs** | Deterministic quality gates for AI agents. Static policy gates, MCP integration. | Gates only — not a full pipeline orchestrator. Complementary, not competing. |
| **CrewAI** | Role-based multi-agent orchestration. | General-purpose agent framework, not software-development-specific. No quality gate concept. |
| **LangGraph (raw)** | Agentflow is built on it. Everything Agentflow does, you could do in raw LangGraph. | Agentflow adds the dev-cycle domain model: steps, gates, prompts, rules, engines. Raw LangGraph is infrastructure. |

Agentflow's niche is narrow: **a configurable, domain-specific orchestrator for solo/small-team software development workflows, built on LangGraph, where you own and understand every line.** None of the market tools target this exact niche. The closest is Copilot Orchestra, but it's locked to GitHub's ecosystem and not configurable.

### Is this what OpenAI built?

Partially overlapping, fundamentally different.

OpenAI's harness engineering (per the report) is a **full engineering system**: repo-as-truth, progressive-disclosure knowledge base, architectural enforcement via linters, agent-bootable application, observability stack, agent-to-agent review (Ralph Wiggum Loop), and automated garbage collection. It's an *environment* — the scaffolding around agents, not an orchestrator over them.

Agentflow is an **orchestrator**: it sequences steps, enforces gates, manages state, and delegates to engines. It's one component of what OpenAI built (roughly their "agent-to-agent review" + "quality gates" layers), not the whole system.

What OpenAI built that Agentflow doesn't address:
- Repository as structured knowledge base (AGENTS.md, docs/ hierarchy)
- Architectural enforcement via linters and structural tests
- Application legibility for agents (bootable per worktree, DevTools integration)
- Per-worktree observability stack
- Continuous garbage collection / background refactoring agents

Agentflow could *become part of* a harness-engineering-style system, but it's not that system by itself. And that's fine — trying to build the whole OpenAI system as a solo developer would be Gateflow 2.0.

### StrongDM's Software Factory

The most documented production example of fully autonomous software development. Three engineers, zero human-written code, zero human code review. Their open-source Attractor spec defines a DOT-graph pipeline orchestrator with typed nodes, convergence loops, and pluggable execution backends.

| Dimension | StrongDM | Agentflow |
| --- | --- | --- |
| Pipeline definition | DOT graph (arbitrary topology) | YAML (linear with gates) |
| Convergence model | `max_retries` + `retry_target` + `goal_gate` | Same model, adopted in Phase 5 |
| Evaluation | External scenarios (holdout set) + satisfaction scoring | LLM-as-judge gates (scenario evaluation is a future phase) |
| Execution backends | Attractor's CodergenBackend (Claude Code, Codex, Cursor) | `ExecutionEngine` protocol (Cursor CLI, Claude Code planned) |
| Testing | Digital Twin Universe (behavioral clones of external dependencies) | Standard test suites — DTU not relevant for agentflow's scope |
| Scale | Production, 3-engineer team, $1K/day/engineer token spend | Solo developer, learning project with personal utility |

StrongDM validates agentflow's core architecture while operating at a much larger scope. The key patterns borrowed: retry/convergence model (Phase 5), goal gates (Phase 5). Deferred patterns: scenario evaluation, autonomous readiness validation, pyramid summaries. Explicitly excluded: DOT syntax, Coding Agent Loop, Digital Twin Universe, Semport. See [full analysis](../../docs/strongdm/strongdm-patterns-for-agentflow.md).

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-02-23 | Initial evaluation |
| 1.1 | 2026-02-25 | Re-evaluation incorporating StrongDM Software Factory patterns: retry/convergence in Phase 5, updated feasibility and risk assessment, StrongDM market context |
| 1.2 | 2026-02-25 | Tests exist: resolved "no tests" risk, concern #1, and Phase 0 decision point |
