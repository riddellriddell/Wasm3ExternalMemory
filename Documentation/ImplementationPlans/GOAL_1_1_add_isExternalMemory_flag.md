# Implementation Plan: Goal 1.1 — Add `isExternalMemory` Flag

version: 1.0
owner: "Your Name"
repo: "your-repo"

---

## Metadata

- Task Type: `GOAL`
- Task Name: Add `isExternalMemory` Flag to M3Memory
- Status: `Complete`
- Owner: "Your Name"
- Last Updated: 2026-07-11

## Linked Context

- Design: [design.md](../Design.md)
- Workflow: [agenticworkflow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: [Goal 1.1 — Add `isExternalMemory` Flag](../goals1.md#goal-1-1)

## Objective

Add a `bool isExternalMemory` field to the `M3Memory` struct that tracks whether the linear memory buffer is externally owned. The field must default to `false` after runtime creation, and the existing code must compile and pass all tests without changes.

## Problem Summary

The `M3Memory` struct currently has no way to distinguish between internally-allocated and externally-provided linear memory buffers. This flag is the prerequisite for all subsequent external memory goals (m3_SetMemory, ResizeMemory guard, Runtime_Release guard). Without it, wasm3 cannot know whether it owns the buffer or the caller does.

## Scope

- In scope: Add `isExternalMemory` field to `M3Memory` struct in `m3_env.h`
- In scope: Ensure field is initialized to `false` in the runtime creation path
- Out of scope: Setting the flag to `true` (Goal 1.2)
- Out of scope: Using the flag in guards (Goal 1.3)
- Out of scope: New API functions or test code

## Current State

**`m3_env.h:29-37`** — Current `M3Memory` struct:
```c
typedef struct M3Memory
{
    M3MemoryHeader *        mallocated;

    u32                     numPages;
    u32                     maxPages;
    u32                     pageSize;
}
M3Memory;
```

**`m3_env.c:173-195`** — `m3_NewRuntime` allocates `M3Runtime` via `m3_AllocStruct(M3Runtime)`. The `M3Memory memory` field is embedded inline at `m3_env.h:183`. The `m3_AllocStruct` macro uses `calloc`, which zero-initializes the entire struct — so any new `bool` field will default to `false` (0) without explicit initialization code.

**`m3_env.c:335-350`** — `InitMemory` sets `numPages`, `maxPages`, and `pageSize` from module info, then calls `ResizeMemory`. It does not touch `isExternalMemory`.

No code currently reads or writes an `isExternalMemory` field. The internal memory path (`ResizeMemory`, `Runtime_Release`) is completely unaffected by adding the field.

## Assumptions and Constraints

- `m3_AllocStruct` zero-initializes via `calloc`, so `isExternalMemory` defaults to `false` (0) without explicit assignment
- The `bool` type is available via `<stdbool.h>` (C99) — verify it is already included in `m3_env.h` or its transitive includes
- Adding a field to `M3Memory` does not change the ABI for the internal memory path since no code reads it yet
- The `M3Memory` struct is embedded inline in `M3Runtime` — adding a field increases `M3Runtime` size by `sizeof(bool)` (typically 1 byte, with possible padding)

## Files and Areas Likely Affected

- `source/m3_env.h` — Add `isExternalMemory` field to `M3Memory` struct (line 37, before closing brace)
- `source/m3_env.c` — No changes needed; `m3_AllocStruct` zero-initializes via `calloc`

## Implementation Steps

1. Open `source/m3_env.h` and locate the `M3Memory` struct at lines 29-37
2. Add `bool isExternalMemory;` as the last field before the closing brace, matching the existing indentation style
3. Verify `<stdbool.h>` is included (directly or transitively) in `m3_env.h` — if not, add the include
4. Build the project via CMake to confirm no warnings or errors
5. Run the full test suite to confirm all existing tests pass

## Verification Plan

### Automated Checks

- `cmake --build` — project compiles with no new warnings
- Full test suite run via CMake — all existing tests pass

### Manual Checks

1. Inspect the `M3Memory` struct in `m3_env.h` to confirm the field is present and correctly typed
2. Confirm no existing code references `isExternalMemory` (grep the codebase) — expected: zero matches outside the new field definition
3. Confirm `sizeof(M3Memory)` increased by at least 1 byte (optional, via a sizeof check)

### Struct Size Impact Audit

Adding a field to `M3Memory` increases its size. Since `M3Memory` is embedded inline in `M3Runtime` (`m3_env.h:183`), this also increases `sizeof(M3Runtime)`. The following checks verify no code is broken by this size change:

**A. Find all allocations of `M3Runtime` and `M3Memory`:**

- Grep for `m3_AllocStruct(M3Runtime)` and `m3_AllocStruct(M3Memory)` — confirm they use the macro (which uses `calloc`/`malloc` with `sizeof`, so they automatically pick up the new size)
- Grep for any hardcoded `sizeof(M3Runtime)`, `sizeof(M3Memory)`, or raw byte counts that assume a specific struct size
- Grep for `calloc` or `malloc` calls that manually compute the size of these structs instead of using `m3_AllocStruct`

**B. Check for fixed-size buffer assumptions:**

- Search for any stack-allocated `M3Memory` or `M3Runtime` variables (e.g., `M3Memory mem;` or `M3Runtime rt;`) — these are fine since the compiler uses the updated `sizeof`, but verify no code takes `&mem` and copies a hardcoded number of bytes
- Search for `memcpy`, `memmove`, or `memset` calls involving `M3Memory` or `M3Runtime` with an explicit byte count — these would break if the count is stale

**C. Check for array or packed-struct assumptions:**

- Grep for any code that computes offsets into `M3Runtime` manually (e.g., pointer arithmetic after the struct base) — the inline `M3Memory memory` field and subsequent `memoryLimit` field at `m3_env.h:183-184` shift in memory; any manual offset calculation would be wrong
- Check for `__attribute__((packed))` or `#pragma pack` around `M3Memory` or `M3Runtime` — packed structs with manual size assumptions are high-risk

**D. Verify no serialization依赖 on struct layout:**

- Grep for any code that serializes/deserializes `M3Memory` or `M3Runtime` to/from a byte buffer (file I/O, network, IPC) — a size change would corrupt the serialization format
- Check for any `offsetof(M3Memory, ...)` usage that would produce a different offset for fields after the insertion point (there are none after the new field since it is last, but verify)

**E. Confirm `M3Runtime` allocation in `m3_NewRuntime`:**

- `m3_env.c:174` — `m3_AllocStruct(M3Runtime)` allocates the full struct. Since it uses `sizeof(M3Runtime)` internally, the allocation automatically includes the new field. No code change needed, but confirm the macro does not cache or hardcode the size.

## Risks and Open Questions

- Risk: `stdbool.h` may not be included in the translation unit — verify transitive includes
- Risk: Struct padding may add more than 1 byte — acceptable, not a concern for this goal
- Question: Should the field be initialized explicitly in `m3_NewRuntime` for clarity, or rely on `calloc` zero-initialization? Recommendation: rely on `calloc` (existing pattern for all other fields)

## Completion Checklist

- [x] `isExternalMemory` field added to `M3Memory` struct in `m3_env.h`
- [x] Field defaults to `false` after `m3_NewRuntime`
- [x] Existing code compiles without warnings
- [x] All existing tests pass
- [x] Implementation matches the linked design and goal context
- [x] Scope stayed within this plan
- [x] Verification steps were completed
- [x] Relevant status docs were updated (goals1.md checkbox)

## Notes for the Implementing Agent

- This is a single-field addition to one struct. The change is intentionally minimal.
- Do not add any logic that reads or writes `isExternalMemory` — that is Goals 1.2 and 1.3.
- Match the existing code style: tab indentation, field names in camelCase, pointer type on the same line as the name.
- After implementation, update the Goal 1.1 acceptance criteria checkboxes in `goals1.md` to reflect completion.
