Version: 1.0
Date Created: 5:31 PM 24/08/2025
Last Edit Date: 5:45 PM 24/08/2025
Owner: "Jarryd Adaens"

# C++ Coding Rules (Workspace)

> Target: Modern C++ projects using C++20 and standard tooling.

## Scope
- Applies to all C++ in this workspace.
- Goal: readable, consistent, maintainable code that compiles fast.

## Language & Types
- Use fixed-width types where size matters: `int32`, `uint8`, `int64`, etc. Use plain `int` only when width is irrelevant.
- Use `bool` for booleans. Do not assume size of `bool`.
- Standard Library: allowed when superior. Avoid mixing idioms in the same API. Keep consistency within an API surface.
- **Avoid `auto`**: Use explicit types for clarity, except for long template types.
- **Type Aliases**: Use `using X = Y` instead of `typedef`. Prefer custom types with `snake_case` names:
  ```cpp
  using int8 = signed char;
  using int16 = short;
  using int32 = int;
  using int64 = decltype(9223372036854775807);
  using uint8 = unsigned char;
  using uint16 = unsigned short;
  using uint32 = unsigned int;
  using uint64 = decltype(18446744073709551615u);
  using float32 = float;
  using float64 = double;
  ```
- **Template Parameters**: Use `PascalCase` for type parameters.
- **Template Concepts (C++20)**: Use `PascalCase` for concept names.

## Naming
- PascalCase for types, methods, and most identifiers.
- Variables:
  - Member variables use `m_` prefix (`m_timeoutMs`, `m_processId`).
  - Static variables use `s_` prefix (`s_defaultTimeout`, `s_instanceCount`).
  - Booleans: member variables use `m_b` prefix (`m_bIsVisible`, `m_bPendingDestroy`), local variables use `b` prefix (`bIsVisible`, `bPendingDestroy`).
  - Use descriptive nouns for data. Avoid cryptic acronyms.
  - One declaration per line.
- Functions:
  - Boolean returns ask a question: `IsVisible()`, `ShouldClearBuffer()`.
  - Procedures use strong verb + object: `ResetCache()`, `ApplySettings()`.
  - Prefer explicit, descriptive names over abbreviations.
- Parameters:
  - Use `camelCase`.
  - If a parameter is passed by non-const reference and is written to, prefix with `Out`: `OutResult`. If also boolean, `bOutSucceeded`.
  - Optional: input parameters may use the `in_` prefix (e.g., `int32 in_Count`). Use consistently across your codebase if adopted.
- Templates:
  - Template type parameters may use `In` prefix to disambiguate (`template<typename InElementType>` then `using ElementType = InElementType;`).
- Macros: ALL_CAPS with underscores, prefix with your project/module tag (e.g., `PROJECT_`, `YOURMODULE_`).
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_TIMEOUT_MS`, `MAX_BUFFER_SIZE`). Use `static constexpr` where possible.
- Enum Types: `PascalCase` for enum type, `PascalCase` for enumerators.

## Class Organization
- Public interface first, then protected, then private.
- Enforce encapsulation. Keep members private unless part of the intended API. Provide protected accessors if needed.
- `final` for types not intended for inheritance.

## Namespaces
- Use namespaces to organize code and prevent naming conflicts.
- No `using` in global scope. `using` is OK within a namespace or function body.

## Files & Includes
- File names match their primary type names: e.g., `BatteryStatus.h/.cpp` for `BatteryStatus`.
- All headers use `#pragma once`.
- IWYU mindset:
  - Forward-declare where possible in headers; include in `.cpp`.
  - Include only what you use; avoid umbrella headers.
  - Don't rely on transitive includes. Include everything you use directly.
- Order:
  - `.cpp`: include its own header first, then other includes.

## Formatting
- Tabs for indentation. Tab width 4. Spaces only for alignment after non-tab characters.
- Allman braces: opening `{` on its own line for functions, control blocks, and class/structs.
- Always use braces, even for single-statement blocks.
- One statement per line.
- Pointer/reference spacing: `Type* Ptr`, `Type& Ref` (one space to the right of `*` or `&`).
- Leave a single blank line at end of file.

## Control Flow
- `if/else`: braces on all branches. `else if` aligned with `if`.
- `switch`: every case breaks/returns or has an explicit `// falls through`. Always provide `default:`.
- Minimize dependency distance. Initialize close to use. Split large functions into well-named helpers.

## Strings & Text
- Prefer named constants over magic literals in calls. Example: `Trigger(ObjectName, CooldownSeconds, bCanInterrupt)`.

## Memory Management
- **Avoid Smart Pointers**: Prefer raw pointers with clear ownership semantics.
- **No Shared Pointers**: Avoid `shared_ptr` due to performance concerns.
- **RAII**: Use RAII principles where appropriate.
- **Explicit Ownership**: Code should clearly know object lifetimes - when an object starts and ends its life.
- **Be Explicit**: Be explicit about object ownership and responsibility for cleanup.

