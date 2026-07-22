#!/usr/bin/env python3

# Author: Volodymyr Shymanskyy
# Usage:
#   ./run-wasi-test.py
#   ./run-wasi-test.py --exec ../custom_build/wasm3 --timeout 120
#   ./run-wasi-test.py --exec "wasmer run --mapdir=/:." --separate-args
#   ./run-wasi-test.py --exec "wasmer run --mapdir=/:. wasm3.wasm --" --fast
#   ./run-wasi-test.py --exec "wasmtime --dir=. wasm3.wasm --" --fast
#   ./run-wasi-test.py --exec "../build/wasm3 --stack-size 2097152 wasm3.wasm" --fast

import argparse
import sys
import subprocess
import hashlib
import fnmatch

sys.path.append('../extra')

from testutils import *
from pprint import pprint

#
# Args handling
#

parser = argparse.ArgumentParser()
parser.add_argument("--exec", metavar="<interpreter>", default="../build/wasm3")
parser.add_argument("--separate-args",  action='store_true')      # use "--" separator for wasmer, wasmtime
parser.add_argument("--timeout", type=int,             default=120)
parser.add_argument("--fast",    action='store_true')
parser.add_argument("--external-mem", metavar="<size>", type=int, default=0,
                    help="Run with external memory of given size (bytes)")
parser.add_argument("--dual-pass", action="store_true",
                    help="Run tests twice: once without --external-mem, once with")

args = parser.parse_args()

commands_full = [
  {
    "name":           "Simple WASI test",
    "wasm":           "./wasi/simple/test.wasm",
    "args":           ["cat", "/wasi/simple/0.txt"],
    "expect_pattern": "Hello world*Constructor OK*Args: *; cat; /wasi/simple/0.txt;*fib(20) = 6765* ms*48 65 6c 6c 6f 20 77 6f 72 6c 64*=== done ===*"
  }, {
    "name":           "Simple WASI test (wasm-opt -O3)",
    "wasm":           "./wasi/simple/test-opt.wasm",
    "args":           ["cat", "./wasi/simple/0.txt"],
    "expect_pattern": "Hello world*Constructor OK*Args: *; cat; ./wasi/simple/0.txt;*fib(20) = 6765* ms*48 65 6c 6c 6f 20 77 6f 72 6c 64*=== done ===*"
  }, {
    "name":           "mandelbrot",
    "wasm":           "./wasi/mandelbrot/mandel.wasm",
    "args":           ["128", "4e5"],
    "expect_sha1":    "37091e7ce96adeea88f079ad95d239a651308a56"
  }, {
    "name":           "mandelbrot (doubledouble)",
    "wasm":           "./wasi/mandelbrot/mandel_dd.wasm",
    "args":           ["128", "4e5"],
    "expect_sha1":    "b3f904daf1c972b4f7d3f8996743cb5b5146b877"
  }, {
    "name":           "C-Ray",
    "stdin":          "./wasi/c-ray/scene",
    "wasm":           "./wasi/c-ray/c-ray.wasm",
    "args":           ["-s", "128x128"],
    "expect_sha1":    "90f86845ae227466a06ea8db06e753af4838f2fa"
  }, {
    "name":           "smallpt (explicit light sampling)",
    "wasm":           "./wasi/smallpt/smallpt-ex.wasm",
    "args":           ["16", "64"],
    "expect_sha1":    "d85df3561eb15f6f0e6f20d5640e8e1306222c6d"
  }, {
    "name":           "smallpt (explicit light sampling, multi-value)",
    "wasm":           "./wasi/smallpt/smallpt-ex-mv.wasm",
    "args":           ["16", "64"],
    "expect_sha1":    "d85df3561eb15f6f0e6f20d5640e8e1306222c6d"
  }, {
    "name":           "mal",
    "wasm":           "./wasi/mal/mal.wasm",
    "args":           ["./wasi/mal/test-fib.mal", "16"],
    "expect_pattern": "987\n",
  }, {
    "name":           "STREAM",
    "wasm":           "./wasi/stream/stream.wasm",
    "expect_pattern": "----*Solution Validates:*on all three arrays*----*"
  }, {
    # TODO "if":             { "file_exists": "./self-hosting/wasm3-fib.wasm" },
    "name":           "Self-hosting",
    "wasm":           "./self-hosting/wasm3-fib.wasm",
    "expect_pattern": "wasm3 on WASM*Result: 832040*Elapsed: * ms*"
  }, {
    "name":           "Brotli",
    "stdin":          "./wasi/brotli/alice29.txt",
    "wasm":           "./wasi/brotli/brotli.wasm",
    "args":           ["-c", "-f"],
    "expect_sha1":    "8eacda4b80fc816cad185330caa7556e19643dff"
  }, {
    "name":           "CoreMark",
    "wasm":           "./wasi/coremark/coremark.wasm",
    "expect_pattern": "*Correct operation validated.*CoreMark 1.0 : * / Clang* / STATIC*"
  }
]

