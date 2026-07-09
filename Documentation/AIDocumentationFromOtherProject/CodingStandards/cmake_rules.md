Version: 1.0
Date Created: 6:17 PM 24/08/2025
Last Edit Date: 6:18 PM 24/08/2025
Owner: "Jarryd Adaens"

# CMake Rules

## Scope and priority
- Target: CMake-based builds on Windows 11 with clang-cl and Ninja.
- Applies to: All `CMakeLists.txt` and `.cmake` files.
- Precedence: Project rules > Global rules > Tool defaults.

## Build system requirements
- Minimum CMake version: 3.21
- Use `cmake_minimum_required()` at the top of the root `CMakeLists.txt`.
- Project name should match repository name or directory.

## Build commands
- Use `Build.bat` as the primary build method. Available options:
  - `Build.bat incremental` (default): Builds incrementally, preserves dependencies
  - `Build.bat clean`: Full clean build, removes everything
  - `Build.bat fresh`: Clean build artifacts, preserve dependencies
- Each sub-project has its own `Scripts/test.bat` for running tests.

## Standard structure
- Every CMake command should have a comment explaining:
  - What the command does
  - Any requirements or constraints it enforces
  - Why it's needed in this location
- Example:
  ```cmake
  # Minimum CMake version required for modern features (e.g., target_compile_features)
  cmake_minimum_required(VERSION 3.21)

  # Project name and version - used for install targets and package metadata
  project(MyProject VERSION 1.0.0 LANGUAGES C CXX)

  # Option to enable/disable tests - defaults to ON, can be disabled for packaging
  option(BUILD_TESTS "Build tests" ON)

  # Find fmt library - REQUIRED ensures build fails if not found
  find_package(fmt REQUIRED)

  # Library - STATIC archive for linking into executables
  add_library(mylib STATIC
      src/lib.cpp
      include/lib.h
  )
  # Expose include directory to all consumers of this library
  target_include_directories(mylib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
  # Link fmt library - PUBLIC propagates dependency to consumers
  target_link_libraries(mylib PUBLIC fmt::fmt)

  # Executable - main application entry point
  add_executable(myapp src/main.cpp)
  # Link mylib as PRIVATE since executable doesn't re-export it
  target_link_libraries(myapp PRIVATE mylib)

  # Tests - only build when tests are enabled
  if(BUILD_TESTS)
      enable_testing()
      add_subdirectory(tests)
  endif()
  ```

## Target requirements
- Always use modern target-based commands: `target_compile_definitions`, `target_include_directories`, `target_link_libraries`.
- Never use global commands like `include_directories` or `link_directories`.
- Specify `PUBLIC`, `PRIVATE`, or `INTERFACE` visibility explicitly.
- Use `INTERFACE` libraries for header-only libraries.

## Compiler settings
- Set standards via `target_compile_features()`, not `CMAKE_CXX_STANDARD`:
  ```cmake
  target_compile_features(mylib PRIVATE cxx_std_20)
  ```
- For Windows with clang-cl:
  ```cmake
  if(WIN32)
      set_target_properties(mylib PROPERTIES
          CXX_EXTENSIONS OFF
      )
  endif()
  ```

## Dependencies
- Use `find_package()` with `REQUIRED` for mandatory dependencies.
- Use `FetchContent` or ` CPMAddPackage` for third-party dependencies if not available via system package manager.
- Prefer `GLOBAL` aliases for package targets:
  ```cmake
  add_library(fmt::fmt ALIAS fmt)
  ```

## Installation
- Use `install()` commands for exported targets:
  ```cmake
  install(TARGETS mylib
      EXPORT MyProjectTargets
      LIBRARY DESTINATION lib
      ARCHIVE DESTINATION lib
  )
  install(EXPORT MyProjectTargets
      FILE MyProjectTargets.cmake
      NAMESPACE MyProject::
      DESTINATION lib/cmake/MyProject
  )
  ```

## Testing
- Enable testing with `enable_testing()`.
- Use `add_test(NAME ... COMMAND ...)` for test executables.
- Each sub-project should have a `Scripts/test.bat` that runs its tests.

## CMake commenting requirements
- All CMakeLists.txt and .cmake files must have comments on every significant command
- Each comment should explain:
  - What the command does
  - Any requirements or constraints
  - Why it's needed in that context
- Group related commands with blank lines and a preceding comment describing the group
- Header comments should document:
  - Purpose of the file
  - Any external dependencies or tools required
  - Platform-specific notes if applicable

## File layout
```
CMakeLists.txt
cmake/              # CMake modules
  FindXXX.cmake
  XXXConfig.cmake
/tests/
  CMakeLists.txt
  test_*.cpp
/src/
/include/
```

## Formatting
- Indent 4 spaces.
- Max line 100 characters.
- Use meaningful variable names.
- Group related commands with blank lines.

## Editor configs
- Add `.editorconfig` with 4 spaces and 100 col.

## Enforcement
- CI checks: configure with clang-cl + Ninja, build all targets, run tests.
