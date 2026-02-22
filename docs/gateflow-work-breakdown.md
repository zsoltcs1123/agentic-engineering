# Work Breakdown: Gateflow

## Summary

Build Gateflow — a domain-agnostic, code-based workflow orchestrator on LangGraph — from placeholder package to working system, then extend with advanced features.

| #   | Task                                           | Phase | Depends On     | Status  |
| --- | ---------------------------------------------- | ----- | -------------- | ------- |
| 1   | Define WorkflowState and base models           | MVP   | None           | DONE    |
| 2   | Define ExecutionEngine protocol                | MVP   | 1              | DONE    |
| 3   | Implement raw LLM engine                       | MVP   | 2              | DONE    |
| 4   | Implement DomainPack loader                    | MVP   | 2              | DONE    |
| 5   | Build dynamic graph constructor                | MVP   | 1, 4           | DONE    |
| 6   | Implement make_node and prompt assembly        | MVP   | 3, 5           | DONE    |
| 7   | Add SQLite checkpointer                        | MVP   | 5              | DONE    |
| 8   | Implement Cursor CLI engine                    | MVP   | 2              | DONE    |
| 9   | Implement Cursor Cloud API engine              | MVP   | 2              | DONE    |
| 10  | Create software-dev domain pack                | MVP   | 4              | DONE    |
| 11  | End-to-end integration test                    | MVP   | 6, 7, 8, 9, 10 | PENDING |
| 12  | Add structured observability and tracing       | v1    | 11             | PENDING |
| 13  | Add trust levels and interrupt configuration   | v1    | 11             | PENDING |
| 14  | Add parallel execution and resource management | v1    | 11             | PENDING |
| 15  | Build CLI                                      | v1    | 11             | PENDING |
| 16  | Implement gate failure retry loops             | v1    | 11             | PENDING |
| 17  | Add per-step context strategy                  | v1    | 11             | PENDING |
| 18  | Implement Claude Agent SDK engine              | v1    | 2              | PENDING |

## Tasks

### 1. Define WorkflowState and base models

Define the core data structures that flow through the graph: the workflow state, structured output models, and the engine result container. These are the foundation everything else imports.

**Steps:**

1. Add langgraph and pydantic as dependencies
2. Define WorkflowState as a LangGraph-compatible state type with fields for task identity, description, working directory, status, plan, review result, verification result, trace, and domain data
3. Define structured output models — EngineResult with output, tool calls, token usage, and duration; NodeOutput with reasoning, assumptions, confidence, blind spots, and output; GateDecision with verdict, reasoning, evidence, blind spots, and issues — with appropriate validation constraints
4. Export the public API from the package root
5. Write unit tests for model validation

**Acceptance criteria:**

- WorkflowState is importable and usable as a LangGraph state type
- Pydantic models enforce their constraints (verdict literals, confidence bounds)
- All types are exported from the package root

**Verification scenarios:**

- Instantiate WorkflowState with all required fields, use as a LangGraph state annotation — no errors
- GateDecision with invalid verdict value — rejected by validation
- NodeOutput with out-of-range confidence — rejected by validation
- EngineResult with no optional fields provided — sensible defaults populated

**Depends on:** None

---

### 2. Define ExecutionEngine protocol

Create the protocol that all execution engines must implement. This is the contract between the orchestrator and any backend.

**Steps:**

1. Define the ExecutionEngine protocol with a run method returning EngineResult
2. Define a permission mode type for the permission_mode parameter
3. Export from package root
4. Write a unit test verifying protocol conformance at runtime

**Acceptance criteria:**

- ExecutionEngine is a runtime-checkable protocol
- A class implementing run is recognized as conforming
- Static type checking passes on conforming implementations

**Verification scenarios:**

- Conforming class — passes isinstance check
- Non-conforming class (missing run method) — fails isinstance check
- Conforming class with wrong return type — static type checker catches mismatch

