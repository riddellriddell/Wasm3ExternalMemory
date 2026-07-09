# Project Name — Design Specification

version: 1.0    
owner: "Your Name"    
repo: "your-repo"

---

## Purpose of This File

This file defines the architecture, principles, and design decisions for the project.

## Documentation Hierarchy

This file is **Tier 1** of the repository's documentation-first workflow.

| Tier | Document | Purpose |
| --- | --- | --- |
| 1 - Design | `design.md` | Project architecture, principles, and constraints |
| 2 - Milestones | [milestones.md](Milestones.md) | Roadmap structure and milestone summaries |
| 3 - Goals | `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) | Specific deliverables and acceptance criteria |
| 4 - Implementation Details | `ImplementationPlans/*.md` | Task-specific implementation plans and handovers |
| Support | [AgenticWorkFlow.md](AgenticWorkFlow.md) | Workflow for AI agent collaboration |
| Support | [AgentThinking.md](AgentThinking.md) | Optional temporary scratchpad for long tasks |

---

## Executive Summary

<!-- One-paragraph overview of the project's purpose and scope. -->

### Core Principles

- **Principle 1:** Description
- **Principle 2:** Description
- **Principle 3:** Description

---

## System Architecture

### How the Pieces Fit Together

<!-- Describe the major components and their layered dependencies. -->

```
Component A
    ↓
Component B
    ↓
Component C
```

**Core Components:**

- **Component A** — Description
- **Component B** — Description
- **Component C** — Description

### External Dependencies

| Dependency | Purpose |
| --- | --- |
| Dependency 1 | Description |
| Dependency 2 | Description |

### Repository Structure

```text
ProjectRoot/
|-- source/                  # Core library source
|-- platforms/               # Platform-specific applications
|-- docs/                    # Existing project documentation
|-- Documentation/           # AI workflow and planning docs
|-- test/                    # Tests
|-- CMakeLists.txt
|-- build.zig
```

---

## Processing Pipelines

<!-- Describe the main data/processing flows of the project. -->

### Pipeline 1: Name

**Status:** Implemented / Planned

```
Step 1 → Step 2 → Step 3 → Output
```

### Pipeline 2: Name

**Status:** Not yet implemented

```
Step 1 → Step 2 → Step 3 → Output
```

---

## Application Layers

<!-- Describe each major layer/module in detail. -->

### Layer 1: Name

**Purpose:** Description

**Architecture:** Description

**Key Capabilities:**

| Capability | Description | Use Case |
| --- | --- | --- |

### Layer 2: Name

**Purpose:** Description

---

## Dependency Rules

Dependencies are strictly layered:

```
Component A
    ↓
Component B
    ↓
Component C
```

**Rules:**
1. Rule 1
2. Rule 2
3. Rule 3

---

## Configuration

### Build Configuration

**Primary:** CMake-based build system

**Compiler Requirements:**
- C99 for core library
- Platform-specific tools as needed

### Runtime Configuration

<!-- List runtime dependencies and expected locations. -->

---

## Security and Privacy

<!-- Describe the security model, sandboxing, and privacy considerations. -->

---

## Observability

### Logging

### Debugging

---

## Testing Policy

### Core Principle

All features must have corresponding tests. Before any change is considered complete, all tests must pass.

### Test Framework

<!-- Describe the test framework and how to run tests. -->

### Required Test Coverage

| Component | Test Requirements |
| --- | --- |

### Test Categories

### Validation Requirements

Before any change is merged or considered complete:
1. Build the project
2. Run all test executables
3. Verify all tests pass
4. Fix any failing tests before declaring the change complete

---

## Performance

<!-- Describe performance considerations and trade-offs. -->

---

## Navigation

### Specification Hierarchy

- [design.md](Design.md) - Tier 1 design overview
- [milestones.md](Milestones.md) - Tier 2 roadmap summary
- `goals*.md` (from [GoalsTemplate.md](GoalsTemplate.md)) - Tier 3 goals and deliverables
- `ImplementationPlans/*.md` - Tier 4 execution plans and handovers

### Reference Documents

- [AgenticWorkFlow.md](AgenticWorkFlow.md) - AI collaboration workflow
- [AgentThinking.md](AgentThinking.md) - optional temporary agent scratchpad
