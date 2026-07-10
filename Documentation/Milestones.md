# Wasm3 External Memory Injection — Milestones

version: 1.0    
owner: "Your Name"    
repo: "your-repo"

---

> Authoritative milestone definitions for the project.
>
> Related: [design.md](Design.md), [agenticworkflow.md](AgenticWorkFlow.md), [AgentThinking.md](AgentThinking.md)

---

## Table of Contents

| Milestone | Goals File | Status | Why | Impact |
| --- | --- | --- | --- | --- |
| [Milestone 1: External Memory Injection](#milestone-1) | [goals1.md](goals1.md) | Not Started | Enables state rollback without re-init | Core capability for snapshot/restore |
| [Milestone 2: Multi-Instance Shared Memory](#milestone-2) | [goals2.md](goals2.md) | Not Started | Enables concurrent wasm instances on shared state | Collaborative wasm execution |

---

<a id="milestone-1"></a>

## Milestone 1: External Memory Injection

**Intent:** Allow wasm3 callers to provide and swap externally-managed linear memory buffers, enabling state rollback without re-initializing the wasm machine.

**Why it matters:**

- State rollback is a core requirement for deterministic replay, undo, and time-travel debugging
- Current wasm3 allocates memory internally, making snapshot/restore expensive (full re-init required)
- External memory injection is the foundation for all future memory-sharing features

**Impact:**

- Callers can snapshot and restore wasm state in O(1) via `m3_SetMemory`
- Zero overhead on the hot execution path — same VM dispatch, same `m3MemData` macro
- Full backward compatibility — existing code paths and tests remain unchanged

**Status:** Not Started - 0/5 goals complete. See [goals1.md](goals1.md) for details.

**Goals:** [goals1.md](goals1.md)

---

<a id="milestone-2"></a>

## Milestone 2: Multi-Instance Shared Memory

**Intent:** Enable multiple wasm3 instances to operate on the same underlying physical memory pages via memory-mapped files, with per-instance headers.

**Why it matters:**

- Collaborative wasm execution requires multiple instances to read/write shared state
- Memory-mapped files provide cross-platform shared memory without custom IPC
- Each instance retains its own `M3MemoryHeader` for independent stack bounds and runtime back-pointers

**Impact:**

- Multiple wasm3 instances can operate on shared data concurrently
- Platform abstraction layer supports Windows, Linux, macOS, and iOS
- Application-level concurrency model — no built-in CoW or locking

**Status:** Not Started - 0/3 goals complete. See [goals2.md](goals2.md) for details.

**Goals:** [goals2.md](goals2.md)

---

## Guidelines

- Use one milestone for each major stage of the project.
- Keep milestones thematic rather than overly granular.
- Link every milestone to a goals file.
- Update milestone status as goals progress.
- Use `AgentThinking.md` only for temporary task notes, not for milestone definitions.
