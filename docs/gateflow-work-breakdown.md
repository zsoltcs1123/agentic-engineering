# Work Breakdown: Gateflow

## Summary

Build Gateflow — a domain-agnostic, code-based workflow orchestrator on LangGraph — from placeholder package to working system, then extend with advanced features.

| #   | Task                                           | Phase | Depends On     |
| --- | ---------------------------------------------- | ----- | -------------- |
| 1   | Define WorkflowState and base models           | MVP   | None           |
| 2   | Define ExecutionEngine protocol                | MVP   | 1              |
| 3   | Implement raw LLM engine                       | MVP   | 2              |
| 4   | Implement DomainPack loader                    | MVP   | 2              |
| 5   | Build dynamic graph constructor                | MVP   | 1, 4           |
| 6   | Implement make_node and prompt assembly        | MVP   | 3, 5           |
| 7   | Add SQLite checkpointer                        | MVP   | 5              |
| 8   | Implement Cursor CLI engine                    | MVP   | 2              |
| 9   | Implement Cursor Cloud API engine              | MVP   | 2              |
| 10  | Create software-dev domain pack                | MVP   | 4              |
| 11  | End-to-end integration test                    | MVP   | 6, 7, 8, 9, 10 |
| 12  | Add structured observability and tracing       | v1    | 11             |
| 13  | Add trust levels and interrupt configuration   | v1    | 11             |
| 14  | Add parallel execution and resource management | v1    | 11             |
| 15  | Build CLI                                      | v1    | 11             |
| 16  | Implement gate failure retry loops             | v1    | 11             |
| 17  | Add per-step context strategy                  | v1    | 11             |
| 18  | Implement Claude Agent SDK engine              | v1    | 2              |

## Tasks

### 1. Define WorkflowState and base models

Define the core data structures that flow through the graph: the state TypedDict, structured output models, and the engine result container. These are the foundation everything else imports.

**Steps:**

1. Add `langgraph`, and `pydantic`, as dependencies in `packages/gateflow/pyproject.toml`.
2. Create `packages/gateflow/src/gateflow/state.py` with `WorkflowState` TypedDict (task_id, task_description, working_directory, current_step, status, plan, review_result, verification_result, trace, domain_data)
3. Create `packages/gateflow/src/gateflow/models.py` with `EngineResult` dataclass (output, tool_calls, token_usage, duration_s), `NodeOutput` Pydantic model (reasoning, assumptions, confidence, blind_spots, output), `GateDecision` Pydantic model (verdict, reasoning, evidence, blind_spots, issues)
4. Export public API from `__init__.py`
5. Write unit tests for model validation (GateDecision rejects invalid verdict, NodeOutput confidence range, EngineResult defaults)

**Acceptance criteria:**

- `WorkflowState` is importable and usable as a LangGraph state type
- Pydantic models enforce their constraints (verdict literals, confidence bounds)
- All types are exported from `gateflow` package root

**Depends on:** None

---

### 2. Define ExecutionEngine protocol

Create the protocol class that all execution engines must implement. This is the contract between the orchestrator and any backend.

**Steps:**

1. Create `packages/gateflow/src/gateflow/engines/__init__.py` with the `ExecutionEngine` Protocol class defining `async def run(self, prompt, working_directory, allowed_tools, permission_mode) -> EngineResult`
2. Add a `PermissionMode` string literal type (`readonly`, `acceptEdits`, `default`)
3. Export from package root
4. Write a unit test that verifies a minimal conforming class satisfies the protocol (using `runtime_checkable`)

**Acceptance criteria:**

- `ExecutionEngine` is a `typing.Protocol` with a single `run` method returning `EngineResult`
- A class implementing the method is recognized as conforming at runtime
- mypy passes on a conforming implementation

**Depends on:** 1

---

### 3. Implement raw LLM engine

Build the simplest engine: a direct Anthropic API call with no agent tools. Used for steps that only need LLM reasoning (plan, review, verify).

**Steps:**

