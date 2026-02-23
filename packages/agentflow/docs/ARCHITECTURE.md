# Agentflow — Architecture

## System Overview

Agentflow is a configurable workflow orchestrator built on LangGraph. It reads a declarative workflow definition, builds a state graph with quality gates, and executes each step by delegating to a pluggable execution engine. The orchestrator knows nothing about what the steps do — it only manages sequencing, gating, state, interrupts, and tracing.

```
                    ┌─────────────────────────────────┐
                    │         Workflow Definition       │
                    │  (steps, gates, rules, engines)   │
                    └───────────────┬─────────────────┘
                                    │ loads
                    ┌───────────────▼─────────────────┐
                    │          Orchestrator             │
                    │     (LangGraph StateGraph)        │
                    │                                   │
                    │  Step1 → Step2 → Gate → Step3 ... │
                    │                                   │
                    │  - Checkpointed state per thread   │
                    │  - Configurable interrupt points   │
                    │  - Structured traces               │
                    └───────────────┬─────────────────┘
                                    │ delegates
                    ┌───────────────▼─────────────────┐
                    │       Execution Engine            │
                    │        (pluggable)                │
                    ├──────────────────────────────────┤
                    │  Cursor CLI    (subprocess)       │
                    │  Claude Code   (subprocess)       │
                    │  Claude SDK    (library, future)  │
                    └───────────────┬─────────────────┘
                                    │ informed by
                    ┌───────────────▼─────────────────┐
                    │     Prompts + Rules               │
                    │  (consumer-provided, per-step)    │
                    └──────────────────────────────────┘
```

**Core principle**: The orchestrator is infrastructure. Domain knowledge (what "review" means, what coding standards apply) lives entirely in prompts, rules, and workflow definitions provided by the consumer project.

---

## Technology Stack

| Layer | Technology | Rationale |
| --- | --- | --- |
| Orchestration | LangGraph `StateGraph` | Graph-based workflow with checkpointing, interrupts, conditional edges. Studio compatibility for visual debugging. |
| Checkpointing | `langgraph-checkpoint-sqlite` | Local-first persistence. No external database for solo/small-team use. |
| CLI framework | `argparse` | Already in use. No need for heavier frameworks at this scale. |
| Terminal UI | `rich` | Already in use. Formatted output, tables, progress display. |
| Workflow definition | YAML (`PyYAML`) | More readable than JSON for humans. Comments supported. Gateflow used JSON — switching to YAML for ergonomics. |
| Type validation | `dataclasses` + manual validation | Avoids Pydantic dependency. Gateflow used Pydantic — proved heavier than needed for config parsing. |
| Engine subprocess | `asyncio.create_subprocess_exec` | Already in use for Cursor CLI. Same pattern for Claude Code. |
| Python | 3.14+ | Workspace constraint. |
| Build | `hatchling` | Already in use. |

---

## Components & Responsibilities

### 1. Workflow Definition (`workflow/definition.py`)

Loads and validates the workflow YAML file. Data model:

```python
@dataclass
class StepDefinition:
    name: str
    prompt: str
    gate: bool = False
    interrupt: bool = False
    readonly: bool = True
    engine: str | None = None     # override default engine for this step
    rules: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)  # prior step names whose outputs to inject

@dataclass
class WorkflowDefinition:
    steps: list[StepDefinition]
    default_engine: str = "cursor-cli"
    trust_level: str = "cautious"  # autonomous | gates_only | cautious
    rules_dir: str | None = None
    prompts_dir: str | None = None
```

Example `workflow.yaml`:

```yaml
default_engine: cursor-cli
trust_level: gates_only
prompts_dir: ./prompts
rules_dir: ./rules

steps:
  - name: plan
    prompt: plan
    rules: [python, python-testing]

  - name: implement
    prompt: implement
    readonly: false
    inputs: [plan]
    rules: [python, python-testing]

  - name: review
    prompt: review
    gate: true
    inputs: [plan]
    rules: [python, python-testing]

  - name: verify
    prompt: verify
    gate: true
    inputs: [plan]
    rules: [python-testing]

  - name: document
    prompt: document
    readonly: false
    inputs: [plan, review, verify]

  - name: commit
    prompt: commit
    readonly: false
```

**Responsibility boundary**: The definition module only parses and validates. It does not build graphs or run engines.

### 2. Graph Builder (`workflow/graph.py`)

Reads a `WorkflowDefinition` and constructs the LangGraph `StateGraph`. This is where the current hardcoded 3-step graph becomes dynamic.

Responsibilities:
- Create a node for each step in the definition.
- Wire edges: gate steps get conditional edges (PASS → next, BLOCK → END); non-gate steps get direct edges.
- Compute interrupt points from trust level and per-step `interrupt` flags.
- Compile with checkpointer.

