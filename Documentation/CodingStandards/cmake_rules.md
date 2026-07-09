Version: 1.1
Date Created: 10/07/2026
Owner: "wasm3"

# CMake Rules

## Scope and priority
- Target: CMake-based builds on multiple platforms (Windows, Linux, macOS, embedded).
- Applies to: All `CMakeLists.txt` and `.cmake` files.
- Precedence: Project rules > Global rules > Tool defaults.

## Build system requirements
- Minimum CMake version: 3.11
- Use `cmake_minimum_required()` at the top of the root `CMakeLists.txt`.
- Project name: `wasm3`.

## Build commands
- Primary CMake build:
  ```sh
  cmake -B build
  cmake --build build
  ```
- Alternative builds:
  - `zig build` (Zig-based build)
  - `build-cross.py` (cross-compilation helper)
- Platform-specific build projects are in `platforms/` (PlatformIO, Android Studio, Xcode, etc.).

## Root CMakeLists.txt structure
The root `CMakeLists.txt` performs these steps in order:

1. **Environment detection** (before `project()`):
   - WasiEnv detection (`$ENV{WASI_CC}` / `WASI_SDK_PREFIX`)
   - MinGW detection (`WIN32` + GNU compiler)
   - Toolchain configuration (Clang, Emscripten, CLANG_CL, 32-bit)

2. **Option configuration**:
   ```cmake
   option(BUILD_NATIVE "Build with machine-specific optimisations" ON)
   set(BUILD_WASI "uvwasi" CACHE STRING "WASI implementation")
   set_property(CACHE BUILD_WASI PROPERTY STRINGS none simple uvwasi metawasi)
   ```

3. **Compiler flags** set via `CMAKE_C_FLAGS` (global, not target-based):
   ```cmake
   set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Dd_m3HasTracer")
   ```
   Note: `d_m3HasTracer` is set unconditionally for WASIENV, MSVC, and GCC/Clang builds (not debug-only).

4. **Project declaration**:
   ```cmake
   project(wasm3)
   ```

5. **C standard configuration**:
   ```cmake
   set(CMAKE_C_STANDARD 99)
   set(CMAKE_C_STANDARD_REQUIRED YES)
   set(CMAKE_C_EXTENSIONS YES)
   ```

6. **Application target** (file glob from `APP_DIR`):
   ```cmake
   file(GLOB app_srcs "${APP_DIR}/*.c")
   add_executable(${OUT_FILE} ${app_srcs})
   ```

7. **WASI dependency setup** (FetchContent for uvwasi/libuv when needed).

8. **LTO/IPO configuration**:
   ```cmake
   check_ipo_supported(RESULT result)
   if(result AND NOT WASIENV)
     set_property(TARGET ${OUT_FILE} PROPERTY INTERPROCEDURAL_OPTIMIZATION True)
   endif()
   ```

9. **Library and install**:
   ```cmake
   add_subdirectory(source)
   install(TARGETS ${OUT_FILE} RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
   ```

## Source library target (`source/CMakeLists.txt`)

Defines the `m3` static library with modern target-based commands:

```cmake
add_library(m3 STATIC ${sources})
target_include_directories(m3 PUBLIC .)
target_compile_features(m3 PRIVATE c_std_99)
```

WASI compile definitions are set via `target_compile_definitions`:
```cmake
if(BUILD_WASI MATCHES "simple")
    target_compile_definitions(m3 PUBLIC d_m3HasWASI)
elseif(BUILD_WASI MATCHES "metawasi")
    target_compile_definitions(m3 PUBLIC d_m3HasMetaWASI)
elseif(BUILD_WASI MATCHES "uvwasi")
    target_compile_definitions(m3 PUBLIC d_m3HasUVWASI)
endif()
```

## Key options

| Option | Values | Default | Purpose |
|--------|--------|---------|---------|
| `BUILD_WASI` | `none`, `simple`, `uvwasi`, `metawasi` | varies by platform | WASI implementation backend |
| `BUILD_NATIVE` | `ON`/`OFF` | `ON` | Machine-specific optimizations (`-march=native`) |
| `CLANG_SUFFIX` | e.g. `-12` | (empty) | Clang version suffix |
| `CLANG_CL` | (set to `ON`) | (unset) | Use clang-cl on Windows |
| `APP_DIR` | path | `platforms/app` | Application source directory |
| `BUILD_FUZZ` | (set to `ON`) | (unset) | Fuzzer build configuration |
| `BUILD_32BIT` | (set to `ON`) | (unset) | 32-bit build (`-m32`) |
| `WASM_EXT` | (set to `ON`) | (unset) | Enable WASM extensions (bulk memory, sign-ext, tail-call) |

## Platform support
- **WasiEnv**: cross-compiles wasm3 to WebAssembly (`wasm3.wasm`)
- **Emscripten**: builds for browser (`wasm3.html`) or standalone WASM
- **MSVC/ClangCL**: Windows builds with MSVC or clang-cl toolchain
- **GCC/Clang**: Linux, macOS, and Unix-like platforms
- **Platform apps**: Individual platform projects in `platforms/` (may use PlatformIO, Android Studio, Xcode, etc. rather than CMake)

## Testing
- Tests live in `test/` directory (not wired into CMake directly).
- Use `run-spec-test.py` and `run-wasi-test.py` for spec and WASI test suites.
- See `docs/Testing.md` for detailed test instructions.

## Formatting
- Indent 4 spaces.
- Use meaningful variable names.
- Group related commands with blank lines.

## Enforcement
- Build with at least one major compiler (Clang, GCC, MSVC) before merging.
- Verify clean build with no errors.