1. Create `packages/gateflow/src/gateflow/engines/raw_llm.py` with `RawLLMEngine` class
2. Implement `run()`: construct messages from prompt, call `anthropic.AsyncAnthropic().messages.create()`, parse response into `EngineResult`
3. Accept model name and max_tokens as constructor parameters with sensible defaults
4. Handle API errors (rate limit, auth, timeout) with clear error messages
5. Write unit tests using a mocked Anthropic client

**Acceptance criteria:**

- `RawLLMEngine` conforms to `ExecutionEngine` protocol
- Prompt is sent as a user message, response text lands in `EngineResult.output`
- Token usage from API response is captured in `EngineResult.token_usage`
- API errors raise descriptive exceptions (not raw httpx errors)

**Depends on:** 2

---

### 4. Implement DomainPack loader

Build the `DomainPack` class that reads a domain directory (domain.json, prompts/, rules/) and provides prompt assembly and engine resolution.

**Steps:**

1. Create `packages/gateflow/src/gateflow/domain.py` with `DomainPack` class
2. Implement `DomainPack.load(path)` class method: validate directory structure, parse `domain.json`, verify referenced prompt/rule files exist
3. Implement `build_prompt(step_name)`: load base prompt from `prompts/{step}.md`, append rule texts from `skillRules` config
4. Implement `get_engine(step_name)`: resolve engine from `engine.overrides` falling back to `engine.default`
5. Implement `get_steps()`: return the step list from domain.json config
6. Write unit tests with a fixture domain pack directory on disk

**Acceptance criteria:**

- `DomainPack.load()` raises clear errors for missing `domain.json`, missing prompt files, or invalid config
- `build_prompt()` concatenates base prompt + applicable rules
- `get_engine()` returns override engine for a step if configured, default otherwise
- `get_steps()` returns the ordered step list from config

**Depends on:** 2

---

### 5. Build dynamic graph constructor

Implement `build_graph()` that reads the step list from a DomainPack and constructs a LangGraph StateGraph with nodes, edges, and conditional gate edges.

**Steps:**

1. Create `packages/gateflow/src/gateflow/graph.py`
2. Implement `build_graph(domain, checkpointer, engine_registry)` that iterates `domain.get_steps()`, adds a node per step, wires sequential edges and conditional edges for gate steps
3. Implement `gate_check()` function that inspects state to determine `pass` or `issues` routing
4. Set entry point to first step, terminal edge from last step to END, gate failure edges to END
5. Write unit tests: build a graph from a mock domain pack, verify node count, edge topology, and that gate steps have conditional edges

**Acceptance criteria:**

- `build_graph()` returns a `CompiledGraph` with one node per step in domain config
- Gate steps route to next step on PASS and to END on ISSUES
- Non-gate steps have unconditional edges to the next step
- Graph compiles without errors for a valid domain config

**Depends on:** 1, 4

---

### 6. Implement make_node and prompt assembly

Build the node factory that creates the async function each graph node executes: assemble prompt, inject state, delegate to engine, update state.

**Steps:**

1. Implement `make_node(step, domain, engine_registry)` in `graph.py` that returns an async node function
2. Implement `inject_state(prompt, state)`: template state fields into the prompt (at minimum: task_description, plan, working_directory, and any domain_data)
3. Implement `update_state(state, step_name, result)`: write engine output to appropriate state field (plan for plan step, review_result for review, etc.), append to trace
4. For gate steps, parse `EngineResult.output` into `GateDecision` and write verdict + issues to state
5. Write unit tests: mock engine, verify prompt assembly includes rules, verify state is updated correctly after node execution

**Acceptance criteria:**

- Node function calls the correct engine with assembled prompt and step's tool/permission config
- State is updated with the engine's output under the correct field
- Gate nodes parse output into GateDecision and the verdict is available for `gate_check`
- Trace list accumulates an entry per executed step

**Depends on:** 3, 5

---

### 7. Add SQLite checkpointer

Configure LangGraph's built-in async SQLite checkpointer so workflow state persists across runs and supports resume.

