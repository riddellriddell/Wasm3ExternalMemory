# Implementation Plan: Dual-Pass Test Execution

version: 1.0    
owner: "wasm3"    
repo: "wasm3"

---

## Metadata

- Task Type: `GOAL`
- Task Name: Dual-Pass Test Execution for External Memory Verification
- Status: `Draft`
- Owner: `wasm3`
- Last Updated: `2026-07-12`

## Linked Context

- Design: [Design.md](../Design.md)
- Workflow: [AgenticWorkFlow.md](../AgenticWorkFlow.md)
- Milestone: [Milestone 1: External Memory Injection](../Milestones.md#milestone-1)
- Goal: [Goal 1.5 — Dual-Pass Test Execution](../goals1.md#goal-1-5)
- Prerequisite: Goal 1.4 (`--external-mem` CLI argument) must be complete

## Objective

Modify the Python test scripts (`test/run-spec-test.py` and `test/run-wasi-test.py`) to support running each test suite in two modes: once with internal memory (baseline) and once with external memory (via `--external-mem`). Both passes must produce identical results, verifying functional equivalence.

## Problem Summary

The external memory path (`isExternalMemory == true`) must be invisible to wasm code — same VM dispatch, same `m3MemData` macro, same results. Running every existing test through both paths is the strongest proof of functional equivalence without writing bespoke unit tests for each scenario. Currently the test scripts only run one pass with internal memory.

## Scope

- In scope: `--external-mem <size>` argument added to `run-spec-test.py`
- In scope: `--external-mem <size>` argument added to `run-wasi-test.py`
- In scope: `--dual-pass` flag added to both scripts
- In scope: Dual-pass logic that compares results and fails on mismatch
- Out of scope: Adding new test cases (tests are the existing spec + WASI suites)
- Out of scope: Modifying the wasm3 binary (Goal 1.4 provides `--external-mem`)

## Current State

**`test/run-spec-test.py`:**

- Uses `--exec` arg (default `"../build/wasm3 --repl"`) to specify the wasm3 REPL command (line 51)
- The `Wasm3` class (line 183) starts a REPL subprocess and communicates via stdin/stdout
- Test stats tracked in `stats` dotdict (line 364): `total_run`, `skipped`, `failed`, `crashed`, `timeout`, `success`, `missing`
- Tests run in a single pass over JSON spec files (line 485-573)

**`test/run-wasi-test.py`:**

- Uses `--exec` arg (default `"../build/wasm3"`) to specify the wasm3 binary (line 28)
- Builds command arrays directly: `command = args.exec.split(' ')` then appends wasm file and args (line 159-164)
- Test stats tracked in `stats` dotdict (line 35): `total_run`, `failed`, `crashed`, `timeout`
- Runs a fixed list of WASI test commands (line 37-147)

## Assumptions and Constraints

- Goal 1.4 is complete: `wasm3 --external-mem <size>` works correctly
- Both test scripts are Python 3 and use `argparse`
- The spec test runner's `Wasm3` class manages a long-lived REPL subprocess — `--external-mem` must be part of the initial command
- The WASI test runner spawns fresh subprocesses per test — `--external-mem` is inserted into each command array
- Default external memory size for tests: 1MB (1048576 bytes) — large enough for all spec and WASI test modules

## Files and Areas Likely Affected

- `test/run-spec-test.py` — add `--external-mem` and `--dual-pass` args, modify exec command construction, add dual-pass loop
- `test/run-wasi-test.py` — add `--external-mem` and `--dual-pass` args, modify command construction, add dual-pass loop

## Implementation Steps

### Step 1: Modify `run-spec-test.py` — add arguments

Add to the argparse block (after line 60):

```python
parser.add_argument("--external-mem", metavar="<size>", type=int, default=0,
                    help="Run with external memory of given size (bytes)")
parser.add_argument("--dual-pass", action="store_true",
                    help="Run tests twice: once without --external-mem, once with")
```

### Step 2: Modify `run-spec-test.py` — inject `--external-mem` into exec command

After arg parsing (after line 62), modify the exec command when `--external-mem` is set:

```python
exec_cmd = args.exec
if args.external_mem > 0:
    exec_cmd += f" --external-mem {args.external_mem}"
```

Then use `exec_cmd` instead of `args.exec` when creating the `Wasm3` instance (line 331):

```python
wasm3 = Wasm3(exec_cmd)
```

### Step 3: Modify `run-spec-test.py` — add dual-pass logic

Wrap the main test loop (lines 331-598) in a function or add a pass counter. The dual-pass flow:

```python
def run_test_pass(exec_cmd):
    """Run the full spec test suite with the given exec command. Return stats."""
    # ... existing test logic using exec_cmd ...
    return stats

if args.dual_pass:
    # Pass 1: internal memory (baseline)
    stats_pass1 = run_test_pass(args.exec)
    print(f"\n--- Pass 1 (internal memory): {stats_pass1.success}/{stats_pass1.total_run} OK ---\n")

    # Pass 2: external memory
    ext_cmd = args.exec + f" --external-mem {args.external_mem}" if args.external_mem else args.exec + " --external-mem 1048576"
    stats_pass2 = run_test_pass(ext_cmd)
    print(f"\n--- Pass 2 (external memory): {stats_pass2.success}/{stats_pass2.total_run} OK ---\n")

    # Compare
    if stats_pass1.success != stats_pass2.success or stats_pass1.failed != stats_pass2.failed:
        print(f"{ansi.FAIL}DUAL-PASS MISMATCH: pass1={stats_pass1.success} OK, pass2={stats_pass2.success} OK{ansi.ENDC}")
        sys.exit(1)
    else:
        print(f"{ansi.OKGREEN}DUAL-PASS OK: both passes produced {stats_pass1.success}/{stats_pass1.total_run} results{ansi.ENDC}")
else:
    # Single pass (existing behavior)
    run_test_pass(exec_cmd)
```

### Step 4: Modify `run-wasi-test.py` — add arguments

Add to the argparse block (after line 33):

```python
parser.add_argument("--external-mem", metavar="<size>", type=int, default=0,
                    help="Run with external memory of given size (bytes)")
parser.add_argument("--dual-pass", action="store_true",
                    help="Run tests twice: once without --external-mem, once with")
```

### Step 5: Modify `run-wasi-test.py` — inject `--external-mem` into command arrays

In the test loop (line 155-200), when building the command array, insert `--external-mem` before the wasm file:

```python
command = args.exec.split(' ')
if args.external_mem > 0:
    command.append("--external-mem")
    command.append(str(args.external_mem))
command.append(cmd['wasm'])
if "args" in cmd:
    if args.separate_args:
        command.append("--")
    command.extend(cmd['args'])
```

### Step 6: Modify `run-wasi-test.py` — add dual-pass logic

Wrap the main test loop in a function and add dual-pass comparison:

```python
def run_wasi_pass(exec_cmd, external_mem):
    """Run the full WASI test suite. Return stats."""
    pass_stats = dotdict(total_run=0, failed=0, crashed=0, timeout=0)
    # ... existing test logic using exec_cmd and external_mem ...
    return pass_stats

if args.dual_pass:
    stats_pass1 = run_wasi_pass(args.exec, 0)
    print(f"\n--- Pass 1 (internal memory): {stats_pass1.total_run - stats_pass1.failed}/{stats_pass1.total_run} OK ---\n")

    ext_size = args.external_mem if args.external_mem else 1048576
    stats_pass2 = run_wasi_pass(args.exec, ext_size)
    print(f"\n--- Pass 2 (external memory): {stats_pass2.total_run - stats_pass2.failed}/{stats_pass2.total_run} OK ---\n")

    if stats_pass1.failed != stats_pass2.failed:
        print(f"{ansi.FAIL}DUAL-PASS MISMATCH{ansi.ENDC}")
        sys.exit(1)
    else:
        print(f"{ansi.OKGREEN}DUAL-PASS OK{ansi.ENDC}")
else:
    run_wasi_pass(args.exec, args.external_mem)
```

### Step 7: Verify

```sh
# Spec tests — single pass with external memory
cd test
python3 run-spec-test.py --external-mem 1048576

# Spec tests — dual pass
python3 run-spec-test.py --dual-pass

# WASI tests — single pass with external memory
python3 run-wasi-test.py --external-mem 1048576

# WASI tests — dual pass
python3 run-wasi-test.py --dual-pass

# Verify no-arg behavior unchanged
python3 run-spec-test.py
python3 run-wasi-test.py
```

## Verification Plan

### Automated Checks

- `python3 run-spec-test.py` — all spec tests pass (unchanged behavior)
- `python3 run-spec-test.py --external-mem 1048576` — all spec tests pass with external memory
- `python3 run-spec-test.py --dual-pass` — both passes produce identical results
- `python3 run-wasi-test.py` — all WASI tests pass (unchanged behavior)
- `python3 run-wasi-test.py --external-mem 1048576` — all WASI tests pass with external memory
- `python3 run-wasi-test.py --dual-pass` — both passes produce identical results

### Manual Checks

1. Confirm `--help` shows the new `--external-mem` and `--dual-pass` options
2. Confirm single-pass with `--external-mem` produces the same output format as baseline
3. Confirm dual-pass reports both pass results and comparison outcome
4. Confirm a intentional failure in pass 2 is caught and reported (test by using an invalid size)

## Risks and Open Questions

- Risk: Some WASI tests may require more than 1MB of memory. If so, the default `--external-mem 1048576` may need to be larger. Check the largest wasm module's memory requirements.
- Risk: The spec test runner's `Wasm3` class caches the loaded module (`self.loaded`). In dual-pass mode, the second pass creates a fresh `Wasm3` instance, so this is safe.
- Question: Should the default external memory size be configurable per-test? Recommendation: no, a single size for all tests is sufficient — the goal is functional equivalence, not stress testing.
- Question: Should dual-pass abort on first failure or run both passes regardless? Recommendation: run both passes regardless, then compare — this gives the most complete picture.
- Dependency: Requires Goal 1.4 (`--external-mem` CLI argument) to be complete.

## Completion Checklist

- [ ] `--external-mem <size>` argument works in `run-spec-test.py`
- [ ] `--external-mem <size>` argument works in `run-wasi-test.py`
- [ ] `--dual-pass` flag works in `run-spec-test.py`
- [ ] `--dual-pass` flag works in `run-wasi-test.py`
- [ ] Dual-pass comparison logic catches mismatches and exits with error
- [ ] Without new flags, both scripts behave identically to before
- [ ] All spec tests pass in both internal and external memory modes
- [ ] All WASI tests pass in both internal and external memory modes
- [ ] Implementation matches the goal spec in [goals1.md](../goals1.md)

## Notes for the Implementing Agent

- Read both Python test scripts fully before editing — understand the existing flow and stats tracking
- The spec test runner uses a long-lived subprocess (`Wasm3` class); the WASI runner spawns fresh processes per test. The `--external-mem` injection point differs accordingly.
- For `run-spec-test.py`, the main logic is currently inline (not in a function). You will need to refactor it into a callable function to support dual-pass. Keep the refactor minimal.
- For `run-wasi-test.py`, the main loop is already a simple `for cmd in commands` — wrapping it in a function is straightforward.
- The `ansi` color codes are imported from `testutils` — use them for pass/fail output formatting.
- After making changes, run both scripts with and without the new flags to verify backward compatibility.
