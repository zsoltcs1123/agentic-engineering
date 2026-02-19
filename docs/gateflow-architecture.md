# Gateflow

A domain-agnostic, code-based orchestrator using LangGraph. Replaces the markdown-driven dev-cycle skill with a portable engine that works across any domain — software development, financial analysis, research, compliance, etc.

## Motivation

The current system encodes orchestration, state management, and structural logic as markdown interpreted by an LLM at runtime. This works but has hard limits:

- No observability — no timing, no token tracking, no structured traces
- No enforced output schemas — LLM can skip reasoning, return malformed output
- Deterministic logic (path resolution, ID generation, git ops) expressed as natural language — unreliable
- No real parallelism — single conversation, sequential execution
- Human-in-the-loop is binary (run or don't) — no per-step, per-task control
- Resume is a re-run from persisted state, not a true checkpoint restore

## Core Insight: Domain-Agnostic Orchestration

The graph topology is the same across domains — it's a universal quality-gated workflow:

```
Define → Plan → Execute → Review → Verify → Document → Finalize
```

What changes per domain is **not the orchestrator** but three things plugged into it:

| Layer            | What it controls                       | How it varies by domain                                                             |
| ---------------- | -------------------------------------- | ----------------------------------------------------------------------------------- |
| **Prompts**      | What the LLM does at each step         | Software: "write code"; Finance: "analyze earnings report"                          |
| **Tools**        | What capabilities each node can invoke | Software: file edit, git, lint; Finance: API fetch, DB write, spreadsheet           |
| **State schema** | What data flows between nodes          | Software: plan, diff, PR URL; Finance: raw report, extracted numbers, enriched data |

The orchestrator only knows: run nodes, check gates, manage state, handle interrupts, log traces. It never touches domain logic.

### Domain examples

**Software development:**

```
Define task → Plan (analyze codebase) → Implement (edit code) →
Review (check diff) → Verify (test acceptance criteria) →
Document (update docs) → Finalize (commit, push, PR)
```

**Financial analysis:**

```
Define task → Plan (identify data sources, analysis approach) →
Execute (fetch report → transform → LLM extract → run models →
cross-reference → enrich → store) →
Review (check methodology, validate numbers) →
Verify (reconcile against source, sanity checks) →
Document (write analysis summary) → Finalize (distribute report)
```

**Research / due diligence:**

```
Define task → Plan (scope sources, define criteria) →
Execute (gather sources → extract claims → cross-reference →
synthesize) → Review (check citations, bias) →
Verify (fact-check key claims) → Document (write brief) →
Finalize (publish, notify stakeholders)
```

Same graph. Same gates. Same observability. Same interrupt model. Different prompts, tools, and state.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Orchestrator (generic)                     │
│                   (LangGraph StateGraph)                     │
│                                                              │
│   Define → Plan → Execute → Review → Verify → Doc → Final   │
│                                                              │
│   - Checkpointed state per thread                            │
│   - Configurable interrupt points                            │
│   - Parallel execution via asyncio                           │
│   - Structured traces + forced reasoning                     │
└──────────────────────────┬───────────────────────────────────┘
                           │
               ┌───────────▼───────────┐
               │   Execution Engine    │
               │     (pluggable)       │
               ├───────────────────────┤
               │ Claude Agent SDK      │  ← library, in-process
               │ Cursor CLI            │  ← subprocess, local
               │ Cursor Cloud API      │  ← REST API, remote
               │ Raw LLM call          │  ← for non-agent steps
               └───────────┬───────────┘
                           │
          ┌────────────────▼────────────────┐
          │          Domain Pack             │
          │  prompts / rules / tools / config│
          └─────────────────────────────────┘
```

## Execution Engines

The orchestrator doesn't call LLMs directly. Each graph node delegates to an **execution engine** — a pluggable backend that handles the actual work (file editing, shell commands, API calls, etc.). The domain pack declares which engine each step uses.

### Engine comparison

|                         | Claude Agent SDK                   | Cursor CLI                        | Cursor Cloud API                  |
| ----------------------- | ---------------------------------- | --------------------------------- | --------------------------------- |
| **Integration**         | Python library, in-process         | Subprocess (`agent chat`)         | REST API, remote                  |
| **Runs where**          | Your machine/server                | Your machine                      | Cursor's cloud                    |
| **File editing**        | Edit tool (targeted replace)       | Cursor's edit engine              | Cursor's edit engine              |
| **Per-tool-call hooks** | Yes — `PreToolUse`/`PostToolUse`   | No                                | No                                |
| **Tool restrictions**   | `allowed_tools` per call           | `cli-config.json` permissions     | Prompt-level only                 |
| **Structured output**   | Streaming messages, parseable      | `--output-format json`            | Webhook payload on completion     |
| **Working dir control** | `cwd` parameter                    | Run from worktree dir             | Branch-based                      |
| **Session/resume**      | SDK sessions                       | `--resume chatId`                 | Agent ID polling                  |
| **Observability**       | Hooks log every tool call          | JSON output parseable             | Status + summary only             |
| **Parallel**            | Async calls in-process             | Multiple subprocesses             | Multiple cloud agents             |
| **Model lock-in**       | Anthropic (+ Azure/Bedrock/Vertex) | Any model via Cursor subscription | Any model via Cursor subscription |
| **Cost model**          | API token usage                    | Cursor subscription               | Cursor subscription               |
| **Maturity**            | GA                                 | Beta                              | Beta                              |

### When to use which

| Scenario                                                 | Best engine                                                |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| Software dev, need max control + observability           | Claude Agent SDK                                           |
| Software dev, want Cursor's models + edit quality, local | Cursor CLI                                                 |
| Software dev, no local compute, fire-and-forget          | Cursor Cloud API                                           |
| Non-coding domain (finance, research, etc.)              | Claude Agent SDK or raw LLM calls                          |
| Mixed: planning/review steps + implement step            | Raw LLM for plan/review, Agent SDK or Cursor for implement |

### Engine interface

The orchestrator talks to engines through a common interface. Each engine implements it:

```python
class ExecutionEngine(Protocol):
    async def run(
        self,
        prompt: str,
        working_directory: str,
        allowed_tools: list[str] | None = None,
        permission_mode: str = "default",
    ) -> EngineResult: ...

@dataclass
class EngineResult:
    output: str
    tool_calls: list[dict]    # what the agent did (if available)
    token_usage: dict | None
    duration_s: float
```

### Claude Agent SDK engine

In-process, richest control. Hooks give you observability inside the agent's execution.

```python
class ClaudeAgentEngine(ExecutionEngine):
    async def run(self, prompt, working_directory, allowed_tools=None, permission_mode="default"):
        result = await query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=allowed_tools or ["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
                permission_mode=permission_mode,
                cwd=working_directory,
            ),
            hooks={
                "pre_tool_use": self.log_tool_call,
            }
        )
        return EngineResult(output=result.text, tool_calls=result.tool_calls, ...)
