# Implementation Plan: Goal 1.2 — Implement `m3_SetMemory` API

version: 1.0    
owner: "wasm3"    
repo: "wasm3"

---

## Metadata

- Task Type: `GOAL`
- Task Name: Implement `m3_SetMemory` API
- Status: `Draft`
- Owner: "wasm3"
- Last Updated: 2026-07-11

## Linked Context

- Design: [Design.md](../Design.md)
- Workflow: [AgenticWorkFlow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: [Goal 1.2](../goals1.md#goal-1-2)
- Depends On: Goal 1.1 (`isExternalMemory` flag already added to `M3Memory` in `m3_env.h:37`)

## Objective

Implement the public `m3_SetMemory` function that allows callers to inject an externally-managed linear memory buffer into a wasm3 runtime, returning a pointer to the usable data region.

## Problem Summary

wasm3 currently allocates linear memory internally via `ResizeMemory` → `m3_Realloc`. Callers have no way to provide their own buffer, making snapshot/restore expensive (full re-init required). This goal creates the entry point for external memory injection.

## Scope

- In scope: Declare `m3_SetMemory` in `wasm3.h` and implement it in `m3_env.c`
- In scope: Validate input, populate `M3MemoryHeader`, compute `numPages`, set `isExternalMemory = true`
- In scope: Emit log entry when `d_m3LogRuntime` is enabled
- Out of scope: Guards in `ResizeMemory` and `Runtime_Release` (Goal 1.3)
- Out of scope: Tests (Goal 1.4)

## Current State

- `isExternalMemory` field exists in `M3Memory` struct (`m3_env.h:37`) — added by Goal 1.1
- `M3MemoryHeader` struct in `m3_core.h:132-138` has fields: `runtime`, `maxStack`, `length`
- `m3MemData` macro in `m3_exec_defs.h:15` skips header to return data pointer
- `m3_GetMemory` in `m3_env.c:1206` demonstrates the data pointer return pattern
- `ResizeMemory` in `m3_env.c:353` shows the header population pattern (`runtime`, `maxStack`, `length`)
- `Runtime_Release` in `m3_env.c:230` currently always calls `m3_Free(mallocated)` — no external memory guard yet
- `d_m3DefaultMemPageSize` is 65536 (used in `InitMemory` at `m3_env.c:344`)
- `d_m3LogRuntime` is the existing log toggle for runtime memory operations
- No existing error constant fits "buffer too small" — a new one or an existing general error must be chosen

## Assumptions and Constraints

- Goal 1.1 is complete: `isExternalMemory` field exists and defaults to `false`
- C99 is required for core library code
- Existing public API signatures in `wasm3.h` must not change
- `sizeof(M3MemoryHeader)` is 24 bytes on 64-bit (3 fields: pointer, pointer, size_t)
- The function must be callable before `m3_LoadModule` (callers provide buffer, then load module into it)
- The function can also be called after execution to swap in a snapshot buffer
- The caller is responsible for buffer lifetime — wasm3 never frees external buffers (Goal 1.3 will enforce this)

## Files and Areas Likely Affected

- `source/wasm3.h` — Add function declaration in the "execution context" section (near `m3_GetMemory`)
- `source/m3_env.c` — Add function implementation (place after `m3_GetMemory` / `m3_GetMemorySize` around line 1228)

## Implementation Steps

1. **Add error constant for buffer too small** in `source/wasm3.h` among the runtime errors section (around line 178). Add:
   ```c
   d_m3ErrorConst  (invalidMemorySize,            "external memory buffer is too small")
   ```

2. **Declare `m3_SetMemory` in `source/wasm3.h`** in the "execution context" section, after the `m3_GetMemory` declaration (after line 230). Add:
   ```c
   uint8_t *           m3_SetMemory                (IM3Runtime             i_runtime,
                                                    void *                 i_buffer,
                                                    uint32_t               i_bufferSize,
                                                    uint32_t               i_pageSize);
   ```

3. **Implement `m3_SetMemory` in `source/m3_env.c`** after `m3_GetMemorySize` (after line 1228). The implementation:
   ```c
   uint8_t *  m3_SetMemory  (IM3Runtime i_runtime, void * i_buffer, uint32_t i_bufferSize, uint32_t i_pageSize)
   {
       M3Memory * memory = & i_runtime->memory;

       if (i_pageSize == 0)
           i_pageSize = d_m3DefaultMemPageSize;

       size_t headerSize = sizeof (M3MemoryHeader);
       size_t minSize = headerSize + i_pageSize;

       if (i_bufferSize < minSize)
           return NULL;

       memory->mallocated = (M3MemoryHeader *) i_buffer;
       memory->mallocated->runtime = i_runtime;
       memory->mallocated->maxStack = (m3slot_t *) i_runtime->stack + i_runtime->numStackSlots;
       memory->mallocated->length = i_bufferSize - headerSize;

       memory->numPages = (i_bufferSize - headerSize) / i_pageSize;
       memory->pageSize = i_pageSize;
       memory->isExternalMemory = true;

   # if d_m3LogRuntime
       m3log (runtime, "set external memory: buffer: %p; size: %u; pages: %u", i_buffer, i_bufferSize, memory->numPages);
   # endif

       return m3MemData (memory->mallocated);
   }
   ```

4. **Verify the build compiles** by running the CMake build command.

## Verification Plan

### Automated Checks

- `cmake --build build` — project compiles with no new warnings
- `cmake --build build --target test` or equivalent test runner — all existing tests pass

### Manual Checks

1. Confirm `m3_SetMemory` symbol is visible in the compiled library (e.g., `nm` or linker map)
2. Confirm the function compiles when called from a C file that includes `wasm3.h`
3. Confirm that calling `m3_SetMemory` with a buffer smaller than `sizeof(M3MemoryHeader) + pageSize` returns `NULL`
4. Confirm that calling `m3_SetMemory` with valid buffer returns a non-NULL pointer equal to `(uint8_t*)buffer + sizeof(M3MemoryHeader)`

## Risks and Open Questions

- Risk: `m3slot_t` type used in `maxStack` calculation — must verify it is defined before use in `m3_env.c` (it is, via `m3_exec_defs.h` → `m3_core.h`)
- Question: Should `m3_SetMemory` be callable when a module is already loaded? Design says yes (for rollback), and since Goal 1.3 guards are not yet in place, this is acceptable — the caller takes responsibility.
- Dependency: Goal 1.1 must be complete (it is — `isExternalMemory` field exists at `m3_env.h:37`)

## Completion Checklist

- [ ] `m3_SetMemory` declared in `wasm3.h`
- [ ] `m3_SetMemory` implemented in `m3_env.c`
- [ ] `invalidMemorySize` error constant added to `wasm3.h`
- [ ] Function returns data pointer on success, NULL on insufficient buffer
- [ ] Header fields (`runtime`, `maxStack`, `length`) correctly populated
- [ ] `numPages` computed from buffer size and page size
- [ ] `isExternalMemory` set to `true`
- [ ] `pageSize` defaults to `d_m3DefaultMemPageSize` when `i_pageSize` is 0
- [ ] Log entry emitted when `d_m3LogRuntime` is enabled
- [ ] Build compiles cleanly with no warnings
- [ ] All existing tests pass
- [ ] Scope stayed within this plan (no guard changes to `ResizeMemory`/`Runtime_Release`)

## Notes for the Implementing Agent

- Place the implementation after `m3_GetMemorySize` in `m3_env.c` for consistency with the existing public memory API functions
- Place the declaration after `m3_GetMemory` in `wasm3.h` to group memory-related public APIs together
- Follow the existing code style: 4-space indentation with tabs, `_try`/`_catch` error macros not needed here since this function does not allocate
- The function does NOT use `_try`/`_catch` — it is a simple pointer assignment with no allocation
- Do NOT add guards to `ResizeMemory` or `Runtime_Release` — those belong to Goal 1.3
