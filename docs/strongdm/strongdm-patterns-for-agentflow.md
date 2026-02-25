# What to Steal from StrongDM's Software Factory for Agentflow

## Context

Agentflow is a configurable workflow orchestrator built on LangGraph. It runs a pipeline of steps (plan → implement → review → ...), each delegating to a pluggable execution engine (currently Cursor CLI). It has checkpointing, trust levels, and a roadmap toward quality gates, retry loops, and autonomous execution.

StrongDM's Software Factory is a production system where three engineers run fully autonomous software development — spec in, software out, no human code or review. Their open-source Attractor spec and factory documentation describe patterns that directly address open questions in agentflow's architecture.

This report maps six StrongDM patterns to concrete changes in agentflow. Ordered by impact and implementation dependency.

---

## 1. Retry/Convergence Model

### The StrongDM pattern

Attractor nodes have `max_retries` (integer, default 50) and `retry_target` (node ID to jump back to on failure). `goal_gate` nodes must reach SUCCESS before the pipeline can exit. The pipeline loops between implementation and evaluation until the holdout scenarios pass — or until retries are exhausted.

The key insight: gates don't just block. They loop back. A BLOCK verdict sends the pipeline to `retry_target` with the failure context appended, so the implementing agent gets the feedback and tries again. The convergence loop is: implement → evaluate → issues found → re-implement with issues → re-evaluate → ... until PASS or max retries hit.

### What agentflow has today

Gate failure halts the pipeline (`BLOCK → END`). The architecture doc explicitly calls retry loops an "open design question" and the roadmap defers them to Phase 8, gated on "confidence in gate quality."

### What to steal

Add three fields to `StepDefinition`:

```yaml
- name: review
  prompt: review
  gate: true
  max_retries: 3        # NEW: retry up to 3 times on BLOCK
  retry_target: implement  # NEW: jump back to implement on BLOCK
  goal_gate: false       # NEW: if true, pipeline cannot complete until this gate passes
```

Change the graph builder's gate routing:

| Current | New |
|---|---|
| BLOCK → END | BLOCK + retries remaining → retry_target (with issues in context) |
| | BLOCK + retries exhausted → END |
| PASS → next step | PASS → next step (unchanged) |

The retry context injection matters: when the pipeline loops back to `retry_target`, the issues from the failed gate must be appended to the step's input context. The implementing agent needs to know *what went wrong*, not just that it failed. This means the `step_outputs` accumulator should store the gate's `GateDecision.issues` and the prompt assembler should inject them when a step is being retried.

Add a `retry_count` to `WorkflowState` (keyed by step name) so the graph builder can track how many times a gate has looped.

### Where it fits in the roadmap

This replaces Phase 8 (Gate retry loops) and should be pulled forward — it's the single most important feature for moving from `gates_only` to `autonomous` trust level. Without retry loops, autonomous mode means the pipeline halts on every BLOCK with no path to self-correction. With retry loops, the pipeline can converge on its own.

**Prerequisite**: Phase 2 (Gate Model) must be done first, since retry routing depends on structured `GateDecision` output.

---

## 2. Scenarios as External Holdout Evaluation

### The StrongDM pattern

Traditional tests live inside the codebase. The agent can read them, which means it can (intentionally or not) optimize for passing tests rather than building correct software. `return true` passes a narrow unit test but isn't correct software.

StrongDM replaces tests with "scenarios" — end-to-end behavioral specifications stored *outside* the codebase. The agent never sees the evaluation criteria. This is analogous to an ML holdout set: the training data (specs, codebase) is separate from the evaluation data (scenarios). The agent builds against specs; scenarios evaluate whether the build is actually correct.

"Satisfaction" replaces boolean pass/fail. It's a probabilistic measure: across all observed trajectories through all scenarios, what fraction likely satisfy the user? This handles non-deterministic behavior (agentic code, LLM-based features) where boolean tests would be flaky.