```

### Cursor CLI engine

Subprocess-based. Structured JSON output. Tool restrictions via project-level `cli-config.json`.

```python
class CursorCLIEngine(ExecutionEngine):
    async def run(self, prompt, working_directory, allowed_tools=None, permission_mode="default"):
        args = [
            "agent", "chat", prompt,
            "--print",
            "--output-format", "json",
        ]
        if permission_mode == "acceptEdits":
            args.append("--force")

        proc = await asyncio.create_subprocess_exec(
            "cursor", *args,
            cwd=working_directory,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        result = json.loads(stdout)
        return EngineResult(output=result["text"], tool_calls=[], ...)
```

### Cursor Cloud API engine

Remote, fire-and-forget with webhook callback. Least control, no local compute needed.

```python
class CursorCloudEngine(ExecutionEngine):
    async def run(self, prompt, working_directory, allowed_tools=None, permission_mode="default"):
        agent = await self.client.create_agent(
            repo=self.repo_url,
            branch=self.branch_from_workdir(working_directory),
            prompt=prompt,
            webhook_url=self.webhook_url,
        )
        result = await self.poll_until_complete(agent["id"])
        return EngineResult(output=result["summary"], tool_calls=[], ...)
```

### Engine selection in domain.json

```json
{
  "name": "software-dev",
  "engine": {
    "default": "claude-agent-sdk",
    "overrides": {
      "plan": "raw-llm",
      "review": "raw-llm",
      "execute": "cursor-cli"
    }
  }
}
```

Per-step engine selection: use a lightweight LLM call for planning and review (no file editing needed), use Cursor for implementation (best edit quality), or mix however makes sense for the domain.

### Distribution model

The orchestrator is a **standalone package** — it ships no domain packs. Each project imports it as a dependency and points it at its own domain pack.

```
# The orchestrator (published package, e.g. PyPI or private registry)
gateflow/
├── pyproject.toml
├── gateflow/
│   ├── __init__.py
│   ├── graph.py            # StateGraph builder
│   ├── domain.py           # DomainPack loader
│   ├── state.py            # base WorkflowState
│   ├── observability.py    # tracing, forced reasoning
│   ├── interrupts.py       # trust levels, human-in-the-loop
│   ├── resources.py        # concurrency limiter, budget guard
│   └── engines/
│       ├── __init__.py     # ExecutionEngine protocol
│       ├── claude_agent.py # Claude Agent SDK engine
│       ├── cursor_cli.py   # Cursor CLI subprocess engine
│       ├── cursor_cloud.py # Cursor Cloud API engine
│       └── raw_llm.py      # Direct LLM call (no agent tools)
```

```
# A consumer project that uses the orchestrator
my-finance-project/
├── pyproject.toml           # depends on gateflow
├── src/
│   └── ...                  # project code
├── workflow/                # the domain pack — lives IN this project
│   ├── domain.json
│   ├── prompts/
│   │   ├── plan.md
│   │   ├── execute.md
│   │   ├── review.md
│   │   └── verify.md
│   ├── rules/
│   │   ├── data-quality.md
│   │   └── compliance.md
│   └── tools/
│       ├── report_fetcher.py
│       ├── number_extractor.py
│       ├── database.py
│       └── enrichment.py
├── run.py
```

```python
# run.py
from gateflow import DomainPack, build_graph

domain = DomainPack.load("./workflow")
app = build_graph(domain)
result = await app.ainvoke(task, thread)
```

This means:

- The orchestrator repo has **zero domain knowledge** — it's pure infrastructure
- Domain packs live next to the code they serve — version-controlled with the project
- Different projects can use different orchestrator versions independently
- Domain packs can be shared across projects too (publish as a package if useful)

### Domain pack structure

```
workflow/
├── domain.json          # state schema, storage config, tool bindings
├── prompts/             # LLM instructions per step
│   ├── plan.md
│   ├── execute.md
│   ├── review.md
│   └── verify.md
├── rules/               # domain-specific prompt fragments
│   ├── data-quality.md
│   └── compliance.md
└── tools/               # callable tools available to nodes
    ├── report_fetcher.py
    └── database.py
```

### domain.json

```json
{
  "name": "financial-analysis",
  "state_fields": {
    "raw_report": "str",
    "extracted_data": "dict",
    "enriched_data": "dict",
    "analysis": "str",
    "destination_db": "str"
  },
  "node_tool_bindings": {
    "execute": ["report_fetcher", "number_extractor", "database", "enrichment"],
    "review": ["database"],
    "verify": ["database", "report_fetcher"]
  },
  "finalize_action": "distribute_report",
  "skillRules": {
    "plan": ["data-quality"],
    "execute": ["data-quality", "compliance"],
    "review": ["compliance"]
  }
}
```

The orchestrator reads this and wires up the graph — it never needs to know what an earnings report is.

## Component Mapping

### What moves from markdown to code

| Current (markdown)          | LangGraph equivalent                         |
| --------------------------- | -------------------------------------------- |
| dev-cycle SKILL.md          | `StateGraph` definition + edge config        |
| State table (PENDING → ...) | `DevCycleState` TypedDict + checkpointer     |
| Resume logic                | Built-in checkpoint resume                   |
| Gate failure → stop         | Conditional edges                            |
| Subagent delegation         | Node functions calling LLM                   |
| `tasks.json` state tracking | LangGraph checkpoint store (SQLite/Postgres) |
| Artifact file I/O           | Python code in node functions                |

### What stays as text (prompts)

| Current                  | LangGraph equivalent                                        |
| ------------------------ | ----------------------------------------------------------- |
| Workflow skill SKILL.md  | Prompt templates loaded into node LLM calls                 |
| Rules (LLM instructions) | Prompt fragments appended to node prompts via `config.json` |

### What becomes pure code (no LLM)

| Current                        | LangGraph equivalent                         |
| ------------------------------ | -------------------------------------------- |
| `task-organization.md`         | `TaskOrganization` config + helpers          |
| commit skill (git operations)  | `subprocess` calls, optional LLM for message |
| push-pr skill (gh CLI)         | `subprocess` calls, optional LLM for PR body |
| ID generation, path resolution | Deterministic Python functions               |

## State Definition

Base state is generic. Domain-specific fields are merged in from `domain.json`.

```python
class WorkflowState(TypedDict):
    task_id: str
    task_description: str
    working_directory: str
    state: str
    plan: str
    review_result: str
    verification_result: str
    trust_level: str
    trace: list[dict]
    domain_data: dict       # domain-specific fields live here
```

## Declarative Workflow Definition

The graph is not hardcoded. Steps, tool restrictions, gate flags, and engine overrides are declared in `domain.json`. The orchestrator builds the graph from this at runtime. Users add/remove/reorder steps without touching Python.

```json
{
  "steps": [
    {
      "name": "plan",
      "prompt": "plan",
      "tools": ["Read", "Glob", "Grep", "WebSearch"],
      "gate": false,
      "readonly": true
    },
    {
      "name": "execute",
      "prompt": "execute",
      "tools": ["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
      "gate": false,
      "readonly": false
    },
    {
      "name": "review",
      "prompt": "review",
      "tools": ["Read", "Glob", "Grep"],
      "gate": true,
      "readonly": true
    },
    {
      "name": "verify",
      "prompt": "verify",
      "tools": ["Read", "Glob", "Grep"],
      "gate": true,
      "readonly": true
    },
    {
      "name": "document",
      "prompt": "document",
      "tools": ["Read", "Edit", "Glob"],
      "gate": false,
      "readonly": false
    },
    {
      "name": "finalize",
      "prompt": "finalize",
      "tools": ["Bash"],
      "gate": false,
      "readonly": false
    }
  ]
}
```

## Graph Definition

The orchestrator reads the step list and builds the graph dynamically:

```python
def build_graph(domain: DomainPack) -> CompiledGraph:
    graph = StateGraph(WorkflowState)
    steps = domain.config["steps"]

    for step in steps:
        graph.add_node(step["name"], make_node(step, domain))

    for i, step in enumerate(steps[:-1]):
        next_step = steps[i + 1]["name"]
        if step.get("gate"):
            graph.add_conditional_edges(
                step["name"], gate_check,
                {"pass": next_step, "issues": END}
            )
        else:
            graph.add_edge(step["name"], next_step)

    graph.add_edge(steps[-1]["name"], END)
    graph.set_entry_point(steps[0]["name"])

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=get_interrupt_points(domain.config)
    )

def make_node(step: dict, domain: DomainPack):
    prompt = domain.build_prompt(step["prompt"])
    engine = domain.get_engine(step["name"])

    async def node(state: WorkflowState) -> WorkflowState:
        result = await engine.run(
            prompt=inject_state(prompt, state),
            working_directory=state["working_directory"],
            allowed_tools=step.get("tools"),
            permission_mode="readonly" if step.get("readonly") else "acceptEdits",
        )
        return update_state(state, step["name"], result)

    return node
```

## Prompt Assembly

Each domain pack has its own prompts and rules. The `DomainPack` class handles assembly.

```python
class DomainPack:
    def __init__(self, path: Path, config: dict):
        self.path = path
        self.config = config

    def build_prompt(self, step: str) -> str:
        base = (self.path / f"prompts/{step}.md").read_text()
        rules = self.config.get("skillRules", {}).get(step, [])
        rule_texts = [
            (self.path / f"rules/{r}.md").read_text()
            for r in rules
            if (self.path / f"rules/{r}.md").exists()
        ]
        return base + "\n\n" + "\n\n".join(rule_texts)

    def get_tools(self, step: str) -> list:
        bindings = self.config.get("node_tool_bindings", {}).get(step, [])
        return [load_tool(self.path / f"tools/{t}.py") for t in bindings]
```

Rule classification (same as before, but per domain):

- **LLM instructions** (coding-standards, data-quality, compliance, etc.) → prompt fragments
- **Structural logic** (task-organization, storage config, etc.) → Python config in `domain.json`

## Observability

### Step-level logging

Every node transition captures timing, token usage, and state changes.

### Forced reasoning (meta-cognition)

LLM output is structured with mandatory fields:

```python
class NodeOutput(BaseModel):
    reasoning: str           # why this approach
    assumptions: list[str]   # what was assumed
    confidence: float        # 0-1 self-assessment
    blind_spots: list[str]   # what couldn't be verified
    output: str              # the actual work product
```

### Gate decisions with evidence

```python
class GateDecision(BaseModel):
    verdict: Literal["PASS", "ISSUES"]
    reasoning: str
    evidence: list[str]
    blind_spots: list[str]
    issues: list[Issue]
```

### Trace artifact per run

Each workflow execution produces a structured JSON trace: task ID, domain, timestamps, per-step duration, token usage, cost, reasoning, gate decisions. Traces are domain-agnostic — same schema regardless of whether it's a code commit or an earnings report.

## Human-in-the-Loop

### Trust levels

| Level        | Interrupts at                                    |
| ------------ | ------------------------------------------------ |
| `autonomous` | None                                             |
| `gates_only` | review, verify                                   |
| `review_all` | plan, implement, review, verify                  |
| `cautious`   | plan, implement, review, verify, commit, push_pr |

Configurable globally, per-task override via task config, and per-node override via `interrupt_overrides`.

### At interrupt points

- **Approve**: resume execution
- **Modify**: update state (edit plan, override gate decision, etc.) then resume
- **Reject**: halt, human reworks manually

State is fully checkpointed — resume picks up exactly where it stopped, no redundant work.

## Parallel Execution

### Workspace isolation (domain-dependent)

Each domain defines how parallel tasks are isolated:

| Domain             | Isolation strategy                | Conflict model                           |
| ------------------ | --------------------------------- | ---------------------------------------- |
| Software dev       | Git worktrees (one branch/task)   | Merge conflicts at PR time               |
| Financial analysis | Temp directories or DB partitions | No conflict — each report is independent |
| Research           | Separate output directories       | Citation overlap flagged at review       |

Software example (worktrees):

```
repo/
repo-worktrees/
├── p01-task-003/    # branch p01-task-003
├── p01-task-004/    # branch p01-task-004
└── p01-task-005/    # branch p01-task-005
```

### Concurrent runs

```python
async def run_batch(tasks: list[dict], domain: DomainPack) -> list[dict]:
    return await asyncio.gather(
        *[run_task(t, domain) for t in tasks],
        return_exceptions=True
    )
```

Each task: own workspace, own LangGraph thread, own checkpoint. No shared mutable state.

### Resource management

- **LLM concurrency**: semaphore limiting parallel API calls
- **Token budget**: per-task and global cost limits with circuit breaker
- **Conflict detection**: domain-specific (file overlap for software, data source contention for analytics)

## UI Options

| Option             | Effort | Best for                                 |
| ------------------ | ------ | ---------------------------------------- |
| LangGraph Studio   | Zero   | Development, debugging, state inspection |
| Terminal (textual) | Low    | Single developer, no infra               |
| Streamlit/Gradio   | Low    | Prototype dashboard + approval UI        |
| Custom web UI      | Medium | Tailored task board, traces, approvals   |

Data is already structured (checkpoint store, traces, reasoning) — UI is a view layer.

## CLI

The orchestrator ships with a CLI for running workflows from the terminal:

```bash
gateflow run task-001                     # full workflow from current state
gateflow run task-001 --from review       # resume from a specific step
gateflow run task-001 --step plan         # run a single step only
gateflow status task-001                  # current state + latest trace summary
gateflow list                             # all tasks with states
gateflow trace task-001                   # full trace for latest run
gateflow trace task-001 --step execute    # trace for a specific step
```

The CLI loads the domain pack from the current directory (or `--domain ./path`), resolves the task, and invokes the graph.

## Open Design Questions

### Gate failure retry loops

Currently gates stop the workflow on ISSUES. An alternative: automatically send the issues back to the execute step and re-run. LangGraph conditional edges support this (edge from review back to execute), but automatic retry risks infinite loops.

Possible design: configurable `max_retries` per gate in the step definition. On failure, the orchestrator re-invokes execute with the issues appended to the prompt. After `max_retries`, stop.

```json
{
  "name": "review",
  "prompt": "review",
  "gate": true,
  "max_retries": 2,
  "retry_target": "execute"
}
```

This stays as an open question — manual fix and re-run might be safer until there's confidence in the retry quality.

### Context between steps

Each step receives a prompt and has tool access. Two strategies for providing codebase context:

1. **Tool-driven exploration**: the agent uses Read, Glob, Grep to find what it needs. More tokens (tool calls), but the agent sees exactly what's relevant. Works well with Claude Agent SDK and Cursor CLI since they have built-in exploration.

2. **Pre-injected context**: the orchestrator reads key files and injects them into the prompt before calling the engine. Fewer tool calls, but risks injecting irrelevant context or missing important files.

Likely answer: tool-driven exploration for execute steps (the agent needs to understand before editing), pre-injected for review/verify steps (inject the diff and plan so the reviewer has everything upfront without spending tokens on exploration).

This could be configurable per step in the step definition:

```json
{ "name": "review", "context_strategy": "inject", "inject": ["diff", "plan"] }
{ "name": "execute", "context_strategy": "explore" }
```

## Migration Path

### Phase 1: Orchestrator package (standalone repo)

1. Create `gateflow` package repo
2. Define `ExecutionEngine` protocol and implement `raw_llm` engine (simplest, no external deps)
3. Build `StateGraph` with generic node names (plan, execute, review, verify, document, finalize)
4. Implement `DomainPack` loader — reads prompts, rules, config from any directory path
5. Implement `make_node` — assembles prompt, resolves engine per step, delegates to engine
6. Add checkpointer (SQLite for local dev, Postgres adapter for shared/production)
7. Publish as installable package (PyPI or private registry)

### Phase 2: First execution engine (Claude Agent SDK)

8. Implement `claude_agent` engine — wraps the SDK, maps `allowed_tools` + `permission_mode`
9. Add hook-based observability (log every tool call via `PreToolUse`)
10. Add file checkpointing support (`rewind_files()` on step failure)
11. Validate: run a non-coding task end-to-end using raw LLM + Claude Agent SDK

### Phase 3: First domain pack (software-dev, in this repo)

12. Add `gateflow` as a dependency in this project
13. Create `workflow/` directory with `domain.json`, prompts, rules
14. Extract prompts from current SKILL.md files — strip orchestration, keep LLM instructions
15. Port rules: LLM instructions → `workflow/rules/`; structural logic → `domain.json`
16. Configure engine per step in `domain.json` (raw LLM for plan/review, Claude Agent SDK for implement)
17. Validate: run a task end-to-end, compare output quality with current markdown system

### Phase 4: Additional engines

18. Implement `cursor_cli` engine — subprocess wrapper, JSON output parsing, `--force` for writes
19. Implement `cursor_cloud` engine — REST client, webhook handling, polling
20. Allow domain packs to swap engines without changing prompts or rules

### Phase 5: Observability + control

21. Add structured logging and forced reasoning schemas (orchestrator level)
22. Add trust levels and interrupt config
23. Add trace output per run (engine-level detail where available, e.g., Claude hooks)
24. Publish new version

### Phase 6: Parallel + scale

25. Add workspace isolation hooks (domain pack declares its isolation strategy)
26. Add asyncio batch execution with resource limits
27. Add UI — start with LangGraph Studio, extend as needed

### Phase 7: Second domain pack (validates portability)

28. In a separate project, add `gateflow` as a dependency
29. Create domain pack for that domain (e.g., financial-analysis)
30. Write prompts, rules — use raw LLM or Claude Agent SDK as engine
31. Zero orchestrator changes required. If changes needed → fix abstraction leak → republish
