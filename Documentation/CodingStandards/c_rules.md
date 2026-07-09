Version: 1.1
Date Created: 10/07/2026
Owner: "wasm3"

# C Coding Rules

> Target: C99 projects using standard tooling (Clang, GCC, MSVC).

## Scope
- Applies to all C in this workspace.
- Goal: readable, consistent, maintainable code that compiles cleanly across platforms.

## Language & Standards
- Target C99 (ISO/IEC 9899:1999) as the base standard.
- Use C99 fixed-width types from `<stdint.h>`: `u64`, `i64`, `u32`, `i32`, `u16`, `i16`, `u8`, `i8`. Use plain `int` only when width is irrelevant.
- Use `bool` from `<stdbool.h>` for booleans.
- Standard Library: use C99 standard library functions. Avoid platform-specific APIs unless absolutely necessary (wrap in `#ifdef`).
- **Type Aliases**: Prefer the project's short fixed-width typedefs (from `m3_core.h`):
  ```c
  typedef uint64_t        u64;
  typedef int64_t         i64;
  typedef uint32_t        u32;
  typedef int32_t         i32;
  typedef uint16_t        u16;
  typedef int16_t         i16;
  typedef uint8_t         u8;
  typedef int8_t          i8;
  typedef double          f64;
  typedef float           f32;
  ```
- **Internal pointer typedefs** (from `m3_core.h`):
  ```c
  typedef const char *            cstr_t;
  typedef const char * const      ccstr_t;
  typedef const u8 *              bytes_t;
  typedef const u8 * const        cbytes_t;
  typedef const void *            m3ret_t;
  typedef const void *            voidptr_t;
  typedef u16                     m3opcode_t;
  ```

## Naming
- `snake_case` for functions, variables, and file-scope identifiers.
- `m3_` prefix for all exported public API functions (`m3_NewEnvironment`, `m3_ParseModule`, etc.) and types (`M3Result`, `IM3Module`, `M3Module`).
- Internal function naming uses two patterns:
  - `VerbObject`: `AllocFuncType`, `AcquireCodePage`, `ResizeMemory`, `ReadCompile`
  - `Module_Verb` (PascalCase-with-underscore): `Module_AddGlobal`, `Environment_Release`, `Function_Release`
- **Public types** use PascalCase without `_t` suffix: `M3Result`, `M3ErrorInfo`, `M3Module`, `M3ValueType`.
- **Internal type aliases** use `_t` suffix: `m3reg_t`, `m3slot_t`, `m3opcode_t`, `cstr_t`, `bytes_t`.
- **Macro naming** uses several patterns:
  - `d_m3` prefix (mixed case, project feature flags): `d_m3HasTracer`, `d_m3FixedHeap`, `d_m3MaxSaneTypesCount`
  - `M3_` prefix (UPPER_SNAKE_CASE, public constants): `M3_VERSION_MAJOR`, `M3_BACKTRACE_TRUNCATED`, `M3_UNLIKELY`
  - `c_` prefix (lowercase, internal constants): `c_waTypes`, `c_waCompactTypes`, `c_ioSlotCount`
  - `m3` prefix (lowercase, API macros): `m3log`, `m3ApiRawFunction`, `m3ApiReturnType`
- **Enum types**: PascalCase (`M3ValueType`).
- **Enum values**: `c_m3Type_*` pattern (lowercase `c_` prefix + PascalCase): `c_m3Type_none`, `c_m3Type_i32`, `c_m3Type_unknown`.

## Function Parameter Convention
Use Hungarian-style prefixes for all function parameters:
- `i_` for input-only parameters: `i_module`, `i_typeA`, `i_signature`
- `o_` for output parameters (written to): `o_functionType`, `o_codePage`
- `io_` for input/output parameters: `io_module`, `io_runtime`

```c
M3Result  AllocFuncType  (IM3FuncType * o_functionType, u32 i_numTypes);
bool      AreFuncTypesEqual  (const IM3FuncType i_typeA, const IM3FuncType i_typeB);
void      Module_AddGlobal  (IM3Module io_module, M3Global * i_global);
```

