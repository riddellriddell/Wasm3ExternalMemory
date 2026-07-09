# Shared Rules Index

This file routes the agent to the minimum relevant shared rules for the current repository and task.

## How To Use This Index

1. Identify the repository technology stack from the files in the workspace.
2. Identify the current task type, such as implementation, UI work, testing, documentation, or review.
3. Load only the rule files directly relevant to that stack and task.
4. Do not read unrelated rule files just because they exist in this directory.

## Rule Files

| File | Review When |
| --- | --- |
| [global_rules.md](global_rules.md) | Always review first for general coding expectations that apply across repositories. |
| [c_rules.md](c_rules.md) | Review when the repository uses C style and tooling. |
| [cmake_rules.md](cmake_rules.md) | Review when the repository uses CMake build system. |
| [README.md](README.md) | Review only if you need background on how this shared rules directory is organized. |

## Selection Rules

- Always load [global_rules.md](global_rules.md).
- Load [c_rules.md](c_rules.md) when the repo contains `.c`, `.h` files.
- Load [cmake_rules.md](cmake_rules.md) when the repo contains `CMakeLists.txt` files.
- Load multiple files when the stack requires it, but only if each file is directly relevant.

## Conflict Resolution

- Repository-local instructions override shared rules.
- Task-specific instructions override general rules.
- When two shared rules overlap, prefer the more specific technology rule for implementation details and retain the general rule for cross-cutting standards.

## Example Decisions

- C feature work: review `global_rules.md` and `c_rules.md`.
- Documentation-only change: review `global_rules.md` and skip language-specific rules unless code is also being edited.
- CMake changes: review `global_rules.md` and `cmake_rules.md`.
