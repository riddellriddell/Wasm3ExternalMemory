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
| Goal 1.4 – Add `--external-mem` CLI Argument | Not Started | [Jump to details](#goal-1-4) |
| Goal 1.5 – Dual-Pass Test Execution | Not Started | [Jump to details](#goal-1-5) |

**Milestone Status:** Not Started — 0/5 goals complete.

### Milestone 1 Scope

**Intent:** Ship a public `m3_SetMemory` API that lets callers provide externally-owned linear memory buffers to wasm3, with proper lifecycle management, a CLI flag for exercising the feature, and dual-pass test coverage.

**What this milestone means:**

- wasm3 can accept caller-provided memory buffers via a new public API
- Externally-provided buffers are not freed or reallocated by wasm3
- The existing internal memory path remains unchanged and fully functional
- The `wasm3` CLI app supports `--external-mem <size>` to exercise the external memory path
- The Python test suites run two passes (internal + external memory) to verify correctness

**Key deliverables:**

- `isExternalMemory` flag in `M3Memory` struct
- `m3_SetMemory` function declared in `wasm3.h` and implemented in `m3_env.c`
- Guards in `ResizeMemory` and `Runtime_Release` for external memory
- `--external-mem <size>` CLI argument in `platforms/app/main.c`
- Dual-pass execution in `test/run-spec-test.py` and `test/run-wasi-test.py`
- All tests pass in both internal and external memory modes

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

- [x] `M3Memory` struct contains `isExternalMemory` field
- [x] Field defaults to `false` after `m3_NewRuntime`
- [x] Existing code compiles without warnings
- [x] All existing tests pass

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
- CLI and test integration (Goals 1.4, 1.5)

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

- CLI and test integration (Goals 1.4, 1.5)
- Multi-instance scenarios (Milestone 2)

---

<a id="goal-1-4"></a>

### Goal 1.4 – Add `--external-mem` CLI Argument

**Intent:** Add a `--external-mem <size>` command-line argument to the wasm3 app (`platforms/app/main.c`) that allocates an external memory buffer of the specified size and injects it into the runtime via `m3_SetMemory`, exercising the external memory path from Goal 1.2.

#### Deliverables

- **Deliverable 1:** `--external-mem <size>` argument parsed in `main.c` arg loop
- **Deliverable 2:** `repl_init` modified to accept `externalMemSize` parameter, call `malloc` + `m3_SetMemory` when non-zero
- **Deliverable 3:** `externalMemBuf` static variable tracked and freed in `repl_free`
- **Deliverable 4:** `print_usage` updated with new flag description
- **Deliverable 5:** All existing `repl_init` call sites updated

#### Acceptance Criteria

- [ ] `wasm3 --external-mem 1048576 file.wasm` runs without error
- [ ] `wasm3 --external-mem 1048576 --repl file.wasm` enters REPL with external memory active
- [ ] Buffer is allocated via `malloc` and freed on exit (no leaks)
- [ ] `m3_SetMemory` receives correct buffer size and returns valid data pointer
- [ ] Module load (`repl_load`) succeeds after external memory injection
- [ ] Wasm execution produces correct results with external memory
- [ ] Without `--external-mem`, behavior is identical to current (no regressions)
- [ ] `print_usage` shows the new flag

#### Out of Scope

- Python test integration (Goal 1.5)
- Multi-instance scenarios (Milestone 2)

> **Implementation details:** See [GOAL_1_4_add_external_mem_cli_arg.md](ImplementationPlans/GOAL_1_4_add_external_mem_cli_arg.md)

---

<a id="goal-1-5"></a>

### Goal 1.5 – Dual-Pass Test Execution

**Intent:** Modify the Python test scripts (`test/run-spec-test.py` and `test/run-wasi-test.py`) to support running each test suite in two modes: once with internal memory (baseline) and once with external memory (via `--external-mem`). Both passes must produce identical results, verifying functional equivalence.

#### Deliverables

- **Deliverable 1:** `--external-mem <size>` argument added to `run-spec-test.py`
- **Deliverable 2:** `--external-mem <size>` argument added to `run-wasi-test.py`
- **Deliverable 3:** `--dual-pass` flag added to both scripts
- **Deliverable 4:** Both scripts correctly inject `--external-mem` into the wasm3 command
- **Deliverable 5:** Dual-pass mode compares results and fails on mismatch

#### Acceptance Criteria

- [ ] `run-spec-test.py --external-mem 1048576` runs all spec tests with external memory
- [ ] `run-spec-test.py --dual-pass` runs two passes and reports matching results
- [ ] `run-wasi-test.py --external-mem 1048576` runs all WASI tests with external memory
- [ ] `run-wasi-test.py --dual-pass` runs two passes and reports matching results
- [ ] Without `--external-mem` or `--dual-pass`, scripts behave identically to current
- [ ] A failure in either pass is reported with clear diagnostic output

#### Out of Scope

- Adding new test cases (tests are the existing spec + WASI suites)
- Modifying the wasm3 binary beyond what Goal 1.4 provides

> **Implementation details:** See [GOAL_1_5_dual_pass_test_execution.md](ImplementationPlans/GOAL_1_5_dual_pass_test_execution.md)

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

### Python 3

- **Purpose:** Test runner scripts (`run-spec-test.py`, `run-wasi-test.py`)
- **Status:** Active (existing dependency, used for dual-pass testing in Goal 1.5)

---

## Agent Guidelines for This Milestone

When working on tasks in this milestone, anchor them to the **goals** above.

### Project Boundaries

- `isExternalMemory` flag → `m3_env.h` (struct definition)
- `m3_SetMemory` → `wasm3.h` (declaration), `m3_env.c` (implementation)
- Guards → `m3_env.c` ( `ResizeMemory`, `Runtime_Release` )
- `--external-mem` CLI arg → `platforms/app/main.c` (arg parsing, `repl_init`, `repl_free`)
- Python test dual-pass → `test/run-spec-test.py`, `test/run-wasi-test.py`

### Development Approach

- Implement goals sequentially: 1.1 → 1.2 → 1.3 → 1.4 → 1.5
- Each goal should compile and pass existing tests before moving to the next
- Run `cmake --build` and test suite after each goal
- Goal 1.4 must be complete before Goal 1.5 can be tested

### Rules Compliance

- Always respect project-level coding conventions and style guides
- Check for IDE-specific rules (see `AgenticWorkFlow.md` → IDE-Specific Agent Rules)
- Follow C99 conventions for core library code

---

## Related Documents

- **`milestones.md`** — Authoritative milestone definitions
- **`Design.md`** — Technical architecture specification
- **`AgenticWorkFlow.md`** — How AI agents collaborate on this project