## Exception-Like Error Handling
The codebase uses a custom `_try`/`_throw`/`_catch` macro system (from `m3_exception.h`) for error propagation, NOT C++ exceptions:

```c
#define _try          M3Result result = m3Err_none;
#define _(TRY)        { result = TRY; if (M3_UNLIKELY(result)) { EXCEPTION_PRINT(result); goto _catch; } }
#define _throw(ERROR) { result = ERROR; EXCEPTION_PRINT(result); goto _catch; }
```

Usage pattern:
```c
M3Result  SomeFunction  (IM3Module io_module)
{
_try {
    _(SomeOtherFunction (io_module));

    if (not io_module)
        _throw (m3Err_invalidData);

    // ... happy path
    return m3Err_none;
} _catch {
    return result;    // result holds the error string
}
}
```

Key points:
- `M3Result` is `typedef const char *` — success is `m3Err_none` (NULL), errors are string literals.
- The `_(call)` macro wraps a call and jumps to `_catch` on failure.
- `_throw(string)` jumps immediately to `_catch`.
- Always check return values with `_(...)` or `M3_UNLIKELY`.

## Operator Macros
The codebase defines `not`, `and`, `or` as operator aliases (from `m3_config_platforms.h`):

```c
#define not      !
#define and      &&
#define or       ||
```

Used extensively instead of `!`, `&&`, `||`:
```c
if (not o_functionType)
    _throw ("null function type");
```

## Files & Includes
- File names: `snake_case.c` / `snake_case.h` matching their primary content (e.g., `m3_compile.c`, `m3_env.h`).
- All headers use `#ifndef`/`#define`/`#endif` include guards:
  ```c
  #ifndef m3_core_h
  #define m3_core_h
  // ...
  #endif // m3_core_h
  ```
- IWYU mindset:
  - Include only what you use; avoid umbrella headers.
  - Don't rely on transitive includes. Include everything you use directly.
- Order:
  - `.c`: include its own header first, then standard library, then project headers.
  - System headers with `<>`, project headers with `""`.

## Formatting
- **4-space indentation** (no tabs).
- **Allman braces** for functions and control flow: opening `{` on its own line.
- `switch` blocks: opening `{` after `switch` on same line or own line (match existing file convention).
- `else` clauses: can be `} else {` on one line or `}\nelse {` on separate lines (match existing convention).
- Braces on single-statement `if` blocks are preferred but not strictly enforced (match surrounding code).
- One statement per line.
- **Pointer/reference spacing**: `Type * name` (space on both sides of `*`):
  ```c
  M3Result  AllocFuncType  (IM3FuncType * o_functionType, u32 i_numTypes);
  ```
- **Function call spacing**: space before `(` in calls and control keywords:
  ```c
  m3_Malloc ("M3FuncType", sizeof (M3FuncType));
  if (not ptr)
  while (true)
  ```
- **Function definition spacing**: double space between return type and function name, double space between name and `(`
- Max line length: 120 characters.
- Leave a single blank line at end of file.

## Compiler Attributes
Use the project's attribute macros (defined in `wasm3_defs.h`):
- `M3_UNLIKELY(expr)` / `M3_LIKELY(expr)` for branch prediction hints
- `M3_NOINLINE` to prevent inlining
- `M3_WEAK` for weak symbols
- `M3_NO_UBSAN` to suppress undefined behavior sanitizer

```c
if (M3_UNLIKELY(result))
    return result;

static M3_NOINLINE void  EmitOp  (IM3Compilation o, m3opcode_t i_opcode);
```

## Control Flow
- `if/else`: braces on all branches preferred. `else if` aligned with `if`.
- `switch`: every case breaks/returns or has an explicit `/* fall through */` comment. Always provide `default:`.
- Minimize nesting. Split large functions into well-named helpers.
- Validate all external inputs early.

