# OpenAI "Harness Engineering" - Analysis Report

Source: [openai.com/index/harness-engineering](https://openai.com/index/harness-engineering/) (Feb 11, 2026)
Author: Ryan Lopopolo, OpenAI Engineering

OpenAI built and shipped an internal product with **zero manually-written code** over five months using Codex agents. ~1M lines of code, ~1,500 PRs, 3 engineers (later 7). They claim ~10x speed vs. manual coding.

---

## Key Learnings

**1. The environment is the product, not the code.**
Early progress was slow not because the agent was weak, but because the environment was underspecified. The primary engineering job became: build the scaffolding that lets agents do useful work.

**2. AGENTS.md as table of contents, not encyclopedia.**
A monolithic instruction file failed. It crowded out task context, rotted quickly, and was impossible to verify. What worked: a short (~100 line) AGENTS.md pointing to a structured `docs/` knowledge base with progressive disclosure.

**3. Repository = single source of truth for agents.**
Anything not in the repo doesn't exist to the agent. Slack discussions, Google Docs, tacit knowledge - all invisible. The team learned to encode decisions into versioned markdown artifacts in the repo.

**4. Enforce invariants, not implementations.**
Strict architectural boundaries (layered domain model, dependency direction rules) enforced via custom linters and structural tests. But within those boundaries, agents have full autonomy in how they express solutions.

**5. Agent legibility > human readability.**
Code is optimized for the agent's ability to reason about it, not human style preferences. If it's correct, maintainable, and legible to future agent runs, it meets the bar.

**6. Feedback loops replace QA bottlenecks.**
Made the app bootable per git worktree so agents could launch isolated instances. Wired Chrome DevTools Protocol for DOM snapshots, screenshots, navigation. Added local observability (logs via LogQL, metrics via PromQL, traces via TraceQL). Agents self-validate.

**7. Continuous garbage collection beats Friday cleanups.**
Initially spent 20% of the week cleaning "AI slop." Didn't scale. Replaced with "golden principles" encoded in-repo + recurring background agent tasks that scan for drift, update quality grades, and open refactoring PRs.

**8. High throughput changes merge philosophy.**
Minimal blocking merge gates. Short-lived PRs. Test flakes addressed with follow-up runs, not blocking. Corrections are cheap; waiting is expensive.

---

## System Build-Up: Step by Step

| Phase | What They Did | Why It Mattered |
|-------|--------------|-----------------|
| **1. Empty repo + scaffold** | Codex generated initial repo structure, CI, formatting rules, package manager, framework, and the first AGENTS.md. | Established that agents own the code from line zero. |
| **2. Depth-first building blocks** | Broke goals into small building blocks. Prompted agent to construct each, then composed them for complex tasks. | Built capability incrementally instead of attempting large tasks that fail. |
| **3. Structured knowledge base** | Replaced monolithic AGENTS.md with a `docs/` hierarchy: design docs, exec plans, product specs, references, quality scores. | Gave agents progressive disclosure - a map, not a manual. |
| **4. Architectural enforcement** | Defined layered domain architecture (Types -> Config -> Repo -> Service -> Runtime -> UI). Custom linters enforce dependency direction. | Prevented architectural drift at scale. Agents can't violate boundaries. |
| **5. App legibility for agents** | Made app bootable per worktree. Integrated Chrome DevTools Protocol. Agents drive the UI, take screenshots, reproduce bugs. | Agents self-validate beyond just running tests. |
| **6. Observability stack** | Ephemeral per-worktree observability: Vector -> Victoria Logs/Metrics/Traces. Agents query via LogQL/PromQL/TraceQL. | Enabled performance-oriented prompts ("startup < 800ms"). |
| **7. Agent-to-agent review** | Pushed review from humans to agents. Codex reviews its own changes, requests additional agent reviews, iterates until reviewers satisfied (Ralph Wiggum Loop). | Removed human review as throughput bottleneck. |
| **8. Garbage collection system** | Golden principles in-repo. Background agent tasks scan for deviations on a cadence, open refactoring PRs. Quality grades tracked. | Continuous debt paydown replaces manual cleanup sprints. |
| **9. End-to-end autonomy** | Single prompt -> validate codebase -> reproduce bug -> record video -> fix -> validate fix -> record resolution video -> open PR -> handle feedback -> merge. | Full agent-driven feature lifecycle with human escalation only when judgment needed. |

---

## Reality Check

OpenAI had their own model, a handpicked team, and a product shaped around agent capabilities from day zero. The transferable lessons are about **system design**, not raw throughput:

- Repository as the single source of agent-accessible truth
- Progressive disclosure over monolithic instructions
- Mechanical enforcement over advisory documentation
- Continuous automated cleanup over manual debt sprints
- Making the application itself legible to agents