**Steps:**

1. Add `langgraph-checkpoint-sqlite` (or equivalent) as a dependency
2. Create `packages/gateflow/src/gateflow/checkpoint.py` with a factory function `create_checkpointer(db_path)` that returns the async SQLite checkpointer
3. Wire the checkpointer into `build_graph()` via the `checkpointer` parameter
4. Write an integration test: run a graph partway, kill it, resume from checkpoint, verify state continuity

**Acceptance criteria:**

- Workflow state survives process restart — resuming a thread ID continues from the last completed step
- Checkpoint database is created at the specified path
- `build_graph()` accepts and uses the checkpointer

**Depends on:** 5

---

### 8. Implement Cursor CLI engine

Build the subprocess-based engine that invokes `cursor agent chat` with JSON output, mapping allowed_tools and permission_mode to CLI flags.

**Steps:**

1. Create `packages/gateflow/src/gateflow/engines/cursor_cli.py` with `CursorCLIEngine` class
2. Implement `run()`: build argument list (`cursor agent chat <prompt> --print --output-format json`), add `--force` when `permission_mode == "acceptEdits"`, spawn via `asyncio.create_subprocess_exec`, capture stdout/stderr
3. Parse JSON output into `EngineResult` (extract text, handle non-zero exit codes)
4. Accept configurable `cursor_path` for non-standard installations
5. Write unit tests mocking `asyncio.create_subprocess_exec`

**Acceptance criteria:**

- `CursorCLIEngine` conforms to `ExecutionEngine` protocol
- Subprocess is invoked with correct arguments including `--print` and `--output-format json`
- `--force` flag is added only when permission_mode is `acceptEdits`
- Non-zero exit codes and malformed JSON produce descriptive errors

**Depends on:** 2

---

### 9. Implement Cursor Cloud API engine

Build the REST-based engine that creates remote Cursor agents and polls until completion.

**Steps:**

1. Create `packages/gateflow/src/gateflow/engines/cursor_cloud.py` with `CursorCloudEngine` class
2. Implement `run()`: POST to create agent (repo, branch, prompt), poll status endpoint until terminal state, extract result
3. Implement polling with configurable interval and timeout, exponential backoff
4. Map `working_directory` to a branch name (constructor accepts a mapping strategy or callable)
5. Write unit tests mocking HTTP calls (use `httpx` or `aiohttp` mock)

**Acceptance criteria:**

- `CursorCloudEngine` conforms to `ExecutionEngine` protocol
- Agent creation sends repo URL, branch, and prompt
- Polling respects timeout and backoff configuration
- Terminal states (success, failure) are correctly mapped to `EngineResult`

**Depends on:** 2

---

### 10. Create software-dev domain pack

Build the first domain pack in this repo's `workflow/` directory, extracting prompts from the existing `.agents/` skills and configuring engines per step.

**Steps:**

1. Create `workflow/domain.json` with step definitions (plan, execute, review, verify, document, finalize), engine config (raw-llm default, cursor-cli for execute), tool bindings, and skillRules
2. Create `workflow/prompts/plan.md` — extract LLM instructions from `.agents/skills/workflow/plan/SKILL.md`, strip orchestration logic, keep only what the LLM needs to produce a plan
3. Create `workflow/prompts/execute.md` — extract from `.agents/skills/workflow/implement/SKILL.md`
4. Create `workflow/prompts/review.md` — extract from `.agents/skills/workflow/code-review/SKILL.md`, include GateDecision output format
5. Create `workflow/prompts/verify.md` — extract from `.agents/skills/workflow/code-verification/SKILL.md`, include GateDecision output format
6. Create `workflow/prompts/document.md` and `workflow/prompts/finalize.md` — extract from documentation-update and commit/push-pr skills
7. Copy relevant rules from `.agents/rules/` to `workflow/rules/` (coding-standards, plan, etc.)

**Acceptance criteria:**