## Memory Management
- Prefer stack allocation where possible.
- Dynamic allocation: use the project's allocator wrappers:
  ```c
  void * m3_Malloc (const char * i_name, size_t i_size);
  void   m3_Free   (void * io_ptr);
  ```
  The `i_name` parameter is a descriptive label for tracking allocations.
- Convenience macros:
  ```c
  #define m3_AllocStruct(TYPE)           (TYPE *) m3_Malloc (#TYPE, sizeof (TYPE))
  #define m3_AllocArray(TYPE, COUNT)     (TYPE *) m3_Alloc (#TYPE, sizeof (TYPE) * (COUNT))
  ```
- Clear ownership semantics: document which function owns allocated memory.
- No C++ features (no exceptions, no RTTI, no templates).

## Function Design
- Use `static` for file-local (private) functions.
- Return `M3Result` for operations that can fail; return other types for pure queries.
- Mark read-only pointer parameters with `const`:
  ```c
  bool  AreFuncTypesEqual  (const IM3FuncType i_typeA, const IM3FuncType i_typeB);
  ```
- Use clear verb+object naming: `ParseModule`, `ReadCompile`, `FreeCompiledCode`.
- The `Module_Verb` pattern is used for internal module operations: `Module_AddGlobal`, `Module_AddFunction`.

## Platform-Specific Code
- Use `#if defined(...)` / `#elif defined(...)` / `#endif` for compile-time platform selection:
  ```c
  #if defined(WIN32) || defined(_WIN32)
      // Windows-specific
  #elif defined(__linux__)
      // Linux-specific
  #else
      // Fallback
  #endif
  ```
- Keep platform differences isolated in small, well-documented sections.
- Use the existing `d_m3` / `d_m3Has*` macro pattern for feature flags.

## Comments & Docs
- U.S. English for code and comments.
- Comments describe *why* the code exists, not *what* the code does.
- Keep comments concise and accurate. Update when behavior changes.
- Use `//` for single-line comments, `/* */` for multi-line or inline annotations.
- Public API functions in `wasm3.h` should have a comment describing their purpose, parameters, and return value.

## Assertions & Tracing
- Use `d_m3Assert(cond)` for internal assertions (defined in `m3_config.h`).
- Standard `assert()` from `<assert.h>` is also acceptable for programming errors.
- Use the `m3log` tracing macros for debug output, gated by `d_m3HasTracer`:
  ```c
  m3log (compile, "emitting opcode: %d", opcode);
  ```
- `d_m3HasTracer` is a compile-time definition (set via CMake), not defined in headers.

## Compile-Time Configuration
- Use `#define` constants and `#if defined()` for compile-time options:
  ```c
  #define d_m3HasTracer
  #define d_m3FixedHeap   1048576
  #define d_m3MaxSaneTypes 1000
  ```
- Group related configuration in `m3_config.h` and `m3_config_platforms.h`.

## Testing
- Tests live in `test/` directory with subdirectories: `fuzz/`, `internal/`, `lang/`, `regression/`, `self-hosting/`, `wasi/`.
- Use `run-spec-test.py` and `run-wasi-test.py` for spec and WASI test suites.
- Include positive, negative, and edge cases in test coverage.
- Ensure all tests pass before considering implementation complete.

## Examples

```c
// Example: reading a module from a byte buffer
// Copyright wasm3. All rights reserved.
#ifndef example_module_reader_h
#define example_module_reader_h

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "wasm3.h"

typedef struct M3ModuleReader
{
    const u8 *      bytes;
    u32             numBytes;
    bool            bParsed;
}
M3ModuleReader;

M3Result  ModuleReader_Init    (M3ModuleReader * o_reader);
void      ModuleReader_Free    (M3ModuleReader * io_reader);
bool      ModuleReader_IsValid (const M3ModuleReader * i_reader);

#endif // example_module_reader_h
```

```c
static M3Result
ValidateBytecode  (const u8 * i_bytes, u32 i_numBytes)
{
    if (not i_bytes)
        _throw (m3Err_invalidData);

    if (i_numBytes < 4)
        _throw ("bytecode too short");

    return m3Err_none;
}
```