commands_fast = [
  {
    "name":           "Simple WASI test",
    "wasm":           "./wasi/simple/test.wasm",
    "args":           ["cat", "./wasi/simple/0.txt"],
    "expect_pattern": "Hello world*Constructor OK*Args: *; cat; ./wasi/simple/0.txt;*fib(20) = 6765* ms*48 65 6c 6c 6f 20 77 6f 72 6c 64*=== done ===*"
  }, {
    "skip":           True,  # Backtraces not enabled by default
    "name":           "Simple WASI test",
    "wasm":           "./wasi/test.wasm",
    "args":           ["trap"],
    "can_crash":      True,
    "expect_pattern": "Hello world*Constructor OK*Args: *; trap;* wasm backtrace:* 6: 0x*Error:* unreachable executed*"
  }, {
    "name":           "mandelbrot",
    "wasm":           "./wasi/mandelbrot/mandel.wasm",
    "args":           ["32", "4e5"],
    "expect_sha1":    "1fdb7dea7ec0f2465054cc623dc5a7225a876361"
  }, {
    "name":           "C-Ray",
    "stdin":          "./wasi/c-ray/scene",
    "wasm":           "./wasi/c-ray/c-ray.wasm",
    "args":           ["-s", "32x32"],
    "expect_sha1":    "05af9604bf352234276e4d64e84b8d666574316c"
  }, {
    "name":           "smallpt (explicit light sampling)",
    "wasm":           "./wasi/smallpt/smallpt-ex.wasm",
    "args":           ["4", "32"],
    "expect_sha1":    "ea05d85998b2f453b588ef76a1256215bf9b851c"
  }, {
    "name":           "smallpt (explicit light sampling, multi-value)",
    "wasm":           "./wasi/smallpt/smallpt-ex-mv.wasm",
    "args":           ["4", "32"],
    "expect_sha1":    "ea05d85998b2f453b588ef76a1256215bf9b851c"
  }, {
    "name":           "mal",
    "wasm":           "./wasi/mal/mal.wasm",
    "args":           ["./wasi/mal/test-fib.mal", "10"],
    "expect_pattern": "55\n",
  }, {
    "name":           "Brotli",
    "stdin":          "./wasi/brotli/alice29_small.txt",
    "wasm":           "./wasi/brotli/brotli.wasm",
    "args":           ["-c", "-f"],
    "expect_sha1":    "0e8af02a7207c0c617d7d38eed92853c4a619987"
  }
]

commands = commands_fast if args.fast else commands_full

def fail(msg, fail_stats):
    print(f"{ansi.FAIL}FAIL:{ansi.ENDC} {msg}")
    fail_stats.failed += 1

