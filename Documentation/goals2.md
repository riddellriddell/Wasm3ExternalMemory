# Wasm3 External Memory Injection – Goals (Milestone 2: *Multi-Instance Shared Memory*)

<!-- markdownlint-disable MD001 MD009 MD012 MD022 MD024 MD031 MD032 MD033 MD036 MD040 MD051 MD058 MD060 -->

version: 1.0    
owner: "Your Name"    
repo: "your-repo"

---

> **Goals and deliverables for Milestone 2: *Multi-Instance Shared Memory***
>
> **Status:** Not Started
>
> See `milestones.md` for the full milestone roadmap.

---

## Context

- **Problem:** Multiple wasm3 instances cannot operate on the same underlying memory pages. Collaborative wasm execution requires shared state without复制 copies or IPC overhead.

## Milestone 2 Goals Summary

| Goal | Status | Link |
|------|--------|------|
| Goal 2.1 – Platform Abstraction Layer | Not Started | [Jump to details](#goal-2-1) |
| Goal 2.2 – Shared Memory via Memory-Mapped Files | Not Started | [Jump to details](#goal-2-2) |
| Goal 2.3 – Multi-Instance Tests | Not Started | [Jump to details](#goal-2-3) |

**Milestone Status:** Not Started — 0/3 goals complete.

### Milestone 2 Scope

**Intent:** Enable multiple wasm3 instances to share the same physical memory pages through memory-mapped files, with per-instance headers for independent runtime state.

**What this milestone means:**

- Multiple wasm3 instances can read/write the same underlying data pages
- Each instance has its own `M3MemoryHeader` (per-instance stack bounds, runtime back-pointer)
- Cross-platform support via platform abstraction layer

**Key deliverables:**

- Platform abstraction layer for memory-mapped files
- Shared memory allocation and mapping functions
- Multi-instance test demonstrating concurrent shared state
- Documentation of concurrency model (no CoW, application-level race handling)

### Explicitly Out of Scope (Milestone 2)

- Copy-on-Write (CoW) protections
- Built-in locking or synchronization primitives
- Concurrent execution safety — left to application layer
- Single-instance external memory (Milestone 1)

---

## Solution Overview

### High-Level Architecture

- **Platform Abstraction Layer** — abstracts `CreateFileMapping`/`MapViewOfFile` (Windows) and `mmap` (POSIX) behind a common interface
- **Shared Memory Manager** — creates/opens memory-mapped files, returns usable buffer pointers
- **Per-Instance Headers** — each wasm3 instance gets its own `M3MemoryHeader` pointing to shared data pages

### Data Flow

#### Pipeline: Shared Memory Setup

1. **Shared memory created** — memory-mapped file allocated via platform API
2. **Instance 1 attaches** — `m3_SetMemory` called with mapped buffer + instance-specific header
3. **Instance 2 attaches** — `m3_SetMemory` called with same mapped buffer + different header
4. **Both instances run** — modifications to data pages visible to both

#### Pipeline: Concurrent Access

1. **Instance 1 writes** — modifies shared data pages
2. **Instance 2 reads** — sees Instance 1's changes (no CoW, no locking)
3. **Application handles races** — wasm3 provides no concurrency guarantees

---

## Milestone 2 Goals & Deliverables

<a id="goal-2-1"></a>

### Goal 2.1 – Platform Abstraction Layer

**Intent:** Create a cross-platform abstraction for memory-mapped file operations.

#### Deliverables

- **Deliverable 1:** Platform header file with common interface
  - `m3_CreateSharedMemory(name, size)` → returns `void*`
  - `m3_OpenSharedMemory(name)` → returns `void*`
  - `m3_CloseSharedMemory(ptr, size)` → unmaps and cleans up
- **Deliverable 2:** Windows implementation
  - Uses `CreateFileMapping` and `MapViewOfFile`
- **Deliverable 3:** POSIX implementation
  - Uses `mmap` and `munmap`
- **Deliverable 4:** macOS/iOS implementation
  - Uses `mmap` with `MAP_SHARED`

#### Acceptance Criteria

- [ ] Common API compiles on Windows, Linux, macOS
- [ ] `m3_CreateSharedMemory` returns valid mapped pointer
- [ ] `m3_OpenSharedMemory` returns same physical pages as creator
- [ ] `m3_CloseSharedMemory` unmaps without leaking
- [ ] No platform-specific code in wasm3 core library

#### Out of Scope

- Actual shared memory usage by wasm3 instances (Goal 2.2)
- Tests (Goal 2.3)

---

<a id="goal-2-2"></a>

### Goal 2.2 – Shared Memory via Memory-Mapped Files

**Intent:** Integrate the platform abstraction layer with wasm3's external memory API to enable multi-instance shared memory.

#### Deliverables

- **Deliverable 1:** Shared memory helper function
  - `m3_CreateSharedRuntimeMemory(name, numPages)` → creates mapped file, returns buffer suitable for `m3_SetMemory`
- **Deliverable 2:** Documentation of per-instance header model
  - Each instance calls `m3_SetMemory` with the shared buffer
  - Each instance gets its own `M3MemoryHeader` (runtime, maxStack, length)
  - Data pages are shared; headers are per-instance
- **Deliverable 3:** Example or integration guide showing two instances sharing memory

#### Acceptance Criteria

- [ ] Two wasm3 instances can attach to the same shared memory buffer
- [ ] Writes by Instance A are visible to Instance B
- [ ] Each instance's `M3MemoryHeader` is independent
- [ ] `Runtime_Release` on one instance does not unmap memory for others
- [ ] Documentation explains the concurrency model

#### Out of Scope

- Concurrency protection (application responsibility)
- CoW semantics
- Tests (Goal 2.3)

---

<a id="goal-2-3"></a>

### Goal 2.3 – Multi-Instance Tests

**Intent:** Create tests demonstrating multi-instance shared memory operation.

#### Deliverables

- **Deliverable 1:** Test for shared memory creation and mapping
  - Two instances attach to same buffer
  - Both can read/write shared data
- **Deliverable 2:** Test for cross-instance data visibility
  - Instance A writes to shared memory
  - Instance B reads the written data
- **Deliverable 3:** Test for independent headers
  - Each instance has correct `numPages`, `maxStack`, `runtime`
  - Releasing one instance does not affect the other

#### Acceptance Criteria

- [ ] All 3 test scenarios pass
- [ ] Tests compile and run via CMake
- [ ] Tests cover Windows and at least one POSIX platform

#### Out of Scope

- Stress/performance testing
- Race condition testing (application responsibility)

---

## Non-Functional Guarantees

### Cross-Platform Support

- Platform abstraction layer behind common API
- Windows: `CreateFileMapping` / `MapViewOfFile`
- POSIX: `mmap` / `munmap`
- No platform-specific code in wasm3 core

### Memory Lifetime Management

- Shared memory lifetime managed by caller, not wasm3
- `Runtime_Release` on one instance does not unmap shared pages
- Multiple instances can independently attach/detach

### No Concurrency Guarantees

- wasm3 provides no locking or CoW protections
- All race conditions handled at application level
- Documented as application responsibility

---

## External Dependencies

### C Standard Library

- **Purpose:** Memory operations, string operations
- **Status:** Active (existing dependency)

### Platform APIs

- **Windows:** `CreateFileMapping`, `MapViewOfFile`, `UnmapViewOfFile`, `CloseHandle`
- **POSIX:** `mmap`, `munmap`, `shm_open` / file-backed `open`
- **Status:** Platform-specific, wrapped behind abstraction layer

### CMake

- **Purpose:** Build system with platform detection
- **Status:** Active (existing dependency)

---

## Agent Guidelines for This Milestone

When working on tasks in this milestone, anchor them to the **goals** above.

### Project Boundaries

- Platform abstraction → new files under `source/` (e.g., `m3_shared_memory.h`, `m3_shared_memory_platform.c`)
- Shared memory helpers → `m3_env.c` or new `m3_shared_memory.c`
- Tests → `test/` or `platforms/app/`
- Documentation → `Documentation/`

### Development Approach

- Implement goals sequentially: 2.1 → 2.2 → 2.3
- Platform abstraction should be testable independently before integration
- Run full test suite after each goal

### Rules Compliance

- Always respect project-level coding conventions and style guides
- Check for IDE-specific rules (see `AgenticWorkFlow.md` → IDE-Specific Agent Rules)
- Follow C99 conventions for core library code

---

## Related Documents

- **`milestones.md`** — Authoritative milestone definitions
- **`Design.md`** — Technical architecture specification
- **`AgenticWorkFlow.md`** — How AI agents collaborate on this project