**Depends on:** 1

---

### 3. Implement raw LLM engine

Build the simplest engine: a direct Anthropic API call with no agent tools. Used for steps that only need LLM reasoning (plan, review, verify).

**Steps:**

1. Implement an engine that calls the Anthropic messages API directly
2. Accept model name and max_tokens as configuration with sensible defaults
3. Map prompt to user message, parse response into EngineResult
4. Handle API errors (rate limit, auth, timeout) with clear error messages
5. Write unit tests using a mocked Anthropic client

**Acceptance criteria:**

- Conforms to ExecutionEngine protocol
- Prompt is sent as a user message, response text lands in EngineResult output
- Token usage from the API response is captured
- API errors raise descriptive exceptions, not raw HTTP errors

**Verification scenarios:**

- Mock client returning valid response — output and token_usage match expected values
- Mock client raising rate limit error — engine raises a descriptive error
- Empty prompt — engine sends the request without client-side rejection

**Depends on:** 2

---

### 4. Implement DomainPack loader

Build the component that reads a domain directory and provides prompt assembly, engine resolution, and step ordering.

**Steps:**

1. Implement loading from a directory path: validate structure, parse config, verify referenced files exist
2. Implement prompt assembly: load base prompt for a step and append configured rule texts
3. Implement engine resolution: return per-step override or default engine
4. Implement step list access: return ordered steps from config
5. Write unit tests with a fixture domain pack directory

**Acceptance criteria:**

- Loading raises clear errors for missing or invalid config
- Prompt assembly concatenates base prompt and applicable rules
- Engine resolution returns override when configured, default otherwise
- Step list returns ordered steps from config

**Verification scenarios:**

- Directory missing config file — raises clear error naming the missing file
- Valid pack, prompt for a step with rules — returned string contains base prompt and rule texts
- Engine resolution for overridden step — returns override; for non-overridden step — returns default

**Depends on:** 2

---

### 5. Build dynamic graph constructor

Implement the function that reads step definitions from a DomainPack and constructs a LangGraph StateGraph with nodes, edges, and conditional gate edges.

**Steps:**

1. Implement a function that takes a DomainPack and supporting config and returns a compiled LangGraph graph
2. Add a node per step, wire sequential edges for non-gate steps and conditional edges for gate steps
3. Gate steps route to the next step on PASS and to END on ISSUES
4. Set entry and terminal points
5. Write unit tests verifying node count, edge topology, and gate routing

**Acceptance criteria:**

- Returns a compiled graph with one node per step
- Gate steps have conditional edges; non-gate steps have unconditional edges
- Graph compiles without errors for valid domain config

**Verification scenarios:**

- 3-step domain with one gate step — gate node has conditional edges, others have unconditional edges
- 1-step domain — graph has a single node with edge to END
- Two consecutive gate steps — both have conditional edges wired correctly

**Depends on:** 1, 4

---

### 6. Implement make_node and prompt assembly

Build the node factory that creates the async function each graph node executes: assemble prompt, inject state context, delegate to engine, update state.

**Steps:**

1. Implement a factory that returns an async node function for a given step
2. Implement state injection into the prompt (task description, plan, working directory, domain data at minimum)
3. Implement state update after engine execution: write output to the appropriate state field, append to trace
4. For gate steps, parse engine output into a GateDecision and write the verdict to state
5. Write unit tests with a mock engine verifying prompt assembly and state updates

**Acceptance criteria:**

- Node calls the correct engine with assembled prompt and the step's tool/permission config
- State is updated with engine output under the correct field
- Gate nodes parse output into GateDecision and the verdict is available for routing
- Trace accumulates an entry per executed step

**Verification scenarios:**

- Mock engine run — prompt contains base prompt text and injected state fields
- Gate node with PASS verdict — state reflects parsed decision, routing returns pass
- Gate node with ISSUES verdict — state stores issues, routing returns issues
- Execute 3 nodes sequentially — trace has 3 entries in order

