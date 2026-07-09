# Coding Standards Directory

A centralized collection of technology-specific coding standards and best practices for use with AI-assisted development in this project.

## Purpose & Goals

- **Consistency**: Apply the same high-quality standards across the project
- **Maintainability**: Single source of truth for coding conventions
- **Quality**: Curated and battle-tested coding standards
- **Flexibility**: Technology-specific rules that adapt to the current context

## Technology Coverage

### Current Rules Files

- **`global_rules.md`** - General coding expectations that apply across the entire project.
  - DRY, SOLID, clarity over brevity, meaningful naming, U.S. English.

- **`c_rules.md`** - C99 coding standards.
  - C99 standard conformance, `snake_case` naming, `m3_` prefix convention.
  - Allman braces, tab indentation, clear ownership semantics.

- **`cmake_rules.md`** - CMake build system conventions.
  - Modern target-based commands, C99 standard, wasm3-specific options.

## Rule Precedence

1. Repository-local instructions override shared rules.
2. Task-specific instructions override general rules.
3. More specific technology rules take precedence for implementation details.

## How to Use This Directory

1. Always load `global_rules.md` first.
2. Load technology-specific rules based on the files being edited (`.c` → `c_rules.md`, `CMakeLists.txt` → `cmake_rules.md`).
3. Do not load rule files that aren't relevant to the current task.
