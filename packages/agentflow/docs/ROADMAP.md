# Agentflow — Roadmap

## Overview

Agentflow already has a working 3-step pipeline (plan → implement → review) with Cursor CLI, checkpointing, and a Rich terminal UI. The roadmap builds on this incrementally — each phase produces a working system and adds one capability layer. No phase requires speculative abstractions; every addition is motivated by a concrete gap.

The sequencing prioritizes the workflow engine core (phases 1-3) before adding engines, observability, and scale. This mirrors the dependency graph: you can't test a new engine without a configurable pipeline, and you can't add observability without structured gate decisions to observe.

---

## Phase Summary

| Phase | Name | Key Outcome |
| --- | --- | --- |
| 1 | Workflow Definition | Steps loaded from YAML instead of hardcoded in Python |
| 2 | Gate Model | Gate steps produce structured decisions and block on BLOCK verdict |
| 3 | Prompt & Rules Assembly | Prompts loaded from files, rules injected per step |
| 4 | Engine Protocol | `ExecutionEngine` protocol; Cursor CLI refactored to implement it |
| 5 | Extended Pipeline | Full default pipeline: Plan → Implement → Review → Verify → Document → Commit |
| 6 | Observability & Studio | Structured traces, gate decision display, LangGraph Studio compatibility |
| 7 | Second Engine | Claude Code CLI engine implementing the same protocol |

---

## Phase Details

### Phase 1: Workflow Definition

**Goal**: Replace the hardcoded 3-step graph with a graph built from a YAML workflow definition.

**Deliverables**:
- `StepDefinition` and `WorkflowDefinition` dataclasses in `workflow/definition.py`.
- `StepDefinition` includes `inputs: list[str]` for declaring dependencies on prior step outputs.
- YAML loader with validation (step names unique, at least one step, `inputs` reference only earlier steps, etc.).
- `build_graph()` refactored to accept `WorkflowDefinition` instead of a hardcoded engine.
- `--workflow` CLI flag. Without it, a built-in default definition preserves current behavior.
- Tests for definition loading, validation errors (including invalid input references), and graph construction from definition.

**Done when**: `agentflow run "task" --workflow workflow.yaml` builds and executes a graph matching the YAML, and `agentflow run "task"` (no flag) still works with the default 3-step pipeline.

---

### Phase 2: Gate Model

**Goal**: Gate steps produce structured `GateDecision` output and conditionally block progression.

**Deliverables**:
- `GateDecision` dataclass in `workflow/gates.py` (verdict, reasoning, issues).
- Gate parsing: JSON parse of engine output with conservative fallback (parse failure → BLOCK).
- `gate_router` function for conditional edges.
- `gate_verdict` field added to `WorkflowState`.
- Node factory creates gate-aware nodes for steps where `gate: true`.
- Graph builder wires conditional edges for gate steps.
- Tests for gate parsing (valid PASS, valid BLOCK, malformed output), gate routing, and graph behavior on BLOCK.

**Done when**: A step marked `gate: true` in the workflow definition produces a `GateDecision`, and the graph halts on BLOCK verdict.

---

### Phase 3: Prompt & Rules Assembly

**Goal**: Step prompts are loaded from markdown files. Consumer-provided rules are appended per step.

**Deliverables**:
- `PromptAssembler` in `workflow/prompts.py` — loads base prompt from file, appends rules, injects input context from declared dependencies.
- `prompts_dir` and `rules_dir` in `WorkflowDefinition`.
- Per-step `rules` list in `StepDefinition`.
- `step_outputs: dict[str, str]` added to `WorkflowState` for cross-step context.
- Input context injection: for each name in a step's `inputs`, the assembler pulls the output from `step_outputs` and appends it as a labeled section.
- Node factory uses `PromptAssembler` instead of inline f-strings. Each node writes its output to `step_outputs[step.name]`.
- Tests for prompt loading, rule injection, input context injection, missing file handling, and undeclared input access.

**Done when**: A step with `inputs: [plan]` automatically receives the plan output in its prompt. A consumer project with `prompts/` and `rules/` directories can define step-specific prompts and rules that get assembled into the final prompt sent to the engine.

---

### Phase 4: Engine Protocol

**Goal**: Formalize the execution engine interface. Refactor `CursorCLI` to implement it. Prepare for additional engines.