**Depends on:** 3, 5

---

### 7. Add SQLite checkpointer

Configure LangGraph's built-in async SQLite checkpointer so workflow state persists across runs and supports resume.

**Steps:**

1. Add the appropriate LangGraph checkpoint dependency
2. Implement a factory function that creates the async SQLite checkpointer for a given path
3. Wire the checkpointer into the graph builder
4. Write an integration test: run partway, resume from checkpoint, verify state continuity

**Acceptance criteria:**

- Workflow state survives process restart — resuming a thread continues from the last completed step
- Checkpoint database is created at the specified path
- Graph builder accepts and uses the checkpointer

**Verification scenarios:**

- Run to completion — checkpoint database file exists and is non-empty
- Interrupt after step 2 of 4, resume with same thread — execution continues from step 3
- Resume with non-existent thread — starts from the beginning

**Depends on:** 5

---

### 8. Implement Cursor CLI engine

Build the subprocess-based engine that invokes the Cursor CLI agent with JSON output, mapping allowed tools and permission mode to CLI flags.

**Steps:**

1. Implement an engine that spawns the Cursor CLI as a subprocess
2. Map permission_mode to appropriate CLI flags
3. Parse JSON output into EngineResult, handle non-zero exit codes
4. Accept configurable path for non-standard Cursor installations
5. Write unit tests mocking the subprocess

**Acceptance criteria:**

- Conforms to ExecutionEngine protocol
- Subprocess is invoked with correct arguments for JSON output
- Permission mode flags are applied correctly
- Non-zero exit codes and malformed JSON produce descriptive errors

**Verification scenarios:**

- Mock subprocess returning valid JSON — output matches expected EngineResult
- Permission mode "acceptEdits" — correct flag present; default mode — flag absent
- Non-zero exit code — descriptive error including stderr content

**Depends on:** 2

---

### 9. Implement Cursor Cloud API engine

Build the REST-based engine that creates remote Cursor agents and polls until completion.

**Steps:**

1. Implement an engine that creates a remote Cursor agent via REST API
2. Implement polling with configurable interval, timeout, and backoff
3. Map working directory to a branch name
4. Map terminal states to EngineResult
5. Write unit tests mocking HTTP calls

**Acceptance criteria:**

- Conforms to ExecutionEngine protocol
- Agent creation sends repo, branch, and prompt
- Polling respects timeout and backoff configuration
- Terminal states correctly map to EngineResult

**Verification scenarios:**

- Mock create returns agent ID, poll returns completed — output matches expected EngineResult
- Poll never reaches terminal state within timeout — timeout error raised
- Create returns 401 — auth error with actionable message

**Depends on:** 2

---

### 10. Create software-dev domain pack

Build the first domain pack for software development, extracting prompts from the existing reference skills and configuring engines per step.

**Steps:**

1. Create the domain pack directory with a config defining steps (plan, execute, review, verify, document, finalize), engine config, tool bindings, and rule assignments
2. Extract LLM-facing prompts from the existing workflow skills — strip orchestration logic, keep only what the LLM needs
3. Ensure review and verify prompts instruct the LLM to produce output parseable as a gate decision
4. Copy relevant rules from the existing rules directory

**Acceptance criteria:**

- DomainPack loader loads the pack successfully
- Each step has a corresponding prompt file
- Review and verify prompts produce gate-decision-compatible output
- Engine config maps reasoning steps to raw LLM, execution steps to Cursor CLI

**Verification scenarios:**

- Load succeeds — step list returns expected steps in order
- Review prompt content — contains gate decision output format instructions
- Engine resolution per step — reasoning steps resolve to raw LLM engine, execution steps to CLI engine

**Depends on:** 4

---

### 11. End-to-end integration test

Validate the full orchestrator with the software-dev domain pack: state transitions, gate behavior, checkpointing, and output.

