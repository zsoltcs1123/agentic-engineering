# Task Detailing

Define implementation steps, implementation requirements, verification scenarios, and dependencies for each task.

## Process

Walk through tasks in logical order. For each task:

### Define Implementation Steps

Break the task into up to 7 concrete actions. Each step should be:

- A specific action, not a vague phase
- Ordered within the task (step 2 builds on step 1)
- Verifiable — you can tell if it's done

**Abstraction level:** Steps should name _what_ to do and _which domain concepts_ are involved, not _where to put them_ or _how to wire them_. Include entity names, behaviors, and contracts. Omit file paths, module locations, full method signatures, and language-specific type constructs — the implementer decides those.

**Good steps:** "Define the token schema with user FK, hash, and expiry columns"
**Bad steps:** "Handle the data layer"
**Also bad:** "Create `packages/auth/src/models/token.py` with a `Token` class containing `user_id: int`, `token_hash: str`, `expires_at: datetime`" — too prescriptive about location and types

### Define Implementation Requirements

Implementation requirements are structural and design constraints checkable by reading the code — no runtime needed. They answer _"can I verify this by inspecting the code?"_ — not _"does it handle edge cases?"_ (that's verification).

**Rule:** If it requires running the software to check, it's not an implementation requirement — it belongs in verification scenarios.

Consolidate the task's objectives into a short bullet list of statically verifiable constraints. Requirements should be:

- Checkable by reading the code (no runtime needed)
- Specific (not "works correctly" but "all credentials reference `${ENV_VAR}` syntax, no hardcoded secrets")
- Complete (covers the task's full scope)
- **Not a restatement of the implementation steps** — requirements describe _what the code must look like_, not _how to get there_
- **Not test cases** — edge cases, error paths, and input variations belong in verification scenarios

**Not this:** "POST /reset-password returns 200" or "Valid email produces a persisted token" — these need runtime to check, so they belong in verification scenarios. The implementation requirement is: "Route handler uses a uniform response shape for both existing and non-existing emails."

**Not this:** "Expired token returns 400", "Used token returns 409" — these are input variations (test cases), not structural constraints. The implementation requirement is: "Token validation logic checks expiry, used flag, and existence before proceeding."

### Define Verification Scenarios

Verification scenarios answer _"does the code work correctly?"_ They exercise code logic under varied inputs — happy paths, error cases, and boundary conditions. Each scenario is a specific input/condition paired with an expected behavior.

#### Format

```
**Verification scenarios:**
- [input/condition] — [expected behavior]
- [input/condition] — [expected behavior]
```

#### Coverage

For each task, cover:

1. **Happy path** — the primary success case
2. **Error cases** — invalid input, missing data, unauthorized access
3. **Edge cases** — boundary values, empty inputs, concurrent access (when relevant)

Not every task needs all three. Use judgment — a simple config task may only need a happy path scenario. A security-sensitive endpoint needs thorough error and edge coverage.

#### Rules

- Each scenario must be specific enough to translate directly into a test case
- Name the input and the expected behavior — don't leave either vague
- Don't restate implementation requirements as scenarios; go deeper
- Keep scenarios at the _what_ level — don't prescribe test framework, assertions, or setup code

**Not this:** "Migration runs successfully", "Model is queryable" — these confirm existence, not behavior under varied conditions. They belong in implementation requirements.

### Record Dependencies

Note which prior tasks this one depends on. Use task numbers from the identification phase. If a task has no dependencies, mark "None".

#### Example

```
### Task 2: Implement reset request endpoint
Endpoint accepts an email, generates a token, and queues a notification.

**Steps:**
1. Create the route and controller
2. Add token generation logic (secure random, hashed storage)
3. Queue email notification with reset link
4. Ensure response is identical for existing and non-existing emails

**Implementation requirements:**
- Route handler uses a uniform response shape for both existing and non-existing emails
- Token generation uses cryptographically secure random bytes with hashed storage
- Notification is queued asynchronously, not sent inline

**Verification scenarios:**
- Registered email — returns 200, token persisted, notification queued
- Unregistered email — returns 200, no token created, no notification queued
- Malformed email — returns 400 with validation error
- Two rapid requests for same email — each produces a distinct token

**Depends on:** 1

---
```