Gate routing:

```python
def gate_router(state: WorkflowState) -> Literal["pass", "block"]:
    if state.get("gate_verdict") == "BLOCK":
        return "block"
    return "pass"
```

For each gate step, `add_conditional_edges` routes to the next step on PASS, or END on BLOCK.

### 3. Node Factory (`workflow/nodes.py`)

Creates the async node function for each step. Each node:

1. Assembles the prompt (base prompt + rules + state context).
2. Resolves the engine (step override or default).
3. Calls `engine.run()`.
4. If the step is a gate, parses the output into a `GateDecision`.
5. Returns the state update (output, trace entry, gate verdict if applicable).

This is where prompt assembly, context injection, and gate parsing live — separated from graph topology (graph.py) and engine execution (engines/).

### 4. Prompt Assembly (`workflow/prompts.py`)

Loads prompt files and rules, assembles the final prompt for a step.

```
final_prompt = base_prompt + input_context + rule_fragments
```

- **Base prompt**: Loaded from `prompts_dir/{step.prompt}.md`.
- **Input context**: Built from the step's `inputs` declaration. For each declared input, the assembler pulls the corresponding value from `step_outputs[input_name]` and appends it as a labeled section (e.g., `## Plan Output\n{step_outputs["plan"]}`). The task description and workdir are always included regardless of `inputs`.
- **Rule fragments**: Loaded from `rules_dir/{rule}.md` for each rule in the step's `rules` list.