**Steps:**

1. Write a test that loads the domain pack, builds the graph with checkpointer, and runs a simple task
2. Use mock/stub engines returning canned responses — avoid real API calls in CI
3. Assert state transitions, gate behavior (halt on ISSUES), and checkpoint resume
4. Verify no orchestrator code references domain-specific concepts

**Acceptance criteria:**

- Graph executes all steps when all gates pass, producing a complete final state
- Graph halts correctly when a gate returns ISSUES
- Resumed thread skips already-completed steps
- Orchestrator code is domain-agnostic

**Verification scenarios:**

- All gates pass — final status is "completed", all state fields populated
- ISSUES at review gate — graph halts, steps after review are not executed
- Interrupt and resume — execution continues from correct step, earlier results preserved

**Validation scenarios:**

- Run the full orchestrator with mock engines against the software-dev domain pack, verify final state is "completed" and trace contains all steps — Automation: full
- Interrupt mid-workflow, resume with same thread ID, verify continuation from correct step — Automation: full

**Depends on:** 6, 7, 8, 9, 10

---

### 12. Add structured observability and tracing

Add step-level logging, reasoning enforcement, and per-run trace artifact output.

**Steps:**

1. Implement step-level structured logging: emit a log record on node entry/exit with step name, duration, and token usage
2. Enforce the NodeOutput schema on engine results — validate that reasoning fields are present
3. Implement a trace writer: after graph completion, serialize the full trace to a JSON file with task ID, timestamps, per-step metrics, and gate decisions
4. Write unit tests for trace serialization and reasoning validation

**Acceptance criteria:**

- Each step execution emits structured log records
- Missing reasoning fields produce a warning or error (configurable)
- Completed workflow produces a JSON trace file
- Trace schema is domain-agnostic

**Verification scenarios:**

- 3-step graph run — 3 structured log records emitted with step name, duration, and token usage
- Engine output missing reasoning fields with enforcement enabled — warning or error raised
- Completed workflow — JSON trace file contains task ID, per-step metrics, and gate decisions

**Depends on:** 11

---

### 13. Add trust levels and interrupt configuration

Implement configurable interrupt points based on trust levels, with approve/modify/reject actions at each interrupt.

**Steps:**

1. Define trust levels (autonomous, gates_only, review_all, cautious) mapping to interrupt-before step sets
2. Support per-node overrides that add or remove interrupts
3. Wire into the graph builder via LangGraph's interrupt_before parameter
4. Allow callers to modify state on resume (edit plan, override gate verdict)
5. Write integration tests per trust level

**Acceptance criteria:**

- Each trust level produces the correct set of interrupt points
- Per-node overrides add or remove interrupts
- Graph pauses at interrupt points and resumes with optionally modified state
- Autonomous mode produces zero interrupts

**Verification scenarios:**

- Autonomous trust level — empty interrupt list
- Gates_only — interrupts at review and verify steps only
- Gates_only with per-node override adding plan — plan step is also interrupted
- Resume with modified state — next step receives the modification

**Depends on:** 11

---

### 14. Add parallel execution and resource management

Enable running multiple tasks concurrently with workspace isolation and resource controls.

**Steps:**

1. Implement batch execution — each task gets its own thread and workspace
2. Add semaphore-based LLM concurrency limiting
3. Add per-task and global token budget with circuit breaker
4. Define a workspace isolation hook in domain config — orchestrator calls a domain-provided callable for setup/teardown
5. Write integration tests for concurrency limiting and budget enforcement

**Acceptance criteria:**

- Multiple tasks execute concurrently with independent state and checkpoints
- LLM concurrency respects the configured limit
- Token budget halts a task when exceeded without affecting others
- Workspace isolation hook is called before task execution

**Verification scenarios:**

- 3 tasks with concurrency limit 2 — at most 2 engine runs active simultaneously
- Token budget exceeded mid-task — that task halts, others continue unaffected
- Each parallel task — gets its own thread and independent checkpoint

