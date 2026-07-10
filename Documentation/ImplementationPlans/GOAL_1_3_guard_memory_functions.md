# Implementation Plan: Guard Existing Memory Functions

version: 1.0    
owner: "wasm3"    
repo: "wasm3"

---

## Metadata

- Task Type: `GOAL`
- Task Name: Guard Existing Memory Functions for External Memory
- Status: `Draft`
- Owner: `wasm3`
- Last Updated: `2026-07-11`

## Linked Context

- Design: [Design.md](../Design.md)
- Workflow: [AgenticWorkFlow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: [Goal 1.3 — Guard Existing Memory Functions](../goals1.md#goal-1-3)
- Prerequisite: Goal 1.2 (`m3_SetMemory` API) must be complete

## Objective

Modify `ResizeMemory` and `Runtime_Release` in `m3_env.c` to behave correctly when `isExternalMemory` is `true`, ensuring wasm3 does not attempt to free or reallocate externally-owned memory buffers.

## Problem Summary

`ResizeMemory` unconditionally calls `m3_Realloc` to grow or allocate the linear memory buffer. `Runtime_Release` unconditionally calls `m3_Free` on the buffer. When external memory is injected via `m3_SetMemory`, the caller owns the buffer lifetime — wasm3 must not free or reallocate it. Without these guards, calling `m3_Free` on a caller-owned buffer causes undefined behavior, and calling `m3_Realloc` on external memory would either crash or corrupt the caller's buffer.

## Scope

- In scope: Guard logic in `ResizeMemory` (line ~353) for external memory
- In scope: Guard logic in `Runtime_Release` (line ~230) for external memory
- Out of scope: `m3_SetMemory` implementation (Goal 1.2)
- Out of scope: Tests for these guards (Goal 1.4)
- Out of scope: Any changes to the VM execution path or compilation layer

## Current State

`M3Memory` struct in `m3_env.h:29-39` already contains the `isExternalMemory` boolean field (added in Goal 1.1). The field defaults to `false`.

`ResizeMemory` (`m3_env.c:353-411`):
- Calls `m3_Realloc` to allocate or grow the buffer
- Updates `numPages`, `mallocated->length`, `mallocated->runtime`, `mallocated->maxStack`
- No awareness of external memory

`Runtime_Release` (`m3_env.c:230-239`):
- Calls `m3_Free(i_runtime->memory.mallocated)` unconditionally
- No awareness of external memory

`m3_SetMemory` (Goal 1.2 prerequisite):
- Must be implemented before this goal
- Sets `memory->isExternalMemory = true` when an external buffer is installed

## Assumptions and Constraints

- Goal 1.2 (`m3_SetMemory`) is complete and sets `isExternalMemory = true` when appropriate
- The `M3MemoryHeader` struct fields (`runtime`, `maxStack`, `length`) are already defined in `m3_core.h:132-138`
- The `m3MemData` macro in `m3_exec_defs.h:15` is allocation-source-agnostic and needs no changes
- `ResizeMemory` is called during `m3_LoadModule` → `InitMemory` when the module specifies initial memory pages — this must still work for external memory (updating page count and header fields without realloc)
- C99 standard applies; `bool` is available via `<stdbool.h>`

## Files and Areas Likely Affected

- `source/m3_env.c:353-411` (`ResizeMemory`) — Add early return / guard when `isExternalMemory` is true; validate requested pages fit in existing buffer
- `source/m3_env.c:230-239` (`Runtime_Release`) — Skip `m3_Free(mallocated)` when `isExternalMemory` is true; null out pointer

## Implementation Steps

### Step 1: Guard `Runtime_Release` (m3_env.c:230-239)

Modify the function to skip freeing external memory:

```c
void  Runtime_Release  (IM3Runtime i_runtime)
{
    ForEachModule (i_runtime, _FreeModule, NULL);                   d_m3Assert (i_runtime->numActiveCodePages == 0);

    Environment_ReleaseCodePages (i_runtime->environment, i_runtime->pagesOpen);
    Environment_ReleaseCodePages (i_runtime->environment, i_runtime->pagesFull);

    m3_Free (i_runtime->originStack);

    if (i_runtime->memory.isExternalMemory)
    {
        i_runtime->memory.mallocated = NULL;
    }
    else
    {
        m3_Free (i_runtime->memory.mallocated);
    }
}
```

**Rationale:** When the buffer is externally owned, we null out the pointer to avoid a dangling pointer but must not call `m3_Free`. The `originStack` free is unchanged — it is always wasm3-allocated.

### Step 2: Guard `ResizeMemory` (m3_env.c:353-411)

Insert a guard after the `memory` pointer is obtained. When `isExternalMemory` is true, skip `m3_Realloc` and instead validate the requested page count fits in the existing buffer:

```c
M3Result  ResizeMemory  (IM3Runtime io_runtime, u32 i_numPages)
{
    M3Result result = m3Err_none;

    u32 numPagesToAlloc = i_numPages;

    M3Memory * memory = & io_runtime->memory;

    if (memory->isExternalMemory)
    {
        if (numPagesToAlloc <= memory->maxPages)
        {
            size_t numPageBytes = numPagesToAlloc * io_runtime->memory.pageSize;
            size_t existingBytes = memory->numPages * io_runtime->memory.pageSize;

            _throwif("external memory buffer too small for requested pages", numPageBytes > existingBytes);

            memory->numPages = numPagesToAlloc;
            memory->mallocated->length = numPageBytes;
            memory->mallocated->runtime = io_runtime;
            memory->mallocated->maxStack = (m3slot_t *) io_runtime->stack + io_runtime->numStackSlots;
        }
        else result = m3Err_wasmMemoryOverflow;

        _catch: return result;
    }

    // ... existing internal memory path unchanged ...
}
```

**Rationale:** The guard validates that the requested page count fits within the existing external buffer. If the module requests fewer pages than were allocated, `numPages` and `length` are updated to reflect the active region. The header fields (`runtime`, `maxStack`) are refreshed to ensure they point to the current runtime instance (important for rollback scenarios where a snapshot's header had a stale `runtime` pointer). The `_throwif` macro is already used elsewhere in this function for error handling.

### Step 3: Verify internal memory path is unchanged

Confirm the existing `ResizeMemory` code path (lines 361-411 in the current file) is completely untouched after the guard insertion. The guard is an early return that only fires when `isExternalMemory == true` — the internal path remains identical.

## Verification Plan

### Automated Checks

- `cmake --build build` — project compiles with no new warnings
- `cd test && python3 run-spec-test.py` — all 17863+ spec tests pass (no regressions)
- `cd test && python3 run-wasi-test.py` — all WASI tests pass (no regressions)

### Manual Checks

1. Confirm `ResizeMemory` early-returns when `isExternalMemory` is true without calling `m3_Realloc`
2. Confirm `Runtime_Release` nullifies `mallocated` and skips `m3_Free` when `isExternalMemory` is true
3. Confirm the internal memory path (default runtime with no `m3_SetMemory` call) is completely unchanged

## Risks and Open Questions

- Risk: If Goal 1.2 (`m3_SetMemory`) is not yet implemented, these guards cannot be functionally tested. The code changes are safe to make but untestable without the preceding goal.
- Question: Should `ResizeMemory` also validate that `numPageBytes` is strictly less than the buffer's allocated capacity (not equal)? The current design spec says "fits within existing buffer" — using `>` (not `>=`) in the check means equality is allowed, which is correct.
- Dependency: Requires `isExternalMemory` field from Goal 1.1 and `m3_SetMemory` from Goal 1.2

## Completion Checklist

- [ ] `Runtime_Release` skips `m3_Free` when `isExternalMemory == true`
- [ ] `Runtime_Release` nullifies `mallocated` when `isExternalMemory == true`
- [ ] `ResizeMemory` skips `m3_Realloc` when `isExternalMemory == true`
- [ ] `ResizeMemory` validates requested pages fit within external buffer
- [ ] `ResizeMemory` updates `numPages` and `length` correctly for external memory
- [ ] Internal memory path (`isExternalMemory == false`) is completely unchanged
- [ ] All existing tests pass (spec + WASI)
- [ ] Implementation matches the design in [Design.md](../Design.md) and goal spec in [goals1.md](../goals1.md)

## Notes for the Implementing Agent

- Read the current `ResizeMemory` function fully before editing — understand the existing control flow and error handling (`_throwif`, `_catch`)
- The `_throwif` macro pattern is used elsewhere in `ResizeMemory` — follow the same convention
- Do not modify any code outside the two functions (`ResizeMemory` and `Runtime_Release`)
- After making changes, build and run the full test suite to confirm zero regressions
- If tests fail, the guard logic is the first thing to inspect — check that the external path does not alter the internal path's control flow
