# WasmTestBedMK1 - Design Specification

version: 1.0    
owner: "Jack Riddell"    
repo: "WasmTestBedMK1"

---

## Purpose of This File

This file defines the architecture, principles, and design decisions for the WasmTestBedMK1 project - a framework for compiling, executing, and comparing C++ code across multiple execution targets.

## Documentation Hierarchy

This file is **Tier 1** of the repository's documentation-first workflow.

| Tier | Document | Purpose |
| --- | --- | --- |
| 1 - Design | `design.md` | Project architecture, principles, and constraints |
| 2 - Milestones | [milestones.md](milestones.md) | Roadmap structure and milestone summaries |
| 3 - Goals | `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) | Specific deliverables and acceptance criteria |
| 4 - Implementation Details | `ImplementationPlans/*.md` | Task-specific implementation plans and handovers |
| Support | [AgenticWorkFlow.md](AgenticWorkFlow.md) | Workflow for AI agent collaboration |
| Support | [AgentThinking.md](AgentThinking.md) | Optional temporary scratchpad for long tasks |

---

## Executive Summary

WasmTestBedMK1 is a framework for compiling, executing, and comparing C++ code across multiple execution targets. It supports WASM execution via the wasm3 interpreter, WASM-to-C conversion via wasm2c2, and direct native execution.

### Core Principles

- **Modular Architecture**: Strict separation between platform abstractions, runtime components, and UI
- **Cross-Platform Support**: Unified interface across Windows, Linux, and WebAssembly targets
- **Zero-Overhead Abstractions**: Header-only library design with compile-time platform selection using CRTP
- **Extensibility**: Clear pipeline stages that can be extended or replaced independently

---

## System Architecture

### How the Pieces Fit Together

The system consists of three main components with strictly layered dependencies:

```
guiFrontend (planned)
    ↓
WasmRunInterface
    ↓
CommonEnvironment
```

**Core Components:**

- **CommonEnvironment** - Header-only C++20 cross-platform abstraction library
- **WasmRunInterface** - C++ compilation pipeline, WASM execution, WASM2C conversion
- **guiFrontend** (future) - User interface for code editing and execution control

### External Dependencies

| Dependency | Purpose |
| --- | --- |
| WASI SDK / Clang | C++ to WebAssembly compilation |
| wasm3 | WebAssembly interpreter runtime |
| wasm2c2 | WebAssembly to C conversion |
| Catch2 | Testing framework |

### Repository Structure

```text
WasmTestBedMK1/
|-- AGENTS.md
|-- CMakeLists.txt
|-- Build.bat
|-- CommonEnvironment/           # Header-only cross-platform library
|   |-- include/                 # Public headers
|   |   |-- OsInterface.h       # Main entry point
|   |   |-- OsInterfaceInternal.h
|   |   |-- OsWindowsInterface.h
|   |   |-- OsLinuxInterface.h
|   |   |-- OsWasmInterface.h
|   |   |-- OsTypes.h
|   |   |-- OsLimits.h
|   |   |-- MemorySpan.h
|   |-- source/
|   |-- tests/
|   |-- CMakeLists.txt
|   |-- README.md
|-- WasmRunInterface/            # WASM runtime and build tools
|   |-- source/
|   |   |-- WasmRunner.cpp       # WASM execution runtime
|   |   |-- WasmBuildTool.cpp    # C++ to WASM compilation
|   |-- Include/
|   |-- Resources/
|   |   |-- scripts/             # Test scripts and samples
|   |   |-- WasmBuildTool/
|   |-- Tests/
|   |-- CMakeLists.txt
|-- Documentation/
|   |-- design.md
|   |-- milestones.md
|   |-- goals1.md
|   |-- agenticworkflow.md
|   |-- AgentThinking.md
|   |-- ImplementationPlans/
|-- cmake/                       # CMake build utilities
|-- Tools/                       # External tools (WASI SDK, etc.)
```

---

## Processing Pipelines

### Pipeline 1: WASM Execution (Implemented)

```
C++ Source File
    ↓
WASI SDK / Clang → WASM
    ↓
WasmRunner (wasm3 runtime)
    ↓
Output
```

**Status**: Implemented in `WasmRunInterface`

**Components**:
- `WasmBuildTool::Build()` - Compiles C++ to WASM using wasi-sdk
- `WasmRunner` - Executes WASM using wasm3 interpreter

---

### Pipeline 2: WASM2C Execution (Planned)

```
C++ Source File
    ↓
WASI SDK / Clang → WASM
    ↓
wasm2c2 → Generated C Code
    ↓
Native Compiler (MSVC/GCC/Clang)
    ↓
Native Shared Library (DLL/so)
    ↓
Native Execution
    ↓
Output
```

**Status**: Not yet implemented

**Planned Components**:
- WASM to C conversion using wasm2c2 library
- Native compilation to DLL/SO
- Dynamic library loading and execution

---

### Pipeline 3: Direct Native Execution (Planned)

```
C++ Source File
    ↓
Native Compiler (MSVC/GCC/Clang)
    ↓
Native Shared Library (DLL/so)
    ↓
Native Execution
    ↓
Output
```

**Status**: Not yet implemented

---

## Application Layers

### Layer 1: CommonEnvironment

**Purpose**: Generic toolkit for hardware abstraction providing foundational building blocks for higher-level systems

CommonEnvironment serves as a cross-platform foundation layer that abstracts hardware and operating system differences. It provides reusable components that can be leveraged by any project needing platform-agnostic functionality.

**Architecture**:
- Header-only C++20 library using CRTP pattern
- Compile-time platform selection via preprocessor macros
- C++20 Concepts for interface validation
- No runtime dependencies - compiles directly into consuming projects

**Building Blocks**:

| Category | Components | Purpose |
| --- | --- | --- |
| **Hardware Abstraction** | `OsInterface` family | Unified interface for OS operations across Windows, Linux, and WebAssembly |
| **Memory Management** | `MemorySpan`, `AllocateMemory` | Cross-platform memory allocation with WASM sandbox awareness |
| **Data Structures** | `MemorySpan` | Type-safe memory region abstractions |
| **Type System** | `OsTypes.h`, `OsLimits.h` | Consistent type definitions (`uint64`, `uint32`, etc.) across platforms |
| **Process Management** | `LaunchProcess`, `LaunchedProcess` | Spawn and manage external processes with output capture |

**Platform Support**:
| Feature | Windows | Linux | WebAssembly |
| --- | --- | --- | --- |
| Process Launching | ✅ Full (Win32) | ✅ Basic (system) | ❌ Blocked (static_assert) |
| Memory Management | ✅ | ✅ | ✅ (Limited) |
| File Operations | ✅ | ✅ | Limited (WASI only) |

**Design Rationale**:
By providing these building blocks in a header-only library with compile-time platform selection, CommonEnvironment enables:
- Zero-overhead abstractions (no virtual function overhead)
- Compile-time validation of platform capabilities
- Consistent API surface across all supported platforms
- Easy integration into any C++ project via CMake or direct inclusion

---

### Layer 2: WasmRunInterface

**Purpose**: Secure runtime scripting layer for loading and executing untrusted logic via WebAssembly or native DLLs

WasmRunInterface provides a library for embedding a safe scripting environment in host applications. The core value proposition is **security isolation** - allowing users or external parties to provide runtime logic (scripts, plugins, user code) without the risk of compromising the host system.

**Architecture**:
- CMake-based C++ library
- Depends on CommonEnvironment for platform abstractions
- Uses wasm3 interpreter for WASM execution
- Planned support for wasm2c2 and native DLL loading

**Core Capabilities**:

| Capability | Description | Use Case |
| --- | --- | --- |
| **WASM Compilation** | Compiles C++ source to WebAssembly via WASI SDK/Clang | User provides C++ code, system compiles to sandboxed WASM |
| **WASM Execution** | Runs WASM modules via wasm3 interpreter | Safe execution of compiled logic in isolated environment |
| **WASM2C Conversion** (planned) | Converts WASM to C via wasm2c2, then compiles to native | Higher performance when security of WASM sandbox is sufficient |
| **Native DLL Loading** (planned) | Loads and executes native shared libraries | Opt-in performance mode with trusted code |
| **Script Discovery** | Scans directories for compilable C++ files | Batch processing of user-provided scripts |

**Security Model**:

The primary purpose of using WebAssembly as the execution engine is **capability-based security**. The architecture separates user-provided code from the host application through enforced isolation layers:

- **User-Provided Code (C++)**: Can only access explicitly exported APIs. Cannot access filesystem (except via WASI), cannot spawn processes, cannot access arbitrary memory, network access limited to WASI sockets.

- **WebAssembly Sandbox**: Provides enforced memory isolation and restricts host system access to only what is explicitly exported.

**Why This Matters**:
Traditional plugin systems (DLL loading, native FFI) allow code to access everything the host process can access. A malicious or buggy plugin could read/write arbitrary files, exfiltrate sensitive data, spawn malicious processes, or exploit vulnerabilities in the host.

WebAssembly's sandbox model limits what the untrusted code can do, regardless of what APIs are exported. Even if an attacker compromises the WASM module, they cannot escape the sandbox to attack the host system.

**Execution Pipeline**:

User C++ Code is compiled via WASI SDK/Clang to produce a WASM binary. The resulting binary can then be executed through multiple options:

| Execution Mode | Engine | Trade-off |
| --- | --- | --- |
| Interpreter | wasm3 | Fast iteration, cross-platform |
| Compiled | wasm2c2 → Native | Higher performance |
| Native DLL | Dynamic loader | Full performance, requires trust |

**Use Cases**:
- Game modding systems where players can write scripts
- Plugin systems for extensible applications
- Educational platforms where students run code
- Sandboxed scripting in embedded devices
- Any scenario where untrusted code must be executed safely

---

### Layer 3: guiFrontend (Future)

**Purpose**: User interface for code editing and execution control

**Architecture**: Not yet designed or implemented

**Planned Features**:
- Code editor with syntax highlighting
- Execution mode selection (WASM, WASM2C, Native)
- Output display and comparison
- Project/script management

---

## Dependency Rules

Dependencies are strictly layered:

```
guiFrontend (future)
    ↓
WasmRunInterface
    ↓
CommonEnvironment
```

**Rules**:
1. `CommonEnvironment` must not depend on any other project
2. `WasmRunInterface` may depend on `CommonEnvironment`
3. `guiFrontend` may depend on both

---

## Configuration

### Build Configuration

**Primary**: CMake-based build system

**Compiler Requirements**:
- C++20 for CommonEnvironment
- Clang with WASM target support (via WASI SDK)

### Runtime Configuration

**WASI SDK**: Required for C++ to WebAssembly compilation
- Expected location: `Tools/wasi-sdk/bin/clang++`

**wasm3**: Embedded as subdirectory dependency
- Compiled as part of WasmRunInterface build

---

## Security and Privacy

### WebAssembly Security Constraints

WebAssembly runs in a security sandbox that prohibits certain operations:

- **Process Launching**: Blocked with compile-time `static_assert`
- **Direct System Calls**: Not permitted
- **File I/O**: Limited to WASI-compliant operations
- **Network Access**: Only through WASI interfaces

### Code Execution

- User-provided C++ code is compiled and executed locally
- No network transmission of code
- WASM sandbox provides isolation for untrusted code

---

## Observability

### Logging

- Console output via `std::cout`
- Process output captured via `LaunchedProcess::GetOutput()`
- Build tool commands logged before execution

### Debugging

- WASM execution errors logged to console
- Clang compilation failures captured and reported
- Exit code propagation for error detection

---

## Testing Policy

### Core Principle

All features must have corresponding tests. Before any change is considered complete, all tests must pass. This ensures:
- New features are properly validated
- Existing functionality is not broken by changes
- The system remains stable across platforms and execution modes

### Test Framework

- **Catch2**: Used for unit and integration tests
- **Build Toggle**: Tests built when `BUILD_TESTING=ON` is set in CMake
- **Execution**: Test binaries output to `build/WasmRunInterface/` directory

### Required Test Coverage

| Component | Test Requirements |
| --- | --- |
| **CommonEnvironment** | Tests for each platform abstraction (Windows, Linux, WASM), memory management, process launching, type definitions |
| **WasmRunInterface** | Tests for WASM compilation pipeline, wasm3 runtime integration, script discovery, output capture |
| **New Features** | Every new feature must include tests that verify its functionality |

### Test Categories

- **Platform Abstraction Tests**: Validate CommonEnvironment on each supported platform. Tests must pass on Windows, Linux, and WASM targets.
- **WASM Compilation Tests**: Verify the C++ to WASM pipeline produces valid WASM binaries that can be executed.
- **WASM Execution Tests**: Validate wasm3 runtime integration, including function invocation, memory handling, and output capture.
- **Cross-Platform Tests**: Ensure consistent behavior across Windows, Linux, and WebAssembly targets.
- **Integration Tests**: Test interactions between CommonEnvironment and WasmRunInterface components.

### Validation Requirements

Before any change is merged or considered complete:
1. Build the project with `BUILD_TESTING=ON`
2. Run all test executables
3. Verify all tests pass on all target platforms
4. Fix any failing tests before declaring the change complete

---

## Performance

**Current Status**: Performance is not the primary concern for this experimental framework.

**Considerations**:
- wasm3 is an interpreter (slower than JIT/AOT)
- WASM2C pipeline aims to provide native-speed execution
- CommonEnvironment uses zero-overhead abstractions (header-only, CRTP)

---

## Navigation

### Specification Hierarchy

- [design.md](design.md) - Tier 1 design overview
- [milestones.md](milestones.md) - Tier 2 roadmap summary
- `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) - Tier 3 goals and deliverables
- `ImplementationPlans/*.md` - Tier 4 execution plans and handovers

### Reference Documents

- [AgenticWorkFlow.md](AgenticWorkFlow.md) - AI collaboration workflow
- [AgentThinking.md](AgentThinking.md) - optional temporary agent scratchpad

### Component Documentation

- [CommonEnvironment/README.md](../CommonEnvironment/README.md) - Platform abstraction library
