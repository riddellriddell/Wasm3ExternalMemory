# WasmTestBedMK1 - Milestones

version: 1.0    
owner: "Jack Riddell"    
repo: "WasmTestBedMK1"

---

> Authoritative milestone definitions for the project.
>
> Related: [design.md](design.md), [agenticworkflow.md](agenticworkflow.md), [AgentThinking.md](AgentThinking.md)

---

## Table of Contents

| Milestone | Goals File | Status | Why | Impact |
| --- | --- | --- | --- | --- |
| [Milestone 1: WASM Run Pipeline](#milestone-1) | [goals1.md](goals1.md) | In Progress | Foundation for WasmRunInterface | End-to-end execution pipeline with WAMR multi-threading |
| [Milestone 2: Alternative Execution Pipelines](#milestone-2) | [goals2.md](goals2.md) | Not Started | wasm2c2 and native DLL modes | Additional execution options |
| [Milestone 3: GUI Project Setup](#milestone-3) | [goals3.md](goals3.md) | Not Started | ImGui GUI foundation | Test/refine script execution API |
| [Milestone 4: Script Execution Integration](#milestone-4) | [goals4.md](goals4.md) | Not Started | WasmRunInterface in GUI | Compile and run predefined WASM script |
| [Milestone 5: Script Edit and Execute](#milestone-5) | [goals5.md](goals5.md) | Not Started | Basic script editing workflow | Write, compile, and execute scripts |

---

## Template

When adding a new milestone, use this structure:

```markdown
<a id="milestone-N"></a>

## Milestone N: Name

**Intent:** One sentence describing what this milestone is supposed to achieve.

**Why it matters:**

- Reason 1
- Reason 2
- Reason 3

**Impact:**

- Outcome 1
- Outcome 2
- Outcome 3

**Status:** Not Started - 0/? goals complete. See [goalsN.md](goalsN.md) for details.

**Goals:** [goalsN.md](goalsN.md)
```

---

<a id="milestone-1"></a>

## Milestone 1: WASM Run Pipeline

**Intent:** Establish a functioning WASM execution pipeline with bidirectional function calling between native host code and WASM guest modules, including WAMR as the primary runtime with multi-threaded shared memory support.

**Why it matters:**

- This is the foundation for WasmRunInterface - without reliable WASM execution, nothing else is possible
- The wasm3 and WAMR runtime integrations provide the execution backends that wasm2c2 and native DLL pipelines must match
- WAMR multi-threading enables concurrent WASM execution with shared memory — a capability wasm3 cannot provide
- Function calling conventions define the security boundary between untrusted code and the host

**Impact:**

- End-to-end pipeline: C++ source → WASM compilation → wasm3/WAMR execution
- Native code can invoke WASM functions with typed parameters and return values
- WASM modules can call back into host-provided functions
- WAMR supports multi-threaded execution with shared memory and host-driven threading
- Establishes the core execution model that wasm2c2 and native pipelines must match

**Status:** In Progress - 5/14 goals complete (1 goal won't fix). See [goals1.md](goals1.md) for details.

**Goals:** [goals1.md](goals1.md)

---

<a id="milestone-2"></a>

## Milestone 2: Alternative Execution Pipelines

**Intent:** Implement wasm2c2 and native DLL execution modes alongside the existing wasm3 and WAMR runtimes, providing a unified scripting interface with multiple performance/security trade-offs.

**Why it matters:**

- wasm2c2 offers near-native performance while retaining WASM's sandbox security model
- Native DLL loading provides maximum performance for trusted code, with improved build times and debuggability compared to WASM compilation
- Users should be able to select execution mode based on their needs without changing calling code

**Impact:**

- wasm2c2 pipeline: WASM → C conversion → native compilation → shared library → execution
- Native DLL pipeline: native source → shared library → execution
- Common API abstracts execution mode from caller - same interface regardless of whether wasm3, WAMR, wasm2c2, or native DLL is used

**Status:** Not Started - 0/2 goals complete. See [goals2.md](goals2.md) for details.

**Goals:** [goals2.md](goals2.md)

---

<a id="milestone-3"></a>

## Milestone 3: GUI Project Setup

**Intent:** Establish a GUI application project with ImGui integration as a foundation for testing and refining the script execution API.

**Why it matters:**

- Provides a runnable GUI executable to test and iterate on the script execution API without command-line friction
- Establishes robust CMake build configuration following the same patterns as CommonEnvironment and WasmRunInterface
- ImGui provides a lightweight, portable immediate-mode GUI framework

**Impact:**

- `guiFrontend/` subproject scaffold with ImGui integrated
- CMake setup matching the build structure and test configuration of CommonEnvironment and WasmRunInterface
- Runnable "Hello World" example rendering simple text via ImGui
- Foundation ready for adding code editor and script execution integration

**Status:** Not Started - 0/? goals complete. See [goals3.md](goals3.md) for details.

**Goals:** [goals3.md](goals3.md)

---

<a id="milestone-4"></a>

## Milestone 4: Script Execution Integration

**Intent:** Integrate WasmRunInterface into guiFrontend and prove the execution pipeline works via a GUI button that compiles and runs a predefined WASM script.

**Why it matters:**

- Validates that the WasmRunInterface library can be embedded in the GUI application
- Establishes the integration pattern for all future script execution features
- A working end-to-end example provides a foundation for adding features like code editing, output display, and script management

**Impact:**

- WasmRunInterface linked into guiFrontend via CMake
- Button click triggers compilation of a predefined C++ string (e.g., `int main() { /*print hello world*/ }`) to WASM
- Compiled WASM executes via the configured runtime
- Result logged to console output
- Proven integration pattern for building more features on top

**Status:** Not Started - 0/? goals complete. See [goals4.md](goals4.md) for details.

**Goals:** [goals4.md](goals4.md)

---

<a id="milestone-5"></a>

## Milestone 5: Script Edit and Execute

**Intent:** Add a basic script editing and execution workflow to the GUI with a text editor, output display, and compilation/execution logging.

**Why it matters:**

- Enables users to write, test, and iterate on C++ scripts directly in the GUI
- Separating output from logs provides clear feedback during development
- Establishes the UI pattern for script interaction that future features build upon

**Impact:**

- Text editor panel for writing or pasting C++ code
- Output panel displaying the script's returned string
- Console panel showing compilation and execution stage logs
- Simple fixed-layout UI with minimum elements needed to write, compile, and execute scripts

**Status:** Not Started - 0/? goals complete. See [goals5.md](goals5.md) for details.

**Goals:** [goals5.md](goals5.md)

---

## Guidelines

- Use one milestone for each major stage of the project.
- Keep milestones thematic rather than overly granular.
- Link every milestone to a goals file.
- Update milestone status as goals progress.
- Use `AgentThinking.md` only for temporary task notes, not for milestone definitions.
