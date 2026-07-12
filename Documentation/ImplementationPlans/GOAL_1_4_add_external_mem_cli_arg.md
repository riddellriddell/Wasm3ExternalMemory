# Implementation Plan: Add `--external-mem` CLI Argument

version: 1.0    
owner: "wasm3"    
repo: "wasm3"

---

## Metadata

- Task Type: `GOAL`
- Task Name: Add `--external-mem` CLI Argument to wasm3 App
- Status: `Draft`
- Owner: `wasm3`
- Last Updated: `2026-07-12`

## Linked Context

- Design: [Design.md](../Design.md)
- Workflow: [AgenticWorkFlow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: [Goal 1.4 — Add `--external-mem` CLI Argument](../goals1.md#goal-1-4)
- Prerequisite: Goals 1.1, 1.2, and 1.3 must be complete

## Objective

Add a `--external-mem <size>` command-line argument to the wasm3 app (`platforms/app/main.c`) that allocates an external memory buffer of the specified size and injects it into the runtime via `m3_SetMemory`, exercising the external memory path from Goal 1.2.

## Problem Summary

Goals 1.1–1.3 introduced external memory injection support (`isExternalMemory` flag, `m3_SetMemory` API, and guards in `ResizeMemory`/`Runtime_Release`) but no CLI mechanism exists to exercise this path. Without a way to run wasm3 with external memory, there is no way to verify the feature works end-to-end or to run existing test suites through the external memory path. A CLI flag enables both manual verification and automated dual-pass testing (Goal 1.5).

## Scope

- In scope: `--external-mem <size>` argument parsing in `main.c`
- In scope: `repl_init` modification to accept external memory size and call `m3_SetMemory`
- In scope: `externalMemBuf` static variable tracked and freed in `repl_free`
- In scope: `print_usage` update
- Out of scope: Python test integration (Goal 1.5)
- Out of scope: Changes to the wasm3 core library code
- Out of scope: Multi-instance scenarios (Milestone 2)

## Current State

**Runtime setup flow** (`platforms/app/main.c`):

The wasm3 app sets up the runtime in two modes, both routed through `repl_init`:

**Non-REPL mode** (line 623-649):

```
repl_init(argStackSize)      // creates runtime via m3_NewRuntime
  ↓
[external mem injection]     // INSERT POINT — after runtime exists, before module load
  ↓
repl_load(argFile)           // m3_ParseModule + m3_LoadModule (InitDataSegments copies data)
  ↓
repl_call(argFunc, ...)      // executes wasm
```

**REPL mode** (line 652-706):

```
:init   → repl_init(argStackSize)
          [external mem injection]   // INSERT POINT
:load   → repl_load(argv[1])
...     → repl_call / repl_invoke
```

Both paths converge on `repl_init` (line 471-479), which calls `repl_free()` then `m3_NewRuntime()`. The `m3_SetMemory` call must happen **after** `m3_NewRuntime` returns (runtime exists) and **before** `m3_LoadModule` is called (data segments need a buffer to copy into).

**Existing `repl_init`** (line 471-479):

```c
M3Result repl_init (unsigned stack)
{
    repl_free();
    runtime = m3_NewRuntime (env, stack, NULL);
    if (runtime == NULL) {
        return "m3_NewRuntime failed";
    }
    return m3Err_none;
}
```

**Existing `repl_free`** (line 458-469):

```c
void repl_free ()
{
    if (runtime) {
        m3_FreeRuntime (runtime);
        runtime = NULL;
    }
    for (int i = 0; i < wasm_bins_qty; i++) {
        free (wasm_bins[i]);
        wasm_bins[i] = NULL;
    }
}
```

**Arg parsing pattern** (line 559-611): Uses `ARGV_SHIFT()` / `ARGV_SET()` macros with `strcmp` chain.

## Assumptions and Constraints

- Goals 1.1–1.3 are complete: `isExternalMemory` flag exists, `m3_SetMemory` is implemented, guards are in `ResizeMemory` and `Runtime_Release`
- `m3_SetMemory` signature: `uint8_t * m3_SetMemory(IM3Runtime i_runtime, void * i_buffer, uint32_t i_bufferSize, uint32_t i_pageSize)`
- Passing `0` for `i_pageSize` defaults to `d_m3DefaultMemPageSize` (65536)
- The wasm3 app already includes `m3_env.h` (line 26: `#include "m3_env.h"`)
- C99 standard applies

## Files and Areas Likely Affected

- `platforms/app/main.c` — arg parsing, `repl_init`, `repl_free`, `print_usage`

## Implementation Steps

### Step 1: Add static tracking variable

Add alongside existing static variables (after line 43):

```c
static void* externalMemBuf = NULL;
```

### Step 2: Add arg variable

Add alongside existing arg variables (after line 573):

```c
uint32_t argExternalMem = 0;
```

### Step 3: Parse `--external-mem` in arg loop

Insert after the `--stack-size` handler (after line 600):

```c
} else if (!strcmp("--external-mem", arg)) {
    const char* tmp = "0";
    ARGV_SET(tmp);
    argExternalMem = atol(tmp);
}
```

### Step 4: Update `print_usage`

Add to the options list (after line 556):

```c
puts("  --external-mem <size>  external memory size in bytes (uses m3_SetMemory)");
```

### Step 5: Modify `repl_init` signature and body

Change from:

```c
M3Result repl_init (unsigned stack)
{
    repl_free();
    runtime = m3_NewRuntime (env, stack, NULL);
    if (runtime == NULL) {
        return "m3_NewRuntime failed";
    }
    return m3Err_none;
}
```

To:

```c
M3Result repl_init (unsigned stack, uint32_t externalMemSize)
{
    repl_free();
    runtime = m3_NewRuntime (env, stack, NULL);
    if (runtime == NULL) {
        return "m3_NewRuntime failed";
    }

    if (externalMemSize > 0) {
        externalMemBuf = malloc (externalMemSize);
        if (!externalMemBuf) {
            return "failed to allocate external memory";
        }
        uint8_t* data = m3_SetMemory (runtime, externalMemBuf, externalMemSize, 0);
        if (!data) {
            free (externalMemBuf);
            externalMemBuf = NULL;
            return "m3_SetMemory failed";
        }
    }

    return m3Err_none;
}
```

### Step 6: Update `repl_free` to release external buffer

Add before the existing `runtime` cleanup:

```c
void repl_free ()
{
    if (runtime) {
        m3_FreeRuntime (runtime);
        runtime = NULL;
    }
    if (externalMemBuf) {
        free (externalMemBuf);
        externalMemBuf = NULL;
    }
    for (int i = 0; i < wasm_bins_qty; i++) {
        free (wasm_bins[i]);
        wasm_bins[i] = NULL;
    }
}
```

### Step 7: Update all `repl_init` call sites

- `main()` line 623: `repl_init(argStackSize, argExternalMem)`
- REPL `:init` command line 666: `repl_init(argStackSize, 0)` (REPL `:init` resets to default; external mem is only settable at startup via CLI arg)

### Step 8: Build and verify

```sh
mkdir -p build && cd build
cmake -GNinja -DBUILD_WASI=simple -DCMAKE_C_COMPILER=gcc ..
cmake --build .
cd ..

# Test without --external-mem (baseline)
./build/wasm3 test/lang/fib32.wasm 10

# Test with --external-mem
./build/wasm3 --external-mem 1048576 test/lang/fib32.wasm 10

# REPL test
./build/wasm3 --external-mem 1048576 --repl test/lang/fib32.wasm
> :version
> fib 10
```

## Verification Plan

### Automated Checks

- `cmake --build build` — project compiles with no new warnings
- `./build/wasm3 test/lang/fib32.wasm 10` — produces correct result without `--external-mem`
- `./build/wasm3 --external-mem 1048576 test/lang/fib32.wasm 10` — produces correct result with external memory
- `cd test && python3 run-spec-test.py` — all spec tests pass (no regressions)
- `cd test && python3 run-wasi-test.py` — all WASI tests pass (no regressions)

### Manual Checks

1. Confirm `wasm3 --help` shows `--external-mem` in the options list
2. Confirm `wasm3 --external-mem 1048576 --repl test.wasm` enters REPL and can execute functions
3. Confirm `wasm3` without `--external-mem` behaves identically to before the change
4. Confirm no memory leaks by running under valgrind (if available)

## Risks and Open Questions

- Risk: If `m3_SetMemory` fails (returns NULL), the error message is generic. Consider whether more detail (e.g., buffer size vs minimum) is needed.
- Risk: REPL `:init` resets to internal memory (passes `0`). This is intentional — external mem is a startup-only option. If REPL users need to toggle it, that would be a separate feature.
- Question: Should `--external-mem` accept a page count instead of raw bytes? Recommendation: raw bytes is more intuitive for callers and matches the `m3_SetMemory` API which takes `i_bufferSize`.
- Dependency: Requires Goals 1.1, 1.2, and 1.3 to be complete.

## Completion Checklist

- [ ] `--external-mem <size>` argument is parsed in the arg loop
- [ ] `repl_init` accepts `externalMemSize` and calls `m3_SetMemory` when non-zero
- [ ] `externalMemBuf` is tracked as a static and freed in `repl_free`
- [ ] `print_usage` shows the new flag
- [ ] All `repl_init` call sites updated
- [ ] `wasm3 --external-mem 1048576 file.wasm` runs correctly
- [ ] `wasm3 --external-mem 1048576 --repl file.wasm` works in REPL mode
- [ ] Without `--external-mem`, behavior is identical to before
- [ ] All existing tests pass (spec + WASI)
- [ ] Implementation matches the design in [Design.md](../Design.md) and goal spec in [goals1.md](../goals1.md)

## Notes for the Implementing Agent

- Read `platforms/app/main.c` fully before editing — understand the arg parsing pattern (`ARGV_SHIFT`/`ARGV_SET` macros)
- The `repl_init` signature change affects two call sites: `main()` and the REPL `:init` command
- The external buffer is allocated by this code, not by the caller of `m3_SetMemory` — this is different from the Design.md rollback scenario where the caller manages the buffer. Here wasm3's CLI app manages it.
- Do not add explanatory comments unless the logic is non-obvious
- After making changes, build and run the full test suite before declaring done