**Depends on:** 11

---

### 15. Build CLI

Ship a command-line interface for running workflows from the terminal.

**Steps:**

1. Add a CLI framework dependency
2. Implement commands: run (execute workflow), status (show current state), list (enumerate tasks), trace (show trace)
3. Support a --domain flag to override the domain pack path
4. Register the CLI entry point in the package config

**Acceptance criteria:**

- run command loads a domain pack, executes the workflow, and prints final status
- status command shows current step and state summary for a task
- list command shows all known tasks
- --domain flag overrides the domain pack path

**Verification scenarios:**

- Run command with valid domain pack — workflow executes and final status is printed
- Status command with existing checkpoint — shows current step and state
- List command with multiple tasks — all tasks displayed

**Validation scenarios:**

- Install the package, invoke the run command with the software-dev domain pack and mock engines, verify output shows completion status — Automation: full
- Invoke the status command for an in-progress task, verify it displays current step — Automation: full
- Invoke the list command with multiple tasks present, verify all are listed — Automation: full

**Depends on:** 11

---

### 16. Implement gate failure retry loops

Add configurable automatic retries when a gate returns ISSUES, re-invoking the target step with issues appended to the prompt.

**Steps:**

1. Extend the step definition schema with optional retry configuration (max retries, retry target)
2. Update gate routing to loop back to the target step when retries remain, halt when exhausted
3. Append the gate's issues to the retried step's prompt
4. Track retry count in state, persist in checkpoint
5. Write unit tests for retry looping and exhaustion

**Acceptance criteria:**

- Gate failure routes to retry target when retries remain, to END when exhausted
- Retry count is tracked in state and persisted
- Retried step receives the previous gate's issues in its prompt
- Steps without retry config behave as before (immediate halt)

**Verification scenarios:**

- Gate fails with retries configured — re-invokes target step with issues appended, up to max retries
- Retries exhausted — routes to END
- No retry config on step — immediate halt on gate failure (backward compatible)
- Retry count survives checkpoint resume — resumed task continues with correct count

**Depends on:** 11

---

### 17. Add per-step context strategy

Allow each step to declare whether it explores context via tools or receives pre-injected context from the orchestrator.

**Steps:**

1. Extend step definition with optional context strategy (explore or inject) and injection field list
2. When strategy is inject, pre-inject specified state fields into the prompt
3. When strategy is explore, pass prompt as-is
4. Default to explore when not configured
5. Write unit tests verifying both strategies

**Acceptance criteria:**

- Inject strategy adds specified state fields to the prompt
- Explore strategy passes only the base prompt
- Strategy is configurable per step without code changes
- Default is explore

**Verification scenarios:**

- Inject strategy with specified fields — prompt contains those state values
- Explore strategy — prompt contains only the base prompt, no injected state
- No strategy configured — defaults to explore behavior

**Depends on:** 11

---

### 18. Implement Claude Agent SDK engine

Build the in-process engine wrapping the Claude Agent SDK with hook-based observability and tool restrictions.

**Steps:**

1. Add the Claude Agent SDK as an optional dependency
2. Implement an engine that calls the SDK, mapping allowed tools and permission mode to SDK options
3. Wire a pre-tool-use hook for logging tool calls
4. Ensure the engine is importable only when the optional dependency is installed (graceful error otherwise)
5. Write unit tests mocking the SDK

**Acceptance criteria:**

- Conforms to ExecutionEngine protocol
- Allowed tools and permission mode map correctly to SDK parameters
- Pre-tool-use hook logs tool calls
- Graceful import error when SDK is not installed

**Verification scenarios:**

- Mock SDK call — output maps correctly to EngineResult, tools and permissions are set
- Tool call during execution — hook fires for each tool call
- Import without SDK installed — descriptive ImportError raised

**Depends on:** 2
