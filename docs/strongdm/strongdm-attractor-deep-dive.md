# StrongDM Attractor & Software Factory — Deep Dive

Source: [StrongDM Software Factory](https://factory.strongdm.ai/) + [Attractor repo](https://github.com/strongdm/attractor) (Feb 2026)
Author: Justin McCarthy (CTO), Jay Taylor, Navan Chauhan — StrongDM

StrongDM's Software Factory is the most documented production example of fully autonomous software development. Three engineers, zero human-written code, zero human code review. Attractor is their open-source non-interactive coding agent — published not as code but as NLSpecs (natural language specifications) that any modern coding agent can implement. The factory's core innovation is treating code like ML model weights: opaque artifacts validated exclusively by externally-observable behavior, never by reading the source.

---

## Key Learnings

**1. Attractor is a DOT-graph pipeline orchestrator, not a chat agent.**
Workflows are defined as directed graphs in Graphviz DOT syntax. Nodes are typed handlers (LLM task, human gate, conditional, parallel fan-out, tool execution, supervisor loop). Edges carry conditions, weights, and routing logic. The `.dot` file *is* the workflow — declarative, visual, version-controllable. This is fundamentally different from the prompt-response paradigm.

**2. The scenario/satisfaction model replaces traditional testing.**
Tests stored inside a codebase can be reward-hacked by agents (`return true` passes the test but isn't correct software). StrongDM uses "scenarios" — end-to-end behavioral specifications stored *outside* the codebase, functioning like a holdout set in ML training. The agent never sees the evaluation criteria. "Satisfaction" is a probabilistic measure: across all observed trajectories through all scenarios, what fraction likely satisfy the user? This shifts from boolean pass/fail to empirical confidence.

**3. Digital Twin Universe (DTU) makes high-fidelity integration testing economically feasible.**
Behavioral clones of Okta, Jira, Slack, Google Docs, Drive, and Sheets — replicating APIs, edge cases, and observable behaviors. Enables thousands of scenarios/hour without rate limits, API costs, or abuse detection. Previously building a full in-memory replica of a SaaS dependency was technically possible but economically absurd. AI agents changed the cost equation — building the twins *is* factory work.

**4. Six reusable techniques form the factory's operational playbook.**

| Technique | What | Why it matters |
| --- | --- | --- |
| **Digital Twin Universe** | Behavioral clones of external dependencies | Deterministic, unlimited-volume validation |
| **Gene Transfusion** | Point agent at a working exemplar, synthesize equivalent in new context | Pattern reuse without shared authorship |
| **Filesystem as Memory** | Agents build indexes, write state, reorganize context on disk | Persistent, inspectable, composable agent memory across sessions |
| **Shift Work** | Separate interactive (intent formation) from non-interactive (execution) | Once intent is complete, the agent runs end-to-end without back-and-forth |
| **Semport** | Semantically-aware automated porting between languages/frameworks | Benefit from upstream libraries without being constrained by their language/dependencies |
| **Pyramid Summaries** | Reversible multi-zoom-level summarization (2 words → 4 → 8 → 16...) | Agents survey hundreds of items compressed, expand only where signal demands |

**5. The Coding Agent Loop spec is a language-agnostic blueprint for building your own agent.**
Not tied to any specific LLM. Defines: agentic loop, provider-aligned toolsets (each model family gets its native tools), execution environment abstraction (local/Docker/K8s/WASM), event-driven architecture, subagent spawning, steering/follow-up queues, context management with truncation. This is a composable library, not a CLI — the host application controls every step.

**6. "Compounding correctness" was the inflection point.**
Before Claude 3.5 Sonnet rev 2 (October 2024), iterative AI coding accumulated errors until the system collapsed. After that model, long-horizon agentic coding began compounding correctness instead — the model could sustain coherent work across sessions. This single capability shift is what made the factory viable.

**7. The factory requires "deliberate naivete" about old constraints.**
Many engineering practices are habits from a world of expensive human labor, not physical laws. Building a full DTU of external dependencies, spending $1,000/day/engineer on tokens, not reviewing code — these feel wrong because we're applying outdated economic intuitions. The factory asks: *why am I doing this?* (implied: the model should be doing this instead).

---

## Actionable Takeaways

- Study the Attractor spec's DOT-based pipeline approach as a pattern for orchestrating multi-stage agent workflows — it's more structured than prompt chains and more flexible than hardcoded pipelines.
- Separate test/evaluation from the agent's development context. If the agent can read the tests, it can game them. External scenarios + satisfaction scoring is the pattern.
- Consider building DTUs for your critical external dependencies — the economics have flipped.
- Apply the Shift Work distinction: identify which work in your org is truly interactive (intent still forming) vs. non-interactive (intent complete, execution can be fully automated).
- Pyramid Summaries + MapReduce is a practical pattern for letting agents reason over large codebases without context window limits.
- The Coding Agent Loop spec is implementable — it's designed so you can tell Claude Code "implement this" and get a working agent. Worth doing as a learning exercise at minimum.

---

## Architecture: Attractor Pipeline

```
.dot file (workflow graph)
    │
    ├─ Nodes: LLM tasks, human gates, conditionals, parallel fan-out, tool exec
    ├─ Edges: conditions, weights, routing labels
    │
    ▼
Pipeline Engine (parse → validate → initialize → execute → finalize)
    │
    ├─ Checkpoint/resume after each node
    ├─ Edge-based routing with condition expressions
    ├─ Model Stylesheet (CSS-like per-node LLM config)
    │
    ▼
CodergenBackend (pluggable: Claude Code, Codex, Cursor, etc.)
    │
    ▼
Coding Agent Loop (agentic loop library)
    │
    ├─ Provider-aligned toolsets
    ├─ Execution environment abstraction
    ├─ Steering/follow-up queues
    ├─ Subagent spawning
    │
    ▼
Unified LLM Client (provider-agnostic API layer)
```

---

## Validation Architecture

```
Specifications (markdown, in codebase)
    │
    ▼
Agent builds code (opaque — treated like ML model weights)
    │
    ▼
Scenarios (behavioral specs, OUTSIDE codebase — holdout set)
    │
    ├─ Run against Digital Twin Universe (simulated dependencies)
    ├─ LLM-as-judge for agentic/non-deterministic behavior
    │
    ▼
Satisfaction score (probabilistic, not boolean)
    │
    ▼
Loop until holdout scenarios pass and stay passing
```

---

## Further Investigation

- How does StrongDM handle specification drift — when the scenarios and specs diverge over time?
- What's the failure mode when the DTU's behavioral clone diverges from the real service's behavior?
- Can the scenario/satisfaction model work for brownfield systems, or only greenfield?
- Attractor's `stack.manager_loop` (supervisor pattern) — how does it handle multi-agent coordination in practice?
- What does the $1,000/day/engineer token spend actually buy in terms of agent runs, and what's the marginal return curve?
