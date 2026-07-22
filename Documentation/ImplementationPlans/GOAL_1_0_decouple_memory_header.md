# Implementation Plan: Decouple M3MemoryHeader from Linear Memory Buffer

version: 1.0
owner: "wasm3"
repo: "wasm3"

---

## Metadata

- Task Type: `GOAL`
- Task Name: `M3MemoryHeader` Decoupling
- Status: `Draft`
- Owner: `wasm3`
- Last Updated: `2026-07-20`

## Linked Context

- Design: [design.md](../Design.md)
- Workflow: [agenticworkflow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: Prerequisite for Goals 1.2–1.5

## Objective

Eliminate the `M3MemoryHeader` struct that is currently prepended to the linear memory buffer. Move its fields (`runtime`, `maxStack`, `length`) directly into the `M3Memory` struct so the linear memory buffer becomes a pure data blob (relocatable, copyable, snapshot-friendly) with no embedded metadata.

## Problem Summary

`M3MemoryHeader` (defined in `m3_core.h:132-138`) is a 24-byte struct prepended to every linear memory allocation:

```
[mallocated]  →  [M3MemoryHeader (24 bytes)] [wasm data pages...]
                  ^— _mem points here            ^— m3MemData(_mem)
```

This couples the linear memory buffer to the runtime instance in two ways:

1. **`runtime` back-pointer** — prevents the buffer from being moved to a different runtime instance without header fixup
2. **`maxStack` boundary** — a value derived from the runtime's native stack, not from the linear memory

Both are runtime metadata cached in the header for fast access via the `_mem` execution register. The `_mem` register (`M3MemoryHeader*`) is passed to every operation in the VM dispatch loop, making `_mem->runtime`, `_mem->maxStack`, and `_mem->length` single-indirection loads.

Storing these in the buffer means:

- The buffer is not a pure data blob — copying/snapshotting includes the header
- `m3_SetMemory` must fix up the header after every buffer swap
- `ResizeMemory` must repopulate the header after realloc
- External memory callers must leave `sizeof(M3MemoryHeader)` bytes of headroom

## Scope

- In scope: Move `runtime`, `maxStack`, `length` from `M3MemoryHeader` into `M3Memory`
- In scope: Change `_mem` execution register type from `M3MemoryHeader*` to `IM3Memory` (`M3Memory*`) in the execution signature
- In scope: Simplify `m3MemData`, `m3MemInfo`, `m3MemRuntime` macros
- In scope: Eliminate `_mem = memory->mallocated` register reassignment in `MemGrow`
- In scope: Update `ResizeMemory`, `m3_SetMemory`, `Runtime_Release`, and all buffer lifecycle code
- In scope: Update all documentation references
- Out of scope: Changing the public API (`wasm3.h` function signatures)
- Out of scope: Any changes to the execution pipeline beyond the `_mem` type change
- Out of scope: Any behavior changes to existing test outcomes

## Current State

### M3MemoryHeader (`m3_core.h:132-138`)
```c
typedef struct M3MemoryHeader
{
    IM3Runtime      runtime;
    void *          maxStack;
    size_t          length;
}
M3MemoryHeader;
```
This struct is prepended to every linear memory buffer allocation. `mallocated` (`M3MemoryHeader*`) points to it.

### M3Memory (`m3_env.h:29-39`)
```c
typedef struct M3Memory
{
    M3MemoryHeader *        mallocated;
    u32                     numPages;
    u32                     maxPages;
    u32                     pageSize;
    bool                    isExternalMemory;
}
M3Memory;
```

### Execution signature (`m3_exec_defs.h:19`)
```c
# define d_m3BaseOpSig  pc_t _pc, m3stack_t _sp, M3MemoryHeader * _mem, m3reg_t _r0
```

### Helper macros (`m3_exec_defs.h:15-17`)
```c
# define m3MemData(mem)     (u8*)(((M3MemoryHeader*)(mem))+1)
# define m3MemRuntime(mem)  (((M3MemoryHeader*)(mem))->runtime)
# define m3MemInfo(mem)     (&(((M3MemoryHeader*)(mem))->runtime->memory))
```

### Where header is populated
- `ResizeMemory` (`m3_env.c:417-422`): sets `runtime`, `maxStack`, `length` after realloc
- `m3_SetMemory` (`m3_env.c:1262-1265`): casts external buffer to `M3MemoryHeader*`, populates fields

### Where `_mem` is reassigned
- `MemGrow` (`m3_exec.h:723`): `_mem = memory->mallocated;` — needed because realloc may move the buffer

## Target State

### Updated M3Memory (`m3_env.h`)
```c
typedef struct M3Memory
{
    IM3Runtime      runtime;        // moved from M3MemoryHeader
    void *          maxStack;       // moved from M3MemoryHeader
    u8 *            data;           // replaced mallocated+1
    size_t          length;         // moved from M3MemoryHeader (data size in bytes)
    u32             numPages;
    u32             maxPages;
    u32             pageSize;
    bool            isExternalMemory;
}
M3Memory;
```

### M3MemoryHeader removed (`m3_core.h`)
The `M3MemoryHeader` struct is deleted. No struct is prepended to the linear memory buffer.

### Execution signature (`m3_exec_defs.h`)
```c
# define d_m3BaseOpSig  pc_t _pc, m3stack_t _sp, IM3Memory _mem, m3reg_t _r0
```

### Simplified macros (`m3_exec_defs.h`)
```c
# define m3MemData(mem)     ((mem)->data)
# define m3MemRuntime(mem)  ((mem)->runtime)
# define m3MemInfo(mem)     (mem)       // _mem IS the IM3Memory pointer
```

### Buffer layout (new)
```
[runtime->memory.data]  →  [wasm data pages...]       (no header)
[_mem = &runtime->memory]                              (stable pointer)
```

## Assumptions and Constraints

- `IM3Memory` (`M3Memory*`) is already a typedef — no new type needed
- The `_mem` register change (`M3MemoryHeader*` → `IM3Memory`) is a single-point change in `d_m3BaseOpSig`; every op defined via `d_m3Op` uses this macro, so all ops pick up the new type automatically
- `_mem` remains reassignable (it is a local variable in each op), but `MemGrow` will no longer need to reassign it because `&runtime->memory` is stable
- The change is internal only — no public API signatures change
- `M3MemoryHeader` is not part of any public API; `wasm3.h` only exposes `IM3Runtime`

## Files and Areas Likely Affected

| File | Impact |
|------|--------|
| `source/m3_core.h:132-138` | Remove `M3MemoryHeader` struct |
| `source/m3_env.h:29-39` | Rewrite `M3Memory` struct: replace `mallocated` with `data`, add `runtime`, `maxStack`, `length` |
| `source/m3_exec_defs.h:15-19` | Change `_mem` type to `IM3Memory`; simplify `m3MemData`, `m3MemInfo`, `m3MemRuntime` macros |
| `source/m3_env.c:184` (m3_NewRuntime) | Remove `sizeof(M3MemoryHeader)` from initial allocation size? (Currently no initial allocation for linear memory here) |
| `source/m3_env.c:343` (InitMemory) | Update to use `M3Memory.data` instead of `mallocated` |
| `source/m3_env.c:365-429` (ResizeMemory) | Replace `m3_Realloc(mallocated, ...)` with `m3_Realloc(data, ...)` + add header; remove header repopulation |
| `source/m3_env.c:230-242` (Runtime_Release) | Replace `m3_Free(mallocated)` with `m3_Free(data)` |
| `source/m3_env.c:597-599` (m3_LoadModule) | Pass `&runtime->memory` instead of `runtime->memory.mallocated` to `RunCode` |
| `source/m3_env.c:932-934,981-983,1031-1033` | Same `RunCode` call sites |
| `source/m3_env.c:1224-1246` (m3_GetMemory, m3_GetMemorySize) | Use `memory->data` and `memory->length` directly |
| `source/m3_env.c:1258-1276` (m3_SetMemory) | Remove header cast, set `data` pointer directly, compute `length` as buffer size (no `- sizeof(M3MemoryHeader)`) |
| `source/m3_exec.h:723` (MemGrow) | Remove `_mem = memory->mallocated;` — `_mem` is already `&runtime->memory` and is stable |
| `source/m3_exec.h:814` (op_Call) | `_mem->maxStack` works identically with the new type — no code change needed |
| `source/m3_exec.h:635,708` | `m3MemRuntime(_mem)` → `_mem->runtime` works identically |
| All ops using `m3MemData(_mem)` | `_mem->data` replaces `m3MemData(_mem)` — update the macro, not each call site |
| `Documentation/Design.md` | Update buffer layout diagram, struct tables, m3_SetMemory behavior, snapshot workflow |
| `Documentation/goals1.md` | Update Goal 1.2 description (no header size requirement) |
| `Documentation/ImplementationPlans/GOAL_1_2_implement_m3_SetMemory.md` | Update to reflect no-header design |
| `Documentation/ImplementationPlans/GOAL_1_3_guard_memory_functions.md` | Update ResizeMemory and Runtime_Release descriptions |

## Implementation Steps

### Phase 1: Struct Redefinition

1. **Edit `source/m3_env.h`** — Rewrite `M3Memory` struct:
   - Remove `M3MemoryHeader* mallocated`
   - Add `IM3Runtime runtime`, `void* maxStack`, `u8* data`, `size_t length`
   - Keep `numPages`, `maxPages`, `pageSize`, `isExternalMemory`

2. **Edit `source/m3_core.h`** — Remove the `M3MemoryHeader` typedef entirely (lines 132-138)

3. **Edit `source/m3_exec_defs.h`**:
   - Change `d_m3BaseOpSig`: `M3MemoryHeader * _mem` → `IM3Memory _mem`
   - Rewrite `m3MemData(mem)` → `((mem)->data)`
   - Rewrite `m3MemRuntime(mem)` → `((mem)->runtime)`
   - Rewrite `m3MemInfo(mem)` → `(mem)` (no-op cast, or just remove)

### Phase 2: Memory Lifecycle

4. **Edit `source/m3_env.c` — `ResizeMemory`** (line ~365):
   - Replace `m3_Realloc(memory->mallocated, ...)` with `m3_Realloc(memory->data, ...)`
   - Replace header field assignments (`mallocated->runtime`, `mallocated->maxStack`, `mallocated->length`) with direct `memory->field` assignments
   - Remove `memory->mallocated = ...` pointer reassignment (no longer needed)
   - Set `memory->data = reallocated_ptr`
   - `memory->length = numPageBytes`
   - `memory->runtime` and `memory->maxStack` only need setting once (in init), not on every resize

5. **Edit `source/m3_env.c` — `InitMemory`** (line ~343):
   - Initialize `memory->runtime`, `memory->maxStack`, `memory->data`, `memory->length`

6. **Edit `source/m3_env.c` — `Runtime_Release`** (line ~230):
   - Replace `m3_Free(mallocated)` → `m3_Free(runtime->memory.data)` (when not external)
   - No header to nullify — just set `data = NULL`

7. **Edit `source/m3_env.c` — `m3_SetMemory`** (line ~1258):
   - Remove cast to `M3MemoryHeader*`
   - Set `memory->data = i_buffer` directly
   - `memory->length = i_bufferSize` (no `- sizeof(M3MemoryHeader)`)
   - Compute `numPages = i_bufferSize / i_pageSize` (no header adjustment)
   - Set `memory->runtime = i_runtime`, `memory->maxStack = ...`, `memory->isExternalMemory = true`
   - Return `memory->data`

8. **Edit `source/m3_env.c` — all `RunCode` call sites** (lines 597, 599, 932, 934, 981, 983, 1031, 1033):
   - Change `runtime->memory.mallocated` → `&runtime->memory` as the `_mem` argument

### Phase 3: Execution Engine

9. **Edit `source/m3_exec.h` — `MemGrow`** (line ~723):
   - Remove `_mem = memory->mallocated;` — `_mem` now points to `&runtime->memory` which is stable

10. **Audit `m3_exec.h`** for any remaining direct `M3MemoryHeader*` usage:
    - `m3MemInfo(_mem)` calls: now trivially return `_mem` — no change needed at call sites
    - `m3MemRuntime(_mem)` calls: now `_mem->runtime` — macro handles this
    - `m3MemData(_mem)` calls: now `_mem->data` — macro handles this
    - Any `_mem->length` accesses: unchanged
    - Any direct `(M3MemoryHeader*)` casts: flag and update

11. **Verify `m3_GetMemory` / `m3_GetMemorySize`** (lines ~1224-1246):
    - Update to use `memory->data` and `memory->length` instead of `memory->mallocated->length`

### Phase 4: Documentation

12. **Edit `Documentation/Design.md`**:
    - Update buffer layout diagram to show no header
    - Update `M3Memory` struct table
    - Remove `M3MemoryHeader` section, fold fields into `M3Memory`
    - Update `m3_SetMemory` description: remove `sizeof(M3MemoryHeader)` from validation
    - Update snapshot workflow: no header to copy

13. **Edit `Documentation/goals1.md`** — Goal 1.2:
    - Update acceptance criteria: no `sizeof(M3MemoryHeader)` requirement
    - Update deliverables: header population step removed

## Verification Plan

### Automated Checks

- `cmake --build build` — project must compile without errors or warnings
- All existing test suites pass (spec tests, WASI tests)
- Both internal and external memory paths produce identical results

### Manual Checks

1. Verify no `M3MemoryHeader` references remain in `source/` (grep for the type name)
2. Verify `m3MemData`, `m3MemInfo`, `m3MemRuntime` macros produce correct values
3. Verify `MemGrow` works without `_mem` reassignment (run a wasm program that grows memory)
4. Verify `m3_SetMemory` accepts a buffer with no header headroom
5. Verify snapshot/restore workflow: copy `data` only, set via `m3_SetMemory`, verify correct execution

## Risks and Open Questions

- **Risk:** Any code outside `source/` (platform apps, tests) that directly references `M3MemoryHeader` or accesses `mallocated` will break. Grep the entire repo for `M3MemoryHeader`, `mallocated`, and `m3MemData` to catch all references.
- **Risk:** The `sizeof(M3MemoryHeader)` constant is embedded in external memory buffer size calculations in various places (m3_SetMemory validation, test scripts, CLI). These must all be updated.
- **Question:** Should `IM3Memory` remain `M3Memory*`, or should we introduce a new lightweight struct (e.g., `M3MemoryView`) that `_mem` points to? Using `M3Memory*` is simpler but means `_mem` carries fields like `numPages`, `maxPages`, `pageSize`, `isExternalMemory` that the execution engine doesn't need. This is harmless but slightly wasteful in the struct footprint. For now, use `IM3Memory` directly.
- **Dependency:** This change should be completed before any Goals 1.2–1.5 implementation to avoid rework.

## Completion Checklist

- [ ] Implementation matches the linked design and goal context
- [ ] Scope stayed within this plan
- [ ] Verification steps were completed or explicitly deferred
- [ ] Relevant status docs were updated
- [ ] A handover document was created if the work stopped mid-phase

## Notes for the Implementing Agent

1. **Priority order:** Phase 1 → Phase 2 → Phase 3 → Phase 4. Each phase should compile before moving to the next.
2. After Phase 1, the project will not compile (structs changed but call sites not updated). This is expected.
3. After Phase 2, the project should compile and link, and all non-execution code paths will be correct.
4. After Phase 3, the full project should compile and all tests should pass.
5. Use `git grep -n 'M3MemoryHeader\|mallocated\|m3MemData\|m3MemInfo\|m3MemRuntime'` to find all references before starting.
