# Wasm3 External Memory Injection — Design Specification

version: 1.0    
owner: "Your Name"    
repo: "your-repo"

---

## Purpose of This File

This file defines the architecture, principles, and design decisions for the project.

## Documentation Hierarchy

This file is **Tier 1** of the repository's documentation-first workflow.

| Tier | Document | Purpose |
| --- | --- | --- |
| 1 - Design | `design.md` | Project architecture, principles, and constraints |
| 2 - Milestones | [milestones.md](Milestones.md) | Roadmap structure and milestone summaries |
| 3 - Goals | `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) | Specific deliverables and acceptance criteria |
| 4 - Implementation Details | `ImplementationPlans/*.md` | Task-specific implementation plans and handovers |
| Support | [AgenticWorkFlow.md](AgenticWorkFlow.md) | Workflow for AI agent collaboration |
| Support | [AgentThinking.md](AgentThinking.md) | Optional temporary scratchpad for long tasks |

---

## Executive Summary

This project modifies the wasm3 WebAssembly interpreter to support external memory injection. The wasm linear memory buffer — which holds the state of a running wasm program — can be provided and swapped by the caller instead of being internally allocated by wasm3. This enables rolling back a wasm program's state to an earlier point in time by pointing the runtime at a previously snapshotted memory buffer, without re-initializing the wasm machine.

The long-term goal extends to multi-instance shared memory using memory-mapped files, where multiple wasm3 instances operate on the same underlying physical pages. That work is planned as a separate milestone.

### Core Principles

- **Backward compatibility** — Existing code paths are unchanged; external memory is opt-in via a new API. All current tests must continue to pass.
- **Minimal invasiveness** — Changes are confined to memory ownership tracking and lifecycle management, not VM execution or compilation.
- **Caller owns buffer lifetime** — wasm3 never frees externally-provided buffers. The caller is responsible for allocation and deallocation.

---

## System Architecture

### How the Pieces Fit Together

```
M3Environment (type registry, code page pool)
    ↓
M3Runtime (execution context: stack, compiled code, linear memory)
    ↓
M3Module (parsed wasm binary: functions, data segments, globals, memory info)
```

**Core Components:**

- **M3Environment** — Shared type registry and code page pool. One per application. Manages `M3FuncType` linked list and released code pages.
- **M3Runtime** — Execution context holding the wasm stack, compiled code pages, and wasm linear memory (`M3Memory`). One per wasm execution instance.
- **M3Module** — Parsed wasm module containing functions, data segments, globals, element segments, and memory configuration. Loaded into a runtime via `m3_LoadModule`.
- **M3Memory** — Tracks the linear memory buffer (`mallocated` header pointer), page count, page size, and (new) external memory ownership flag.
- **M3MemoryHeader** — 24-byte struct prepended to the linear memory buffer. Contains the runtime back-pointer, stack boundary, and buffer length.

### External Dependencies

| Dependency | Purpose |
| --- | --- |
| C standard library | Memory allocation (`malloc`, `realloc`, `free`), string operations |
| CMake | Build system |

### Repository Structure

```text
ProjectRoot/
|-- source/                  # Core library source (m3_*.c/h, wasm3.h)
|-- platforms/               # Platform-specific applications
|-- docs/                    # Existing project documentation
|-- Documentation/           # AI workflow and planning docs
|-- test/                    # Tests
|-- CMakeLists.txt
|-- build.zig
```

---

## Memory Architecture

This is the central design area for this project.

### Buffer Layout

The wasm linear memory buffer has a fixed layout:

```
[M3MemoryHeader (24 bytes on 64-bit)] [wasm linear memory data pages...]
^ mallocated                          ^ m3MemData(mallocated)
```

The `m3MemData` macro (`m3_exec_defs.h:15`) skips past the header to return the raw data pointer:

```c
#define m3MemData(mem)  (u8*)(((M3MemoryHeader*)(mem))+1)
```

### M3MemoryHeader Fields

Defined in `m3_core.h:132-138`:

| Field | Type | Purpose |
| --- | --- | --- |
| `runtime` | `IM3Runtime` | Back-pointer to the owning M3Runtime instance |
| `maxStack` | `void*` | Stack boundary for overflow checks during execution |
| `length` | `size_t` | Size of the data pages in bytes (excludes header) |

### M3Memory Struct

Defined in `m3_env.h:29-37`:

| Field | Type | Purpose |
| --- | --- | --- |
| `mallocated` | `M3MemoryHeader*` | Pointer to the start of the buffer (header + data) |
| `numPages` | `u32` | Current number of wasm memory pages |
| `maxPages` | `u32` | Maximum allowed pages |
| `pageSize` | `u32` | Bytes per page (default 65536) |
| `isExternalMemory` | `bool` | **(new)** Whether the buffer is externally owned |

### Current Memory Ownership Model

1. **Allocation**: `ResizeMemory()` (`m3_env.c:353`) calls `m3_Realloc()` on `mallocated` to allocate or grow the buffer. It populates the `M3MemoryHeader` fields.
2. **Data loading**: `InitDataSegments()` (`m3_env.c:456`) `memcpy`s parsed wasm data segments into the buffer at their specified offsets.
3. **Deallocation**: `Runtime_Release()` (`m3_env.c:230`) calls `m3_Free(mallocated)`.

### Proposed External Memory Model

A new public API function `m3_SetMemory` allows the caller to provide an externally-managed buffer:

```c
uint8_t * m3_SetMemory(IM3Runtime i_runtime,
                        void * i_buffer,
                        uint32_t i_bufferSize,
                        uint32_t i_pageSize);
```

**Behavior:**
1. Validates that `i_bufferSize >= sizeof(M3MemoryHeader) + i_pageSize`
2. Sets `memory->mallocated` to `i_buffer`
3. Populates the header: `runtime`, `maxStack`, `length`
4. Computes `numPages` from `(i_bufferSize - sizeof(M3MemoryHeader)) / i_pageSize`
5. Sets `memory->isExternalMemory = true`
6. Returns a pointer to the data region (same as `m3_GetMemory`)

**Guards added to existing functions:**
- `ResizeMemory()`: When `isExternalMemory == true`, skips `m3_Realloc`. Validates that the requested page count fits within the existing buffer. Updates `numPages` and `length`.
- `Runtime_Release()`: When `isExternalMemory == true`, skips `m3_Free(mallocated)`.

### Memory Lifecycle States

| State | Condition | Behavior |
| --- | --- | --- |
| Unallocated | `mallocated == NULL` | After `m3_NewRuntime`, before module load or `m3_SetMemory` |
| Internal | `isExternalMemory == false`, `mallocated != NULL` | Default path; wasm3 owns and manages the buffer |
| External | `isExternalMemory == true`, `mallocated != NULL` | Caller owns the buffer; wasm3 populates header only |

### Rollback Workflow

```
// 1. Initial setup
m3_NewRuntime(env, stackSize, NULL)
m3_SetMemory(runtime, emptyBuf, bufSize, pageSize)
m3_LoadModule(runtime, module)          // copies data segments into emptyBuf

// 2. Snapshot (raw copy of entire buffer including header)
memcpy(snapshot, runtime->memory.mallocated, bufSize)

// 3. Run wasm — modifies memory contents
m3_FindFunction(&func, runtime, "main")
m3_CallV(func)

// 4. Rollback to earlier state
m3_SetMemory(runtime, snapshot, bufSize, pageSize)  // re-fills header, restores data
// ready to run again on restored state
```

The snapshot captures the entire buffer (header + data). On restore, `m3_SetMemory` overwrites the header with the current instance's `runtime` and `maxStack` values. The data pages are preserved as-is.

---

## Processing Pipelines

### Pipeline 1: Module Load and Initialization

**Status:** Implemented (modified for external memory)

```
m3_ParseModule → m3_LoadModule → InitMemory → ResizeMemory → InitDataSegments → InitElements → InitGlobals
```

When external memory is active, `ResizeMemory` skips allocation and validates the existing buffer.

### Pipeline 2: Function Execution

**Status:** Implemented (unchanged)

```
m3_FindFunction → CompileFunction → RunCode (VM dispatch loop using m3MemData)
```

No changes to the execution pipeline. The `m3MemData` macro works identically regardless of buffer allocation source.

### Pipeline 3: Memory Swap

**Status:** New

```
m3_SetMemory(newBuffer) → header populated → ready to run
```

O(1) operation — pointer assignment and header fill. No data copy required because the caller provides a fully-formed buffer.

---

## Application Layers

### Layer 1: Public API

**Purpose:** External-facing interface for wasm3 consumers.

**Architecture:** Declared in `wasm3.h`. Functions prefixed with `m3_`.

**Key Capabilities:**

| Capability | Description | Use Case |
| --- | --- | --- |
| `m3_NewRuntime` | Create execution context | Runtime setup |
| `m3_GetMemory` | Get pointer to wasm linear memory | Read/write wasm memory from host |
| `m3_SetMemory` | **(new)** Inject external memory buffer | State rollback, buffer swap |
| `m3_LoadModule` | Load parsed module into runtime | Module initialization |
| `m3_FindFunction` / `m3_Call*` | Locate and execute wasm functions | Running wasm code |

### Layer 2: Environment

**Purpose:** Runtime and module lifecycle management, memory allocation.

**Architecture:** Implemented in `m3_env.c`. Handles initialization, memory resize, data segment loading, and cleanup.

### Layer 3: Compilation

**Purpose:** Translates wasm bytecode to M3 internal opcodes.

**Architecture:** Implemented in `m3_compile.c`. No changes required for this project.

### Layer 4: Execution

**Purpose:** VM dispatch loop and opcode implementations.

**Architecture:** Implemented in `m3_exec.h` and `m3_exec_defs.h`. Uses `m3MemData` macro for memory access. No changes required — the macro works regardless of how the buffer was allocated.

---

## Dependency Rules

Dependencies are strictly layered:

```
wasm3.h (public API)
    ↓
m3_env.c (lifecycle + memory management)
    ↓
m3_compile.c (wasm → metacode)
    ↓
m3_exec.h (VM execution, uses m3MemData macro)
```

**Rules:**
1. Higher layers depend on lower layers, never the reverse.
2. The execution layer accesses memory only through `m3MemData(mallocated)`, which is allocation-source-agnostic.
3. The public API layer (`wasm3.h`) is the only entry point for external memory injection.

---

## Configuration

### Build Configuration

**Primary:** CMake-based build system

**Compiler Requirements:**
- C99 for core library
- Platform-specific tools as needed

### Runtime Configuration

- `d_m3DefaultMemPageSize` (65536) — default wasm page size, used when `pageSize` argument to `m3_SetMemory` is 0
- `d_m3MaxLinearMemoryPages` (65536) — compile-time limit on maximum pages

---

## Security and Privacy

- External memory buffers are unowned by wasm3. The caller must ensure the buffer's lifetime exceeds the runtime's lifetime. Use after freeing the buffer is undefined behavior.
- Bounds checking is unchanged. wasm3 still enforces page limits and the `memoryLimit` cap regardless of memory ownership.
- Data segments are still validated against buffer size during `InitDataSegments` — out-of-bounds writes are rejected.
- The `M3MemoryHeader.runtime` back-pointer is always set to the current runtime by `m3_SetMemory`, preventing stale pointer reuse.

---

## Observability

### Logging

Runtime memory operations are logged when `d_m3LogRuntime` is enabled. `m3_SetMemory` should emit a log entry with the buffer pointer, size, and page count.

### Debugging

`m3_GetMemory` continues to work identically for external memory. No debug tooling changes required.

---

## Testing Policy

### Core Principle

All features must have corresponding tests. Before any change is considered complete, all tests must pass.

### Test Framework

The project uses test executables in `test/` and `platforms/app/`. Build and run via CMake.

### Required Test Coverage

| Component | Test Requirements |
| --- | --- |
| `m3_SetMemory` | Installs buffer correctly; header fields populated; returns data pointer |
| `m3_LoadModule` after `m3_SetMemory` | Data segments copied into external buffer |
| `ResizeMemory` when external | Returns error or validates size without realloc |
| `Runtime_Release` when external | Does not call `m3_Free` on external buffer |
| Buffer swap + re-run | End-to-end rollback scenario works |
| Existing tests | All current tests continue to pass (backward compatibility) |

### Validation Requirements

Before any change is merged or considered complete:
1. Build the project
2. Run all test executables
3. Verify all tests pass
4. Fix any failing tests before declaring the change complete

---

## Performance

- Zero overhead vs internal memory path — same VM dispatch, same `m3MemData` macro, no additional branching in hot paths.
- `m3_SetMemory` is O(1) — pointer assignment, header fill, flag set. No data copy.
- Buffer swap for rollback is a single `m3_SetMemory` call. The caller's `memcpy` for snapshotting is O(bufferSize) but that is outside wasm3.
- The `isExternalMemory` flag check adds one branch to `ResizeMemory` and `Runtime_Release`, both of which are cold paths (called once during module load and once during teardown).

---

## Future Work

### Multi-Instance Shared Memory (Separate Milestone)

Multiple wasm3 instances sharing the same underlying physical pages via memory-mapped files:

- **Mechanism**: Memory-mapped files (`CreateFileMapping`/`MapViewOfFile` on Windows, `mmap` on POSIX)
- **Layout**: Each instance has its own `M3MemoryHeader` (per-instance state), but the data pages are mapped to the same physical pages
- **Concurrency**: No CoW protection — all instances can write simultaneously. Race conditions handled at the application level.
- **Cross-platform**: Abstract behind a platform abstraction layer with Windows, Linux, macOS, and iOS implementations

---

## Navigation

### Specification Hierarchy

- [design.md](Design.md) - Tier 1 design overview
- [milestones.md](Milestones.md) - Tier 2 roadmap summary
- `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) - Tier 3 goals and deliverables
- `ImplementationPlans/*.md` - Tier 4 execution plans and handovers

### Reference Documents

- [AgenticWorkFlow.md](AgenticWorkFlow.md) - AI collaboration workflow
- [AgentThinking.md](AgentThinking.md) - optional temporary agent scratchpad