## Function Design
- Use `[[nodiscard]]` where the return value should not be ignored. Apply to functions whose return value must be handled to prevent silent failures.
- Mark member functions as `const` when they don't modify object state.
- Use `const` extensively to enforce immutability contracts and prevent accidental modification.

### Const Correctness
- **Function Parameters**: Pass by `const&` for input parameters that are not modified:
  ```cpp
  void ProcessData(const std::string& in_data);
  int32 CalculateTotal(const std::vector<int32>& in_values);
  ```
- **Pointers**: Use `const Type*` when pointer is input, `Type* const` when pointer itself is const, `const Type* const` for both:
  ```cpp
  void Read(const uint8* in_data);        // pointer to const data
  void Write(uint8* const out_data);      // const pointer to mutable data
  void Modify(uint8* const inout_data);   // const pointer to const data
  ```
- **Return Types**: Return by `const` for non-modifiable return types:
  ```cpp
  const std::string& GetName() const;
  const uint64 GetId() const;
  ```
- **Local Variables**: Use `const` for values that do not change after initialization:
  ```cpp
  const size_t maxSize = CalculateMaxSize();
  const auto& item = GetItem();
  ```

- Comprehensive documentation for all functions:
  ```cpp
  /**
   * Brief description of what the function does
   * @param param1 Description of parameter
   * @param param2 Description of parameter  
   * @return Description of return value
   * @throws ExceptionType Description of when exception is thrown
   * @constraints Any constraints or prerequisites
   */
  ```

## Performance Guidelines
### Compile-Time Optimization
- Use `constexpr` where possible to run functions at compile time.
- Prioritize compile-time calculation over runtime calculation where possible.

### Hot Loop Optimization
- Push branching statements (`if`, `switch`) **out** of hot loops.
- Push data manipulation and calculations **into** loops for bulk operations.
- Minimize branching in frequently executed code.
- Structure loops for sequential memory access patterns.

### Branch Hoisting
- Validate parameters once before entering loops.
- Use template specialization for compile-time branching.

### Memory Access Patterns
- Favor sequential access patterns for better cache utilization.
- Process data in chunks for better cache performance.

## CRTP Pattern
Use Curiously Recurring Template Pattern for platform-specific implementations:
```cpp
template<typename Impl>
class BaseInterface {
public:
    static ReturnType PublicMethod() {
        return Impl::ImplementationMethod();
    }
};

class ConcreteImplementation : public BaseInterface<ConcreteImplementation> {
public:
    static ReturnType ImplementationMethod() {
        // Platform-specific code
    }
};
```

## Platform-Specific Code
- Use `{Platform}{Feature}Interface` naming pattern (e.g., `WindowsOSInterface`, `LinuxOSInterface`).
- Use `#ifdef` for compile-time platform selection.
- For WebAssembly: Consider WASM sandbox limitations in all new code.

## Logging & Asserts
- Use standard asserts (`assert`, `static_assert`) for programming errors.
- Keep assert messages actionable.

## Error Handling
- Validate all external inputs early.
- Use assertions to catch programming errors.
- Validate function parameters and class invariants.
- Use exceptions for exceptional circumstances.
- Use error codes for expected error conditions.
- Log errors meaningfully without exposing sensitive information.

## Comments & Docs
- U.S. English for code and comments.
- Keep comments concise and accurate. Update when behavior changes.
- Comments should describe why the code exists not what code does
- Classes and structs should have a comment above them describing their role in the codebase
- Place variable documentation above the declaration. Optional blank lines to group variables.

## Testing Guidelines
- Write tests before implementation when possible (test-first development).
- Include positive, negative, and edge cases in test coverage.
- Use descriptive test names that convey purpose.
- Group tests in logical categories using tags.
- Ensure all tests pass before considering implementation complete.

## Examples

```cpp
// Example class
// Copyright Your Studio. All Rights Reserved.
#pragma once

#include <cstdint>
#include <vector>
#include <string>

class BatteryStatusComponent
{
public:
    BatteryStatusComponent();

    bool IsBatteryLow() const;

    void GetLowBatteryThreshold(int32& OutThreshold) const;

    int32 GetSize(int32 in_sizeOfExample) const;

private:
    int32 m_batteryPercent = 100;
    int32 m_lowThreshold = 20;
    bool m_bIsCharging = false;
    std::vector<int32> m_cache;
    int32 m_mode = 0;
};

inline int32 BatteryStatusComponent::GetSize(int32 in_sizeOfExample) const
{
    const bool bHasCache = m_cache.size() > static_cast<size_t>(in_sizeOfExample);
    if (bHasCache)
    {
        return m_cache.back();
    }

    switch (m_mode)
    {
        case 0:
            // falls through
        case 1:
            return 1;
        default:
            return 0;
    }
}