- `DomainPack.load("./workflow")` succeeds without errors
- Each step in `domain.json` has a corresponding prompt file in `workflow/prompts/`
- Review and verify prompts instruct the LLM to produce output parseable as `GateDecision`
- Engine config maps plan/review/verify to raw-llm and execute to cursor-cli

**Depends on:** 4

---

### 11. End-to-end integration test

Run a real task through the full orchestrator using the software-dev domain pack. Validate state transitions, gate behavior, checkpointing, and output.

**Steps:**

1. Write an integration test that loads the software-dev domain pack, builds the graph with SQLite checkpointer, and invokes with a simple task (e.g., "add a utility function")
2. Mock or stub engines to return canned responses (plan text, implementation confirmation, PASS gate decisions) — avoid real API calls in CI
3. Assert state transitions: each step updates the correct state field and trace entry
4. Assert gate behavior: inject an ISSUES response for review, verify the graph halts at END
5. Assert checkpoint resume: interrupt after plan step, resume thread, verify it continues from execute
6. Run with real engines manually (not in CI) to validate end-to-end with actual LLM calls

**Acceptance criteria:**

- Graph executes all steps in order when all gates pass, final state is complete
- Graph halts at the correct point when a gate returns ISSUES
- Resumed thread skips already-completed steps
- No orchestrator code references domain-specific concepts (software, code, git, etc.)

**Depends on:** 6, 7, 8, 9, 10

---

### 12. Add structured observability and tracing

Add step-level logging, forced reasoning enforcement, and per-run trace artifact output.

**Steps:**

1. Create `packages/gateflow/src/gateflow/observability.py`
2. Implement step-level structured logging: emit a log record on node entry/exit with step name, duration, token usage, and state diff
3. Enforce `NodeOutput` schema on engine results — parse or validate that reasoning, assumptions, confidence, blind_spots are present
4. Implement trace writer: after graph completion, serialize the full trace list (from state) to a JSON file with task ID, domain name, timestamps, per-step metrics, and gate decisions
5. Write unit tests for trace serialization and reasoning validation

**Acceptance criteria:**

- Each step execution emits structured log records (parseable, not just print statements)
- Missing reasoning fields in engine output produce a warning or error (configurable)
- Completed workflow produces a JSON trace file with all step metrics
- Trace schema is domain-agnostic

**Depends on:** 11

---

### 13. Add trust levels and interrupt configuration

Implement configurable interrupt points based on trust levels, with approve/modify/reject actions at each interrupt.

**Steps:**

1. Create `packages/gateflow/src/gateflow/interrupts.py`
2. Define `TrustLevel` enum: autonomous, gates_only, review_all, cautious — each mapping to a set of interrupt-before step names
3. Implement `get_interrupt_points(config)` that resolves trust level + per-node overrides into a list of interrupt-before nodes
4. Wire into `build_graph()` via LangGraph's `interrupt_before` parameter
5. Implement state modification on resume: allow callers to patch state (edit plan, override gate verdict) before continuing
6. Write integration tests: set trust level to `gates_only`, verify graph pauses before review/verify; resume with modified state, verify it propagates

**Acceptance criteria:**

- Each trust level produces the correct set of interrupt points
- Per-node overrides add or remove interrupts beyond the trust level default
- Graph pauses at interrupt points and resumes with (optionally modified) state
- `autonomous` trust level produces zero interrupts

**Depends on:** 11

---

### 14. Add parallel execution and resource management

Enable running multiple tasks concurrently with workspace isolation and resource controls.

**Steps:**

1. Create `packages/gateflow/src/gateflow/resources.py`
2. Implement `run_batch(tasks, domain)` using `asyncio.gather` — each task gets its own thread ID and workspace
3. Add semaphore-based LLM concurrency limiter (configurable max parallel API calls)
4. Add per-task and global token budget with circuit breaker (halt task if budget exceeded)
5. Define workspace isolation hook in DomainPack config (e.g., `isolation_strategy` field) — orchestrator calls a domain-provided callable to set up/tear down isolated workspaces
6. Write integration tests: run 3 tasks in parallel with a concurrency limit of 2, verify only 2 engines run simultaneously

