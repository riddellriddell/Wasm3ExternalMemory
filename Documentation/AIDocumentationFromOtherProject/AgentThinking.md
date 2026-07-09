# Agent Thinking

version: 1.0    
owner: "Jack Riddell"    
repo: "WasmTestBedMK1"    

---

This file is an optional scratchpad for temporary agent notes during a long or multi-phase task.

## Usage Rules

- Use it only when explicitly instructed or when a task genuinely needs temporary working memory.
- Keep notes brief, factual, and tied to the current task.
- Do not treat this file as an authoritative specification.
- Reset or replace its contents when switching to a different goal, bug, or feature.
- Avoid committing sensitive data, secrets, or irrelevant chat residue.

---

## Current Notes

### Test Suite Crash Debugging — Handover for Fresh Agent

#### What Was Accomplished

1. **Fixed MSVC standard library header issue**: Root cause was missing `INCLUDE`/`LIB` env vars (CMake run outside VS dev shell). Using `Build.bat` (which calls `VsDevCmd.bat`) resolves it.

2. **Fixed WAMR compilation errors**:
   - `WamrScriptRunnerFactory.h:43`: Changed `Alloc_Default` → `Alloc_With_System_Allocator` (non-existent enum value)
   - `WamrScriptRunner.h:143`: Removed `const` from `reinterpret_cast<uint8_t*>` for `wasm_runtime_load()` call
   - Added `COMPILING_WASM_RUNTIME_API` compile definition to both `WasmRunInterface` and `test_main` targets to fix `__imp_` linker errors

3. **Fixed `ScriptRunnerFactory::~ScriptRunnerFactory()` throw-vs-reset ordering** (`ScriptRunnerFactory.h:68-76`):
   - Moved `s_instanceExists = false;` to execute **before** the throw check, so the static flag is always cleared — even when the destructor throws due to outstanding runners.
   - **This was not sufficient to fix the full suite crash.**

#### Current State

- **Build succeeds**: Both `WasmRunInterface.exe` and `test_main.exe` compile and link with zero errors for both WASM3 and WAMR configurations.
- **Individual test groups pass**: `[WasmBuildTool]`, `[catch2_integration]`, `[mock_runner]` all pass when run in isolation from `build/WasmRunInterface/`.
- **`[factory]` tests crash** with exit code 3 → std::abort() / Windows "abort() has been called" dialog. No console output at all.
- **Full suite (`.\test_main.exe` with no filter)** also crashes the same way — exit code 3, no output.

#### Root Cause Investigation Status

**Confirmed NOT the root cause** (already fixed, but crash persists):
- `s_instanceExists` flag getting stuck by `REQUIRE_THROWS_AS` tests was a real issue, but fixing it didn't resolve the crash.

**Still unknown**. Hypotheses for fresh agent to test:

1. **Exception escaping during stack unwinding (double-exception → std::terminate)**:
   - `~ScriptRunnerFactory()` is `noexcept(false)`, but the mock factory destructors or runner destructors called during test cleanup might be `noexcept(true)` (implicit).
   - If the factory destructor throws while another exception is in flight, or if a runner destructor throws during factory destruction, `std::terminate` is called.
   - Look at `~MockScriptRunnerFactory()` and `~MockScriptRunner()` — are they `noexcept(false)`? Do they call `Return()` in their destructors?

2. **Catch2 test ordering / global fixture issue**:
   - Catch2 may reorder tests across translation units. The `[factory]` tests might be running in an order that triggers the crash.
   - Try running with `--order rand` to see if the crash is consistent or flaky.

3. **Static initialization order fiasco**:
   - `ScriptRunnerFactory<Impl, RunnerType>::s_instanceExists` is a template static. If tests from different translation units are shuffled, the static might not be initialized before first use.

4. **Catch2 `TEST_CASE` name collision across translation units**:
   - Both `TestWasm3ScriptRunner.cpp` and `TestWamrScriptRunner.cpp` define `TEST_CASE("Factory Enforcement Tests", "[factory]")` with identical names. Catch2 merges duplicate names — this might cause undefined behavior or state corruption.
   - **Most promising lead**: Check if both files have identically named `TEST_CASE` blocks. If so, rename them to be distinct.

#### Files Changed

| File | Change |
|------|--------|
| `WasmRunInterface/CMakeLists.txt` | Added `COMPILING_WASM_RUNTIME_API` to both `WasmRunInterface` and `test_main` compile definitions |
| `WasmRunInterface/include/WamrScriptRunnerFactory.h` | `Alloc_Default` → `Alloc_With_System_Allocator` |
| `WasmRunInterface/include/WamrScriptRunner.h` | Removed `const` from `reinterpret_cast` |
| `WasmRunInterface/include/ScriptRunnerFactory.h` | Moved `s_instanceExists = false` before throw in destructor |

#### How to Build & Run Tests

```powershell
# From repo root, open in VS dev shell first:
# Or use Build.bat which handles that:
.\Build.bat msvc fresh

# Run tests from build output dir:
cd build/WasmRunInterface
.\test_main.exe                          # Full suite (crashes)
.\test_main.exe "[factory]"             # Factory tests (crashes)
.\test_main.exe "[WasmBuildTool]"       # Passes
.\test_main.exe "[mock_runner]"         # Passes
```

#### Next Steps for Fresh Agent

1. **Check for duplicate `TEST_CASE` names** across `TestWasm3ScriptRunner.cpp` and `TestWamrScriptRunner.cpp` — both likely define `"Factory Enforcement Tests"`. If so, make them unique (e.g., add ` - Wasm3` / ` - WAMR` suffix).
2. If that doesn't fix it, instrument the factory destructor with a `__try/__except` or use `set_terminate` handler to catch and print the exception before abort.
3. Consider making `~ScriptRunnerFactory()` **never throw** — log the error and clear state instead. This avoids `std::terminate` entirely.
4. Once crash is fixed, run full suite and verify all tests pass.

#### Critical Context

- The `[script_runner]` and `[factory]` groups cause the abort even when run **separately** (not just in combination with other groups).
- The abort dialog suggests `std::terminate` (exception escaping a `noexcept` context, or double-exception during stack unwinding).
- `~ScriptRunnerFactory()` is `noexcept(false)` — but the caller during stack unwinding might not be.

---

## Previous Notes

### GOAL_2_0 WAMR Build System Integration - Implementation Attempt

[... archived — see file content prior to this handover for full GOAL_2_0 notes ...]

### GOAL_1_1 Implementation Plan Critique
[... archived ...]
