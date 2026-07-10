# Wasm3 External Memory Injection – Goals (Milestone 1: *External Memory Injection*)

<!-- markdownlint-disable MD001 MD009 MD012 MD022 MD024 MD031 MD032 MD033 MD036 MD040 MD051 MD058 MD060 -->

version: 1.0    
owner: "Your Name"    
repo: "your-repo"

---

> **Goals and deliverables for Milestone 1: *External Memory Injection***
>
> **Status:** Not Started
>
> See `milestones.md` for the full milestone roadmap.

---

## Context

- **Problem:** wasm3 allocates linear memory internally, making state snapshot and restore expensive (requires full re-initialization). Callers need O(1) buffer swap to enable rollback, undo, and time-travel scenarios.

## Milestone 1 Goals Summary

| Goal | Status | Link |
|------|--------|------|
| Goal 1.1 – Add `isExternalMemory` Flag | Not Started | [Jump to details](#goal-1-1) |
| Goal 1.2 – Implement `m3_SetMemory` API | Not Started | [Jump to details](#goal-1-2) |
| Goal 1.3 – Guard Existing Memory Functions | Not Started | [Jump to details](#goal-1-3) |
| Goal 1.4 – Write Unit Tests | Not Started | [Jump to details](#goal-1-4) |
| Goal 1.5 – Verify Backward Compatibility | Not Started | [Jump to details](#goal-1-5) |

**Milestone Status:** Not Started — 0/5 goals complete.

### Milestone 1 Scope

**Intent:** Ship a public `m3_SetMemory` API that lets callers provide externally-owned linear memory buffers to wasm3, with proper lifecycle management and full test coverage.

**What this milestone means:**

- wasm3 can accept caller-provided memory buffers via a new public API
- Externally-provided buffers are not freed or reallocated by wasm3
- The existing internal memory path remains unchanged and fully functional

**Key deliverables:**

- `isExternalMemory` flag in `M3Memory` struct
- `m3_SetMemory` function declared in `wasm3.h` and implemented in `m3_env.c`
- Guards in `ResizeMemory` and `Runtime_Release` for external memory
- Unit tests covering all new code paths
- All existing tests pass with no regressions

### Explicitly Out of Scope (Milestone 1)

- Multi-instance shared memory (Milestone 2)
- Memory-mapped file support
- CoW or concurrency protections
- Performance benchmarking beyond verifying zero overhead on hot path

---

## Solution Overview

### High-Level Architecture

- **M3Memory struct** — gains `isExternalMemory` boolean field to track buffer ownership
- **m3_SetMemory** — new public API function in `wasm3.h`, implemented in `m3_env.c`
- **ResizeMemory guard** — skips `m3_Realloc` when external; validates requested size fits buffer
- **Runtime_Release guard** — skips `m3_Free(mallocated)` when external

### Data Flow

#### Pipeline: External Memory Setup

1. **Caller allocates buffer** — manages lifetime externally
2. **m3_SetMemory called** — validates size, sets `mallocated`, populates header, sets flag
3. **m3_LoadModule called** — `InitDataSegments` copies wasm data into external buffer
4. **Execution proceeds** — VM uses `m3MemData(mallocated)` identically to internal path

#### Pipeline: Buffer Swap (Rollback)

1. **Snapshot** — caller `memcpy`s entire buffer (header + data) to separate storage
2. **Run wasm** — modifies memory contents
3. **m3_SetMemory called with snapshot** — overwrites header with current runtime/maxStack, data pages restored
4. **Execution resumes** — on restored state

---

## Milestone 1 Goals & Deliverables

<a id="goal-1-1"></a>

### Goal 1.1 – Add `isExternalMemory` Flag

**Intent:** Add a boolean field to `M3Memory` that tracks whether the linear memory buffer is externally owned.

#### Deliverables

- **Deliverable 1:** `isExternalMemory` field added to `M3Memory` struct in `m3_env.h:29-37`
  - Type: `bool`
  - Default: `false` (set during `m3_NewRuntime`)
- **Deliverable 2:** Field initialized to `false` in runtime creation path

#### Acceptance Criteria

- [ ] `M3Memory` struct contains `isExternalMemory` field
- [ ] Field defaults to `false` after `m3_NewRuntime`
- [ ] Existing code compiles without warnings
- [ ] All existing tests pass

#### Out of Scope

- Setting the flag to `true` (Goal 1.2)
- Using the flag in guards (Goal 1.3)

---

<a id="goal-1-2"></a>

### Goal 1.2 – Implement `m3_SetMemory` API

**Intent:** Implement the public API function that allows callers to inject an externally-managed linear memory buffer into a wasm3 runtime.

#### Deliverables

- **Deliverable 1:** Function declaration in `wasm3.h`
  - Signature: `uint8_t * m3_SetMemory(IM3Runtime i_runtime, void * i_buffer, uint32_t i_bufferSize, uint32_t i_pageSize)`
- **Deliverable 2:** Function implementation in `m3_env.c`
  - Validates `i_bufferSize >= sizeof(M3MemoryHeader) + i_pageSize`
  - Sets `memory->mallocated = (M3MemoryHeader*)i_buffer`
  - Populates header: `runtime`, `maxStack`, `length`
  - Computes `numPages = (i_bufferSize - sizeof(M3MemoryHeader)) / i_pageSize`
  - Sets `memory->isExternalMemory = true`
  - Returns pointer to data region via `m3MemData(mallocated)`
- **Deliverable 3:** Log entry emitted when `d_m3LogRuntime` is enabled

#### Acceptance Criteria

- [ ] `m3_SetMemory` is declared in `wasm3.h` and callable from C code
- [ ] Returns valid data pointer on success
- [ ] Returns `NULL` (or appropriate error) when buffer too small
- [ ] Header fields (`runtime`, `maxStack`, `length`) are correctly populated
- [ ] `numPages` is correctly computed from buffer size and page size
- [ ] `isExternalMemory` is set to `true`
- [ ] `pageSize` defaults to `d_m3DefaultMemPageSize` (65536) when `i_pageSize` is 0

#### Out of Scope

- Guards for `ResizeMemory` and `Runtime_Release` (Goal 1.3)
- Tests (Goal 1.4)

---

<a id="goal-1-3"></a>

### Goal 1.3 – Guard Existing Memory Functions

**Intent:** Modify `ResizeMemory` and `Runtime_Release` to behave correctly when `isExternalMemory` is `true`.

#### Deliverables

- **Deliverable 1:** `ResizeMemory` guard in `m3_env.c:353`
  - When `isExternalMemory == true`: skip `m3_Realloc`
  - Validate requested page count fits within existing buffer
  - Update `numPages` and `length` accordingly
- **Deliverable 2:** `Runtime_Release` guard in `m3_env.c:230`
  - When `isExternalMemory == true`: skip `m3_Free(mallocated)`
  - Set `mallocated = NULL` to avoid dangling pointer

#### Acceptance Criteria

- [ ] `ResizeMemory` does not call `m3_Realloc` when external memory is active
- [ ] `ResizeMemory` rejects requests that exceed the external buffer size
- [ ] `Runtime_Release` does not call `m3_Free` when external memory is active
- [ ] `Runtime_Release` nullifies `mallocated` after skipping free
- [ ] Internal memory path ( `isExternalMemory == false`) remains unchanged
- [ ] All existing tests pass

#### Out of Scope

- Tests for guards (Goal 1.4)
- Multi-instance scenarios (Milestone 2)

---

<a id="goal-1-4"></a>

### Goal 1.4 – Write Unit Tests

**Intent:** Create comprehensive tests covering all new external memory code paths.

#### Deliverables

- **Deliverable 1:** Test for `m3_SetMemory` basic operation
  - Installs buffer correctly
  - Header fields populated correctly
  - Returns data pointer
- **Deliverable 2:** Test for `m3_LoadModule` after `m3_SetMemory`
  - Data segments copied into external buffer
  - Memory contents match expected state
- **Deliverable 3:** Test for `ResizeMemory` when external
  - Returns error or validates size without realloc
  - Rejects oversized requests
- **Deliverable 4:** Test for `Runtime_Release` when external
  - Does not call `m3_Free` on external buffer
  - Buffer remains valid after runtime release
- **Deliverable 5:** End-to-end rollback test
  - Buffer swap + re-run scenario works
  - State is correctly restored

#### Acceptance Criteria

- [ ] All 5 test scenarios above have corresponding test code
- [ ] Tests compile and run via CMake test infrastructure
- [ ] All new tests pass
- [ ] Tests are in `test/` or `platforms/app/` per project conventions

#### Out of Scope

- Performance/stress testing
- Multi-instance testing (Milestone 2)

---

<a id="goal-1-5"></a>

### Goal 1.5 – Verify Backward Compatibility

**Intent:** Confirm that all existing tests pass unchanged after the external memory feature is implemented.

#### Deliverables

- **Deliverable 1:** Full test suite run
  - Build project via CMake
  - Run all test executables in `test/` and `platforms/app/`
  - Record results
- **Deliverable 2:** Regression report
  - Document any failures (expected: none)
  - Confirm zero regressions

#### Acceptance Criteria

- [ ] Project builds cleanly with no new warnings
- [ ] All existing tests pass
- [ ] No changes to existing test files required
- [ ] Internal memory path (`isExternalMemory == false`) behaves identically to pre-feature state

#### Out of Scope

- New tests for external memory (Goal 1.4)
- Performance regression testing

---

## Non-Functional Guarantees

### Zero Overhead on Hot Path

- The `isExternalMemory` flag is only checked in `ResizeMemory` and `Runtime_Release` — both cold paths
- The VM dispatch loop (`m3_exec.h`) uses `m3MemData(mallocated)` which is allocation-source-agnostic
- No additional branching in compiled wasm code execution

### Backward Compatibility

- `isExternalMemory` defaults to `false` — all existing code takes the same path as before
- `m3_SetMemory` is opt-in — callers must explicitly call it
- No changes to `wasm3.h` function signatures for existing APIs

### Security

- Bounds checking is unchanged — wasm3 enforces page limits and `memoryLimit` regardless of ownership
- Data segments validated against buffer size during `InitDataSegments`
- `M3MemoryHeader.runtime` always set to current runtime by `m3_SetMemory` — prevents stale pointer reuse

---

## External Dependencies

### C Standard Library

- **Purpose:** Memory allocation (`malloc`, `realloc`, `free`), `memcpy`
- **Status:** Active (existing dependency)

### CMake

- **Purpose:** Build system
- **Status:** Active (existing dependency)

---

## Agent Guidelines for This Milestone

When working on tasks in this milestone, anchor them to the **goals** above.

### Project Boundaries

- `isExternalMemory` flag → `m3_env.h` (struct definition)
- `m3_SetMemory` → `wasm3.h` (declaration), `m3_env.c` (implementation)
- Guards → `m3_env.c` ( `ResizeMemory`, `Runtime_Release` )
- Tests → `test/` or `platforms/app/`

### Development Approach

- Implement goals sequentially: 1.1 → 1.2 → 1.3 → 1.4 → 1.5
- Each goal should compile and pass existing tests before moving to the next
- Run `cmake --build` and test suite after each goal

### Rules Compliance

- Always respect project-level coding conventions and style guides
- Check for IDE-specific rules (see `AgenticWorkFlow.md` → IDE-Specific Agent Rules)
- Follow C99 conventions for core library code

---

## Related Documents

- **`milestones.md`** — Authoritative milestone definitions
- **`Design.md`** — Technical architecture specification
- **`AgenticWorkFlow.md`** — How AI agents collaborate on this project