def run_wasi_pass(exec_cmd, external_mem):
    pass_stats = dotdict(total_run=0, failed=0, crashed=0, timeout=0)

    for cmd in commands:
        if "skip" in cmd:
            continue

        command = exec_cmd.split(' ')
        if external_mem > 0:
            command.append("--external-mem")
            command.append(str(external_mem))
        command.append(cmd['wasm'])
        if "args" in cmd:
            if args.separate_args:
                command.append("--")
            command.extend(cmd['args'])

        command = list(map(str, command))
        print(f"=== {cmd['name']} ===")
        pass_stats.total_run += 1
        try:
            if "stdin" in cmd:
                fn = cmd['stdin']
                f = open(fn, "rb")
                print(f"cat {fn} | {' '.join(command)}")
                output = subprocess.check_output(command, timeout=args.timeout, stdin=f)
            elif "can_crash" in cmd:
                print(f"{' '.join(command)}")
                output = subprocess.run(command, timeout=args.timeout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
            else:
                print(f"{' '.join(command)}")
                output = subprocess.check_output(command, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            pass_stats.timeout += 1
            fail("Timeout", pass_stats)
            continue
        except subprocess.CalledProcessError as e:
            pass_stats.crashed += 1
            fail(f"Exited with error code {e.returncode}", pass_stats)
            continue

        if "expect_sha1" in cmd:
            actual = hashlib.sha1(output).hexdigest()
            if actual != cmd['expect_sha1']:
                fail(f"Actual sha1: {actual}", pass_stats)

        if "expect_pattern" in cmd:
            actual = output.decode("utf-8")
            if not fnmatch.fnmatch(actual, cmd['expect_pattern']):
                fail(f"Output does not match pattern:\n{actual}", pass_stats)

        print()

    return pass_stats


if args.dual_pass:
    print(f"\n{'='*60}")
    print(f" PASS 1: INTERNAL MEMORY (baseline)")
    print(f"{'='*60}\n")
    stats_pass1 = run_wasi_pass(args.exec, 0)
    print(f"\n--- Pass 1 (internal memory): {stats_pass1.total_run - stats_pass1.failed}/{stats_pass1.total_run} OK ---\n")
    pprint(stats_pass1)

    ext_size = args.external_mem if args.external_mem else 268435456
    print(f"\n{'='*60}")
    print(f" PASS 2: EXTERNAL MEMORY ({ext_size} bytes)")
    print(f"{'='*60}\n")
    stats_pass2 = run_wasi_pass(args.exec, ext_size)
    print(f"\n--- Pass 2 (external memory): {stats_pass2.total_run - stats_pass2.failed}/{stats_pass2.total_run} OK ---\n")
    pprint(stats_pass2)

    if stats_pass1.failed != stats_pass2.failed:
        print(f"{ansi.FAIL}{'='*60}")
        print(f" DUAL-PASS MISMATCH")
        print(f"{'='*60}{ansi.ENDC}")
        print(f"  Pass 1 (internal):  {stats_pass1.total_run - stats_pass1.failed}/{stats_pass1.total_run} OK, {stats_pass1.failed} failed")
        print(f"  Pass 2 (external):  {stats_pass2.total_run - stats_pass2.failed}/{stats_pass2.total_run} OK, {stats_pass2.failed} failed")
        sys.exit(1)
    else:
        print(f"{ansi.OKGREEN}{'='*60}")
        print(f" DUAL-PASS OK: both passes produced {stats_pass1.total_run - stats_pass1.failed}/{stats_pass1.total_run} results")
        print(f"{'='*60}{ansi.ENDC}")
else:
    stats = run_wasi_pass(args.exec, args.external_mem)

    pprint(stats)

    if stats.failed:
        print(f"{ansi.FAIL}=======================")
        print(f" FAILED: {stats.failed}/{stats.total_run}")
        print(f"======================={ansi.ENDC}")
        sys.exit(1)

    else:
        print(f"{ansi.OKGREEN}=======================")
        print(f" All {stats.total_run} tests OK")
        print(f"======================={ansi.ENDC}")