### What agentflow has today

Gate steps ask an LLM to review the work. The review prompt says "check the diff" or "verify against the plan." The LLM reads the code and gives a verdict. This is vulnerable to the same problem: the evaluating LLM is reading the same codebase the implementing LLM wrote. It's not a holdout — it's the same data.

### What to steal

Introduce a `scenarios_dir` concept — a directory of behavioral scenarios stored outside the working directory, not visible to the implementing engine:

```yaml
default_engine: cursor-cli
scenarios_dir: ./scenarios   # NEW: external to the workdir

steps:
  - name: implement
    prompt: implement
    readonly: false

  - name: verify
    prompt: verify
    gate: true
    evaluation: scenario     # NEW: run scenarios instead of LLM review
    max_retries: 3
    retry_target: implement
```

A scenario file describes expected behavior from the outside:

```yaml
# scenarios/user-login.yaml
name: User can log in with valid credentials
steps:
  - action: "Run the application"
  - action: "Submit login form with valid credentials"
  - expect: "User is redirected to dashboard"
  - expect: "Session token is set"
```

The verification step runs these scenarios against the built software (via the engine — e.g., run the test suite, hit the endpoints, check the outputs) and measures satisfaction: how many scenarios pass, how confident are we that the software behaves correctly?

This is a bigger architectural addition than the retry model. The practical starting point:

1. **Phase A**: Define scenarios as markdown files describing expected behavior. The verify step's prompt includes these scenarios and asks the engine to check each one. The scenarios live outside `workdir` so the implementing agent never sees them. This is a prompt-level separation — not airtight, but functional.

2. **Phase B**: Formalize scenario execution. The verify step doesn't just ask an LLM — it runs the scenarios programmatically (shell commands, HTTP requests, file assertions) and reports results. This requires a scenario runner, which is a separate component.

3. **Phase C**: Satisfaction scoring. Instead of boolean PASS/BLOCK, the gate returns a confidence score (0.0–1.0). The threshold for PASS is configurable per gate. This handles non-deterministic behavior gracefully.

### Where it fits in the roadmap