If `inputs` is empty, only the task description is injected (the step's prompt file is responsible for its own context, e.g., via tool-driven exploration). This keeps backward compatibility with steps that don't need prior outputs.

**Validation**: At graph build time, the definition loader validates that every name in a step's `inputs` list refers to a step that appears earlier in the pipeline. This catches configuration errors before execution.

### 5. State (`workflow/state.py`)

The workflow state TypedDict, extended from current:

```python
class WorkflowState(TypedDict):
    task: str
    workdir: str
    plan: str
    review: str
    gate_verdict: str           # "PASS" | "BLOCK" | "" — reset per gate step
    step_outputs: dict[str, str]  # all step outputs keyed by step name
    trace: Annotated[list[TraceEntry], operator.add]
```

`step_outputs` is the accumulator — every node writes its output here keyed by step name. The prompt assembler reads from it when resolving a step's `inputs` list. Individual fields like `plan` and `review` are kept for backward compatibility and direct access in prompts.

### 6. Gate Decision (`workflow/gates.py`)

Structured gate output:

```python
@dataclass
class GateDecision:
    verdict: Literal["PASS", "BLOCK"]
    reasoning: str
    issues: list[str] = field(default_factory=list)
```

Parsing: attempt JSON parse of engine output. On failure, default to BLOCK with a parse-error message. This is conservative — ambiguous output blocks rather than passes.

### 7. Execution Engine Protocol (`engine/protocol.py`)

```python
class ExecutionEngine(Protocol):
    async def run(
        self,
        prompt: str,
        *,
        working_directory: str,
        mode: PermissionMode = "readonly",
    ) -> EngineResult: ...
```

The existing `CursorCLI` class already satisfies this protocol. Future engines (Claude Code, Claude SDK) implement the same interface.

### 8. Engine: Cursor CLI (`engine/cursor_cli.py`)

Existing implementation. No changes needed to the engine itself — only the graph builder and node factory change to support the new architecture.

### 9. CLI (`cli.py`)

Extended to accept workflow definition path:

```
agentflow run <task> [--workflow workflow.yaml] [--workdir .] [--model M]
```

If `--workflow` is not provided, uses a built-in default pipeline (plan → implement → review) for backward compatibility.

### 10. Display (`workflow/display.py`)

Existing Rich-based terminal UI. Extended to display gate decisions (verdict, reasoning, issues) and step-level trace summaries.

---

## Data Architecture

### Data Flow

```
                    ┌─────────┐
                    │  Task   │
                    │ (input) │
                    └────┬────┘
                         │
              ┌──────────▼──────────┐
              │    WorkflowState     │
              │                      │
              │  task, workdir       │
              │  plan, review        │
              │  gate_verdict        │
              │  step_outputs{}      │
              │  trace[]             │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
     │  Step   │   │  Gate   │   │  Step   │  ...
     │  Node   │   │  Node   │   │  Node   │
     └────┬────┘   └────┬────┘   └────┬────┘
          │              │              │
          │   ┌──────────▼──────────┐   │
          │   │   GateDecision      │   │
          │   │   verdict/reasoning │   │
          │   └─────────────────────┘   │
          │                             │
          └──────────────┬──────────────┘
                         │
              ┌──────────▼──────────┐
              │   Checkpoint DB     │
              │  (SQLite, per-run)  │
              └──────────▼──────────┘
                         │
              ┌──────────▼──────────┐
              │   Trace (in state)  │
              │  per-step entries   │
              └─────────────────────┘
```

### Where Data Lives

| Data | Location | Format |
| --- | --- | --- |
| Workflow definition | Consumer project (e.g., `workflow.yaml`) | YAML |
| Prompts | Consumer project (e.g., `prompts/plan.md`) | Markdown |
| Rules | Consumer project (e.g., `rules/python.md`) | Markdown |
| Checkpoint state | `{workdir}/.agentflow/checkpoints.db` | SQLite (LangGraph managed) |
| Trace | In `WorkflowState.trace` (persisted via checkpoint) | List of `TraceEntry` dataclasses |
| Gate decisions | In `WorkflowState.gate_verdict` + step output | String verdict + structured decision in output |

---

## Observability

| Signal | Source | Access |
| --- | --- | --- |
| Step timing | `TraceEntry.duration_s` | Trace in state, printed in CLI summary |
| Step output | `step_outputs[name]` | State, CLI display |
| Gate decisions | `GateDecision` parsed per gate step | State, CLI display, Studio |
| Tool calls | `TraceEntry.tool_call_count` + `EngineResult.tool_calls` | Trace in state |
| Full graph state | LangGraph checkpoint | LangGraph Studio (visual inspection) |
| Step transitions | LangGraph graph structure | LangGraph Studio (graph view) |

LangGraph Studio serves as the development/debugging UI. The CLI + Rich display is the production interface. No custom web UI in v1.

---

## Key Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
| --- | --- | --- |
| YAML over JSON for workflow definition | More readable, supports comments, better for human editing | Extra dependency (`PyYAML`). Gateflow's JSON was harder to maintain. |
| Dataclasses over Pydantic for config | Fewer dependencies, simpler. Gateflow's Pydantic models were overkill. | Less automatic validation. Manual validation required. |
| Gate failure halts (no retry loop) | Simpler. Retry loops risk infinite cycles. Manual fix and resume is safer until gate quality is proven. | Requires human intervention on every gate failure. |
| Engine protocol as Python Protocol | Duck-typed, no base class inheritance. Easy to add engines. | No runtime enforcement — violations surface as runtime errors, not import-time. |
| Prompts and rules live in consumer project | Agentflow stays domain-free. Consumer controls quality standards. | Consumer must create and maintain prompt/rule files. Could ship optional defaults later. |
| `step_outputs` dict for cross-step context | Simple accumulator. Every step writes here; later steps read via `inputs`. | All outputs in memory. Large outputs could grow state significantly. |
| Declared `inputs` + implicit `step_outputs` | Steps declare dependencies explicitly via `inputs`. Prompt assembler auto-injects them. `step_outputs` remains available for undeclared access in prompt templates. | Two access paths (declared vs implicit). Declared is preferred — it's validated at build time and self-documents the data flow. |
| No Pydantic for GateDecision | Dataclass + manual JSON parse. Avoids dependency. | No automatic schema validation. Parse errors default to BLOCK (conservative). |
| Trust levels computed from step flags + global setting | Flexible per-step override while keeping a simple global default. | Two sources of truth (global trust_level + per-step interrupt flag). Needs clear precedence rules. |

---

## Future Considerations

| Item | Trigger | Approach |
| --- | --- | --- |
| Claude Code engine | Claude Code CLI stabilizes | New engine module implementing `ExecutionEngine` protocol. Subprocess-based like Cursor CLI. |
| Claude SDK engine | Need in-process control, tool hooks | New engine module. Library-based, richer observability via SDK hooks. |
| Gate retry loops | Confidence in gate quality, repeated manual fixes | Add `max_retries` and `retry_target` to `StepDefinition`. Conditional edge loops back to target step. |
| Parallel task execution | Multiple tasks, workspace isolation needed | `asyncio.gather` over tasks, each with own workdir/thread. Git worktree integration. |
| Token/cost tracking | API-based engines (Claude SDK) provide usage data | Extend `EngineResult` with `token_usage`. Aggregate in trace. |
| Default prompt pack | Consumer onboarding friction | Ship optional `agentflow init` that scaffolds a starter workflow.yaml + prompts. |
| Postgres checkpointer | Shared/team use, production deployments | Swap `langgraph-checkpoint-sqlite` for `langgraph-checkpoint-postgres`. |

---

## Version History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-02-23 | Initial version |
| 1.1 | 2026-02-23 | Added step dependency model: `inputs` field on StepDefinition, input context injection in prompt assembly, build-time validation |
