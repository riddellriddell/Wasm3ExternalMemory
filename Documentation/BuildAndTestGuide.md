Version: 1.0
Date Created: 11/07/2026
Owner: "wasm3"

# Build and Test Guide

This document provides step-by-step instructions for building and testing the Wasm3 project. It is based on a verified build on Windows (x86_64) using GCC/MinGW 13.2.0, CMake 4.2.1, Ninja 1.12.1, and Python 3.12.10.

## Prerequisites

### Required
- **C compiler**: GCC (MinGW), Clang, or MSVC
- **CMake** >= 3.11
- **Python 3** (for running tests)

### Optional
- **Ninja** (recommended over default Makefiles for speed)
- **Zig** toolchain (alternative build system)
- **Git** (needed for test suite auto-download)

### Windows-Specific Notes
- **Use GCC (MinGW)** as the C compiler. Clang on Windows (without clang-cl) will fail to link because the CMake build adds `-lm` which does not exist on Windows — only GCC/MinGW provides a compatible `libm`.
- If using the MSVC generator (Visual Studio), no extra flags are needed, but the default WASI backend (`uvwasi`) requires fetching dependencies via CMake's FetchContent (requires internet access).
- Using `-DBUILD_WASI=simple` avoids the uvwasi/libuv dependency fetch.

## Building

### Quick Start (Recommended)

```sh
mkdir build
cd build
cmake -GNinja -DBUILD_WASI=simple ..
cmake --build build
```

This produces `build/wasm3.exe` (Windows) or `build/wasm3` (Linux/macOS).

### CMake Options

| Option | Values | Default | Notes |
|---|---|---|---|
| `BUILD_WASI` | `none`, `simple`, `uvwasi`, `metawasi` | `uvwasi` (Unix), `metawasi` (WASI) | `simple` avoids external dependencies |
| `BUILD_NATIVE` | `ON`/`OFF` | `ON` | Adds `-march=native` for host-specific optimizations |
| `CMAKE_BUILD_TYPE` | `Release`, `Debug` | `Release` | |
| `BUILD_FUZZ` | `ON`/`OFF` | `OFF` | Requires Clang; enables libFuzzer |

### Build with GCC (Linux / MinGW on Windows)

```sh
mkdir build && cd build
cmake -GNinja -DBUILD_WASI=simple -DCMAKE_C_COMPILER=gcc ..
cmake --build .
```

### Build with Clang (Linux / macOS)

```sh
mkdir build && cd build
cmake -GNinja -DBUILD_WASI=simple ..
cmake --build .
```

### Build with MSVC (Windows)

```sh
mkdir build && cd build
cmake -G"Visual Studio 17 2022" -A x64 ..
cmake --build . --config Release
cp build/Release/wasm3.exe build/
```

### Build with Zig

```sh
zig build
```

Output: `zig-out/bin/wasm3`. For release builds:

```sh
zig build -Drelease-fast
```

### Build with Compiler Directly

```sh
# GCC/Clang (Linux)
gcc -O3 -g0 -s -Isource -Dd_m3HasWASI source/*.c platforms/app/main.c -lm -o wasm3
```

### Direct Compile Verification

On the verified Windows setup, the following exact commands produced a working build:

```sh
mkdir build && cd build
cmake -GNinja -DBUILD_WASI=simple -DCMAKE_C_COMPILER=gcc ..
ninja
```

Build output: `build/wasm3.exe` (verified working, version `Wasm3 v0.5.2 on x86_64`).

## Testing

### Prerequisites for Testing
- **Python 3** must be installed and available as `python3` (or `python` on Windows)
- The `test/` directory must contain the test WASM binaries (included in the repo under `test/wasi/`)
- The spec test suite is auto-downloaded on first run

### Running WebAssembly Spec Tests

```sh
cd test
python3 run-spec-test.py
```

This automatically downloads the WebAssembly core test suite from GitHub, then runs it against the built `wasm3` binary. By default it looks for `../build/wasm3 --repl`.

Expected result: `17863/17863 tests OK` (with ~235 skipped).

To test against a previous spec version:

```sh
cd test
python3 run-spec-test.py --spec=v1.1
```

To run a specific test file:

```sh
cd test
python3 run-spec-test.py ../path/to/test.json
```

### Running WASI Integration Tests

```sh
cd test
python3 run-wasi-test.py
```

This runs pre-built WASI applications (CoreMark, C-Ray, Brotli, mandelbrot, smallpt, etc.) and verifies their output.

Expected result: `All 12 tests OK`.

For a faster subset of tests:

```sh
cd test
python3 run-wasi-test.py --fast
```

To test against a custom interpreter:

```sh
cd test
python3 run-wasi-test.py --exec "path/to/wasm3"
```

### Fuzz Testing

Build the fuzzer (requires Clang):

```sh
mkdir build-fuzzer && cd build-fuzzer
cmake -GNinja -DCLANG_SUFFIX="-12" -DBUILD_FUZZ=ON ..
ninja
```

Run the fuzzer:

```sh
cd test
../build-fuzzer/wasm3-fuzzer -detect_leaks=0 ./fuzz/corpus
```

### Full Test Workflow

The complete sequence to build and test on this project:

```sh
# Build
mkdir build && cd build
cmake -GNinja -DBUILD_WASI=simple -DCMAKE_C_COMPILER=gcc ..
ninja
cd ..

# Run spec tests
cd test
python3 run-spec-test.py
cd ..

# Run WASI tests
cd test
python3 run-wasi-test.py
cd ..
```

## Troubleshooting

### Clang on Windows fails with "could not open 'm.lib'"
The CMake build links `-lm` (math library) for non-MSVC builds. On Windows, Clang without clang-cl falls into the GCC/Clang code path but lacks `libm`. **Solution**: Use GCC (MinGW) instead, or use the MSVC/Visual Studio generator.

### Python not found on Windows
Windows may not have `python3` on PATH. Try `python` instead, or ensure Python 3 is installed and added to PATH.

### Spec test download fails
The spec test suite is downloaded from GitHub on first run. If you are behind a firewall, manually download and extract the test suite into `test/.spec-opam-1.1.1/`.

### WASI tests timeout
Some WASI tests (CoreMark, Brotli) can be slow. The default timeout is 120 seconds. Use `--timeout` to increase it if needed.

### Deprecated function warnings on Windows
Clang on Windows produces deprecation warnings for `fopen`, `getenv`, `lseek`, `setmode`, `fileno`. These are harmless and caused by Windows CRT security deprecation notices. They do not affect the build.

## Build Artifacts

After a successful build:

| Path | Description |
|---|---|
| `build/wasm3.exe` (Windows) / `build/wasm3` (Unix) | Main interpreter binary |
| `build/source/libm3.a` (Unix) / `build/source/m3.lib` (Windows) | Static library (`libm3`) |
| `build/CMakeFiles/` | CMake build metadata |