This is a new capability layer, not covered in the current roadmap. It should come after Phase 2 (Gate Model) and Phase 5 (Extended Pipeline), since it extends the gate concept. It could be Phase 8, replacing the current "Gate retry loops" phase (which is subsumed by pattern #1 above).

---

## 3. Shift Work: Interactive vs. Non-Interactive Separation

### The StrongDM pattern

StrongDM distinguishes between two modes of system growth:

- **Interactive**: Intent is still forming. Human and agent collaborate — generate, clarify, generate, approve, correct. This is Cursor in your IDE.
- **Non-interactive**: Intent is complete. Specs, scenarios, and constraints are fully defined. The agent runs end-to-end without human interaction.

The factory only handles non-interactive work. Interactive work happens before the factory — it's where humans define what should exist.

### What agentflow has today

Trust levels (`cautious`, `gates_only`, `autonomous`) partially express this, but there's no explicit concept of "this task's intent is complete enough for non-interactive execution." The human decides by choosing a trust level. There's no validation that the specification is actually sufficient for autonomous execution.

### What to steal

Add a **readiness check** before pipeline execution in autonomous mode. When `trust_level: autonomous`, the orchestrator validates that the task has:

- A specification (not just a one-line task description)
- Scenarios defined for the verify step (if scenario evaluation is configured)
- All required prompt inputs available

If the readiness check fails, the pipeline refuses to run in autonomous mode and falls back to `gates_only` with a message explaining what's missing. This prevents the "garbage in, garbage out" failure mode where an underspecified task runs autonomously and produces useless output.

In `workflow.yaml`:

```yaml
trust_level: autonomous
autonomous_requires:    # NEW
  - min_task_length: 200    # task description must be at least 200 chars
  - scenarios: true          # scenarios_dir must have at least one scenario
  - spec_file: true          # a spec.md file must exist in workdir
```

This is lightweight to implement and high value: it encodes the Shift Work boundary explicitly. Interactive work (intent not yet complete) stays at `cautious` or `gates_only`. Non-interactive work (intent fully specified) runs at `autonomous` — but only if the specification actually meets the bar.

### Where it fits in the roadmap

After Phase 5 (Extended Pipeline) when trust levels are implemented. Small addition to the CLI/validation layer.

---

## 4. Goal Gates: Required-Pass Nodes

### The StrongDM pattern

Attractor has a `goal_gate` flag on nodes. If `goal_gate=true`, the node *must* reach SUCCESS before the pipeline can exit. Even if the pipeline reaches the exit node, if any goal gate hasn't passed, the engine jumps to the `retry_target` and tries again (up to `max_retries`).

This is different from a regular gate. A regular gate blocks progression. A goal gate blocks *completion*. The pipeline can proceed past a goal gate node, but it can't finish until all goal gates have been satisfied.

### What agentflow has today

Gates block progression only. `BLOCK → END` or (with pattern #1) `BLOCK → retry_target`. There's no concept of "this gate must eventually pass for the pipeline to be considered successful."

### What to steal

Add `goal_gate: bool` to `StepDefinition`. In the graph builder, after the final step (before END), add a conditional check: if any `goal_gate` step has a BLOCK verdict, route back to the first unsatisfied goal gate's `retry_target` instead of END.

This matters for the commit/finalize step. You don't want to commit code that failed verification. The goal gate on `verify` ensures the pipeline doesn't reach `commit` unless verification has passed — and if it somehow does (due to non-gate steps in between), the exit check catches it.

```yaml
steps:
  - name: verify
    gate: true
    goal_gate: true          # pipeline cannot complete unless this passes
    max_retries: 3
    retry_target: implement
```

### Where it fits in the roadmap

Implement alongside pattern #1 (Retry/Convergence). They're the same system — goal gates are retry triggers at the pipeline exit rather than at the gate node itself.

---

## 5. Pyramid Summaries for Context Management

### The StrongDM pattern

"Summarize this in 2 words. Now 4. Now 8. Now 16." Each level preserves essential meaning while expanding or contracting detail. Agents survey hundreds of items at the compressed level, identify interesting ones, and expand only those. Combined with MapReduce and clustering, a model with limited context can "see" the full terrain of a problem.

### What agentflow has today

`step_outputs` stores full output from each step. The prompt assembler injects these into the next step's prompt via the `inputs` declaration. For large outputs (e.g., a plan that spans 50 files, or a review with dozens of issues), this can overflow context or dilute attention.

### What to steal

Add a `summary_level` option to the `inputs` declaration:

```yaml
- name: document
  prompt: document
  inputs:
    - name: plan
      summary: 16      # inject 16-word summary of plan output
    - name: review
      summary: full     # inject full review output
    - name: verify
      summary: 64       # inject 64-word summary of verify output
```

The prompt assembler generates summaries at the requested word count before injection. This keeps context tight for steps that only need an overview (documentation doesn't need the full plan — just what was done) while preserving full detail for steps that need it (review needs the full plan to check against).

Implementation: a utility function that asks the engine (or a lightweight LLM call) to summarize text at a target word count. Cache summaries in `step_outputs` keyed by `{step_name}:summary:{level}`.

### Where it fits in the roadmap

After Phase 3 (Prompt & Rules Assembly), since it extends the prompt assembler. Low priority — context overflow won't be a problem until pipelines are longer and outputs are larger.

---

## 6. Filesystem as Agent Memory

### The StrongDM pattern

Agents build an on-disk index, write scratch state, and rehydrate context by reading files. The filesystem becomes a persistent, inspectable, composable memory substrate. Agents create directories with meaningful names, write Markdown indexes, and reorganize as the hierarchy grows (the library-science concept of "genrefying").

### What agentflow has today

State lives in LangGraph's checkpoint store (SQLite). Step outputs live in `WorkflowState.step_outputs`. There's no persistent filesystem-based context that accumulates across tasks or across pipeline runs.

### What to steal

This isn't an orchestrator feature — it's a **prompt/rule pattern**. Add to your prompts and rules:

1. **Agent workspace convention**: Each task gets a `.agentflow/context/` directory in the workdir. The implementing agent is instructed (via the implement prompt) to write an index file summarizing what it did, what decisions it made, and what files it touched.

2. **Cross-task memory**: A `.agentflow/memory/` directory persists across tasks. Each completed task appends a summary. Future tasks' plan steps are instructed to read this memory before planning, giving them context about prior work in the same codebase.

3. **Pyramid index**: The memory directory maintains a pyramid-structured index — a 2-word summary of each past task, expandable to full detail. The plan step reads the compressed index; it only expands entries that seem relevant.

This requires no orchestrator changes — just prompt engineering and a convention for filesystem layout. The orchestrator doesn't manage the memory; the agents do, guided by prompts.

### Where it fits in the roadmap

Anytime. It's prompt/rule work, not code work. Start with a simple convention in the implement and plan prompts and iterate.

---

## Implementation Priority

| # | Pattern | Impact | Effort | Depends on | Roadmap phase |
|---|---------|--------|--------|------------|---------------|
| 1 | Retry/convergence | Critical — enables autonomous mode | Medium | Phase 2 (gates) | Replace Phase 8, pull forward |
| 4 | Goal gates | High — prevents incomplete pipelines | Low | Pattern #1 | Same as #1 |
| 3 | Shift Work readiness | High — safety gate for autonomous mode | Low | Phase 5 (trust levels) | After Phase 5 |
| 2 | Scenario evaluation | High — real evaluation quality | High | Phase 2, Phase 5 | New Phase 8 |
| 6 | Filesystem memory | Medium — cross-task context | Low | None (prompt work) | Anytime |
| 5 | Pyramid summaries | Medium — context management | Medium | Phase 3 (prompts) | After Phase 3 |

### Critical path to autonomous software factory

```
Current state (3-step hardcoded pipeline)
    │
    ▼ Roadmap Phases 1-4 (workflow def, gates, prompts, engine protocol)
    │
    ▼ Pattern #1 + #4 (retry/convergence + goal gates)
    │  ← This is the inflection point: pipeline can self-correct
    │
    ▼ Pattern #3 (Shift Work readiness check)
    │  ← Pipeline refuses autonomous mode unless spec is sufficient
    │
    ▼ Roadmap Phase 5 (extended pipeline + trust levels)
    │
    ▼ Pattern #2 (scenario evaluation)
    │  ← Gates become trustworthy: external holdout, not LLM opinion
    │
    ▼ Autonomous multi-task execution
       trust_level: autonomous, reliable gates, retry convergence
```

---

## What NOT to steal

**DOT syntax for workflow definition.** YAML is more ergonomic for agentflow's linear-with-gates topology. DOT is powerful for arbitrary graphs but overkill here.

**The Coding Agent Loop spec.** You don't need to build your own agentic loop. Cursor CLI is your backend. When you get Claude Code, it drops in behind the same `ExecutionEngine` protocol. The loop spec is relevant if you need mid-task steering or provider-aligned tool formats — neither is a current requirement.

**Digital Twin Universe.** Relevant for StrongDM because they integrate with Okta, Jira, Slack, etc. Your use case (software development against a codebase) doesn't have the same external dependency surface. Standard test suites and CI pipelines serve this role.

**Semport (semantic porting).** Interesting technique but not relevant to agentflow's architecture. File it for future reference if you ever need cross-language migration.

**$1,000/day/engineer token spend.** Aspirational metric, not actionable guidance. Your token spend scales with how many tasks you run autonomously. Focus on making each run reliable before scaling volume.