**Acceptance criteria:**

- Multiple tasks execute concurrently with independent state and checkpoints
- LLM concurrency respects the configured semaphore limit
- Token budget halts a task when exceeded without affecting other tasks
- Workspace isolation hook is called before task execution

**Depends on:** 11

---

### 15. Build CLI

Ship a command-line interface for running workflows from the terminal.

**Steps:**

1. Add `click` (or `typer`) as a dependency
2. Create `packages/gateflow/src/gateflow/cli.py` with commands: `run`, `status`, `list`, `trace`
3. `run` command: load domain pack from `--domain` (default `./workflow`), resolve task, invoke graph, print result
4. `status` command: load checkpoint for task, print current state and latest trace summary
5. `list` command: enumerate all checkpointed threads, print task IDs and states
6. `trace` command: print full or per-step trace from trace artifact
7. Register CLI entry point in `pyproject.toml`

**Acceptance criteria:**

- `gateflow run task-001` loads the domain pack, runs the workflow, and prints the final status
- `gateflow status task-001` shows current step and state summary
- `gateflow list` shows all known tasks
- `--domain` flag overrides the domain pack path

**Depends on:** 11

---

### 16. Implement gate failure retry loops

Add configurable automatic retries when a gate returns ISSUES, re-invoking the target step with issues appended to the prompt.

**Steps:**

1. Extend step definition schema in domain.json with optional `max_retries` and `retry_target` fields
2. Update `gate_check()` in `graph.py` to track retry count in state and route to `retry_target` instead of END when retries remain
3. When retrying, append the gate's issues to the target step's prompt so the engine can address them
4. After `max_retries` exhausted, route to END as before
5. Write unit tests: gate fails twice then passes on third attempt; gate exhausts retries and halts

**Acceptance criteria:**

- Gate failure routes to retry_target when retries remain, to END when exhausted
- Retry count is tracked in state and persisted in checkpoint
- Retried step receives the previous gate's issues in its prompt
- Steps without `max_retries` configured behave as before (immediate halt on ISSUES)

**Depends on:** 11

---

### 17. Add per-step context strategy

Allow each step to declare whether it explores context via tools or receives pre-injected context from the orchestrator.

**Steps:**

1. Extend step definition schema with optional `context_strategy` (explore | inject) and `inject` fields (list of state keys to inject)
2. Update `make_node` / `inject_state` to pre-inject specified state fields into the prompt when strategy is `inject`
3. When strategy is `explore`, pass the prompt as-is (agent uses tools to find context)
4. Update software-dev domain pack: set review/verify to `inject` with `["diff", "plan"]`, set execute to `explore`
5. Write unit tests: verify inject strategy adds state content to prompt, explore strategy does not

**Acceptance criteria:**

- Steps with `context_strategy: inject` receive specified state fields in their prompt
- Steps with `context_strategy: explore` receive only the base prompt
- Domain pack config controls the strategy per step without code changes
- Default behavior (no context_strategy) is `explore`

**Depends on:** 11

---

### 18. Implement Claude Agent SDK engine

Build the in-process engine wrapping the Claude Agent SDK with hook-based observability and tool restrictions.

**Steps:**

1. Add `claude-code-sdk` (or equivalent) as an optional dependency in `pyproject.toml`
2. Create `packages/gateflow/src/gateflow/engines/claude_agent.py` with `ClaudeAgentEngine` class
3. Implement `run()`: call `query()` with prompt, map `allowed_tools` and `permission_mode` to SDK options, set `cwd` from `working_directory`
4. Wire `PreToolUse` hook for logging every tool call
5. Write unit tests mocking the SDK's `query` function

**Acceptance criteria:**

- `ClaudeAgentEngine` conforms to `ExecutionEngine` protocol
- `allowed_tools` and `permission_mode` are correctly mapped to SDK parameters
- `PreToolUse` hook logs tool calls
- Engine is importable only when the optional dependency is installed (graceful import error otherwise)

**Depends on:** 2
