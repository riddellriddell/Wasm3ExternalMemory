# Agentic Workflow

version: 1.0    
owner: "Your Name"    
repo: "your-repo"    

---

**How AI agents collaborate with the developer in this repository**

[Back to Design Specification](design.md)

---

## Tiered Specification Hierarchy

The project uses a four-tier specification system that moves from broad project direction to concrete implementation work.

```text
Tier 1: Design Specification (design.md)
  |  Project-wide architecture, principles, and constraints
  |
  +--> Tier 2: Milestones (milestones.md)
  |     Thematic groupings of related deliverables
  |
  +--> Tier 3: Goals (goals1.md, goals2.md, ...)
  |     Individual features, bugs, or significant changes
  |
  +--> Tier 4: Implementation Details (ImplementationPlans/)
        Task-specific implementation plans and phase handovers
```

### Goal Variants

When a goal requires research or prototyping of multiple alternative approaches, use lettered variants such as `Goal 1.2A`, `Goal 1.2B`, and `Goal 1.2C`. Only one variant is ultimately selected; the others should be marked as failed, rejected, or superseded.

Variants answer: *Which approach should we use?*

### Goal Phases

When a goal is too large for a single pass, split it into sequential phases such as Phase 1, Phase 2, and Phase 3. Phases are execution steps for one chosen approach, not competing alternatives.

Phases answer: *What order do we build this in?*

---

## Phase Execution and Context Management

Phase splitting exists to manage AI context limitations. A single conversation should not carry the entire history of a large feature if a smaller, cleaner handoff can do the job.

### AgentThinking.md

`AgentThinking.md` is an optional scratchpad for temporary working notes during a long or complex task.

**Rules:**

- Do not use `AgentThinking.md` unless explicitly instructed or genuinely needed for task continuity.
- Treat it as temporary working memory, not as authoritative project documentation.
- Reset or replace its contents when switching to a different feature, goal, or bug.
- Avoid committing it unless preserving context across separate AI runs is important.

### Phase Handover Documents

At the end of a phase, create a handover document so a fresh AI session can continue the work without depending on prior chat history.

**Location:** `Documentation/ImplementationPlans/`

**Naming convention:**

| Context | Naming Pattern | Example |
| --- | --- | --- |
| Goal-based work | `GOAL_<M>_<G>_<variant>_handover_from_phase<N>.md` | `GOAL_1_3_A_handover_from_phase1.md` |
| Bug fix | `BUG_<short-slug>_handover_from_phase<N>.md` | `BUG_timeout_error_handover_from_phase1.md` |
| Feature (no goal) | `FEATURE_<short-slug>_handover_from_phase<N>.md` | `FEATURE_export_csv_handover_from_phase1.md` |

**Minimum contents:**

1. What was completed in this phase
2. What exists in the repository now
3. Explicit next steps
4. Key decisions and rationale
5. Known issues, risks, or open questions
6. Important files and sections to read next

### How the Next AI Starts a Later Phase

1. Read the handover document first.
2. Then read only the necessary project documents:
   - `design.md`
   - the relevant goals file
   - `AgentThinking.md` only if it was used and is still relevant
3. Continue from the documented repo state rather than reconstructing the full prior conversation.

---

## Multi-Model Orchestration

This project uses capability-tiered model allocation so the level of model effort matches the difficulty of the task.

| Task Domain | Model Tier | Examples |
| --- | --- | --- |
| Architecture and planning | High-capability | design decisions, milestone definition, major refactors |
| Implementation plans | High-capability | detailed Tier 4 job packets |
| Implementation execution | Mid-capability | routine coding, doc updates, scoped feature work |
| Review and analysis | High-capability | code review, system analysis, deeper synthesis |

### Actual Workflow

1. The developer researches and captures requirements.
2. Requirements are brought into the agentic IDE workflow.
3. A high-capability model revises plans against the on-disk repository and current documentation.
4. Tier 1 through Tier 3 documents are updated as needed.
5. A Tier 4 implementation plan is created when work is ready for execution.
6. An implementation-focused agent executes against that plan and the repository.

---

## Documentation Lifecycle

- `design.md`, `milestones.md`, and the goals files are authoritative and maintained.
- `ImplementationPlans/*.md` contains active task plans and phase handovers.
- `AgentThinking.md` is temporary and should stay lightweight.
- Wiki and reference material may become stale and should be checked against the source of truth.

---

## Agent Operational Guidelines

When assigned work in this repository:

1. Check for a relevant handover document first if the work is phased.
2. Read the minimum necessary context in this order:
   - `CodingStanndards/index.md`
   - `design.md`
   - `milestones.md` when scope or roadmap matters
   - the relevant goals file
   - `AgentThinking.md` only when explicitly needed
3. If a Tier 4 implementation plan exists for the task, follow it closely.
4. Keep repository structure, naming, and documentation conventions consistent.
5. Update status fields in milestone and goal documents when the task requires it.
6. When ending a phase mid-stream, create a handover document in `Documentation/ImplementationPlans/`.

---

## IDE-Specific Agent Rules

 