**Deliverables**:
- `ExecutionEngine` Protocol in `engine/protocol.py`.
- `CursorCLI` confirmed to satisfy the protocol (no changes needed to its API, just verify).
- Engine registry: workflow definition specifies `default_engine` and optional per-step `engine` override.
- `build_graph()` receives an engine registry (dict of name → engine instance).
- Node factory resolves the engine per step.
- Tests for engine resolution (default, override, missing engine).

**Done when**: `CursorCLI` is used via the protocol, and the node factory resolves engines by name from a registry.

---

### Phase 5: Extended Pipeline

**Goal**: Ship the full default pipeline with all step types working end-to-end.

**Deliverables**:
- Default `workflow.yaml` with: Plan → Implement → Review (gate) → Verify (gate) → Document → Commit.
- Default prompt files for each step in an optional bundled prompts directory.
- Trust level logic: `autonomous` (no interrupts), `gates_only` (interrupt after gate steps), `cautious` (interrupt after every step).
- `agentflow init` command that scaffolds a starter `workflow.yaml`, `prompts/`, and `rules/` directory into the consumer project.
- End-to-end test with the full pipeline (mocked engine).

**Done when**: `agentflow init` + `agentflow run "task"` executes a 6-step gated pipeline with configurable interrupt points.

---

### Phase 6: Observability & Studio

**Goal**: Structured traces with gate decision details. LangGraph Studio compatibility verified.

**Deliverables**:
- `TraceEntry` extended with gate decision summary (verdict, issue count) for gate steps.
- CLI summary prints per-step timing, gate verdicts, and issue highlights.
- Rich display for gate decisions (verdict badge, reasoning, issues list).
- Verify LangGraph Studio can load and visualize the compiled graph (state inspection, step transitions, checkpoint replay).
- Document Studio setup instructions.

**Done when**: A completed workflow run produces a structured trace viewable in both CLI output and LangGraph Studio.

---

### Phase 7: Second Engine (Claude Code)

**Goal**: Add Claude Code CLI as a second execution engine, proving the engine protocol works.

**Deliverables**:
- `ClaudeCodeCLI` engine in `engine/claude_code.py` implementing `ExecutionEngine`.
- Output parsing for Claude Code's output format.
- Workflow definition can specify `claude-code` as engine (default or per-step).
- Tests with mocked subprocess.

**Done when**: A workflow can run with `default_engine: claude-code` and produce equivalent results to Cursor CLI. Switching engines is a one-line YAML change.

---

## Milestones & Success Criteria

| Milestone | After Phase | Criteria |
| --- | --- | --- |
| Configurable pipeline | 1 | Steps defined in YAML, not Python |
| Quality gates working | 2 | Gate steps halt on BLOCK verdict with structured decisions |
| Consumer-ready | 3 + 4 | External project can bring its own prompts, rules, and engine config |
| Full pipeline | 5 | 6-step gated workflow runs end-to-end |
| Observable | 6 | Traces in CLI + Studio |
| Multi-engine | 7 | Two engines, swappable via config |

---

## Learning Points

| Phase | What We Learn | Informs |
| --- | --- | --- |
| 1 | Whether YAML + dataclass validation is sufficient or needs more structure | Phase 3 (prompt/rules config in same format) |
| 2 | How reliably LLMs produce structured gate JSON | Phase 5 (how many gate steps to include), future retry loops |
| 3 | Whether declared `inputs` + auto-injection is sufficient or needs a template engine | Future: template engine vs string concat |
| 4 | Whether the Protocol abstraction holds across engine types | Phase 7 (Claude Code), future engines |
| 5 | Whether the full pipeline adds value or creates friction | Which steps become standard, which are optional |
| 6 | What Studio reveals about state/graph design | Potential state schema adjustments |

---

## Future Phases

| Phase | Focus | Trigger |
| --- | --- | --- |
| 8 | Gate retry loops | Gate quality proven reliable enough to auto-retry |
| 9 | Parallel task execution | Need to process multiple tasks concurrently |
| 10 | Claude SDK engine (in-process) | Need richer observability (tool-call hooks, token tracking) |
| 11 | Token/cost tracking | API-based engines provide usage data |
| 12 | Default prompt packs | Consumer onboarding friction is too high |

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-02-23 | Initial version |
| 1.1 | 2026-02-23 | Added step dependency model (`inputs` field) to Phase 1 and Phase 3 deliverables |
