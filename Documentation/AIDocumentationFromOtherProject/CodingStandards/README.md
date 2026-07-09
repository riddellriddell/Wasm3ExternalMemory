# Windsurf Rules Repository

A centralized collection of technology-specific coding standards and best practices for use with Windsurf AI assistant across multiple projects.

## Purpose & Goals

This repository contains curated coding rules that ensure consistency, maintainability, and best practices across different technology stacks. Rather than duplicating rule files across every project or relying on fragile filesystem links, we use Windsurf's persistent memory system to make these rules globally available.

### Our Goals
- **Consistency**: Apply the same high-quality standards across all projects
- **Maintainability**: Single source of truth for rules - update once, apply everywhere  
- **Efficiency**: No need to copy/paste rules between repositories
- **Quality**: Curated, reviewed, and battle-tested coding standards
- **Flexibility**: Technology-specific rules that adapt to your current context

## Technology Coverage

### Current Rules Files

- **`csharp_rules.md`** - Microsoft C# conventions with team modifications
  - Modern C# features, async/await patterns, naming conventions
  - Allman braces, parameter prefixes (`in_`), SOLID principles
  
- **`cplusplus_rules.md`** - Unreal Engine C++ best practices  
  - UE5 coding standards, UHT/UBT compliance, Epic naming conventions
  - Memory management, reflection macros, Blueprint integration

- **`wpf_rules.md`** - WPF/XAML coding standards
  - MVVM patterns, dependency properties, resource management
  - XAML formatting, virtualization, binding best practices

- **`qt_rules.md`** - Qt C++ for Windows development
  - Qt6 + CMake, signals/slots, threading, container usage
  - OpenRGB plugin-specific guidance, MSVC toolchain settings

## How It Works: Assistant Memory System

### Why Not Traditional Approaches?

We explored several options for sharing rules across projects:

- ❌ **Copy/paste files** - Creates maintenance nightmare, rules drift apart
- ❌ **Git submodules** - Complex, requires setup in every repo  
- ❌ **Filesystem junctions** - Windows-specific, breaks on different machines
- ❌ **Git subtrees** - Manual sync required, easy to forget updates

### ✅ Assistant Memory Approach

Instead, we use Windsurf's persistent memory system:

1. **Global Storage**: Rules are stored as persistent memories in the assistant
2. **Auto-Detection**: Assistant detects technology stack and applies relevant rules
3. **Cross-Project**: Works in any workspace without setup
4. **Precedence**: Local repo rules override global memories when present
5. **Easy Updates**: Send new content or URLs to update memories instantly

## Getting Started

### For Rule Authors

1. **Create/Edit Rules**: Write your rules in clear, actionable markdown
2. **Review & Test**: Validate rules work in real projects  
3. **Commit to Memory**: Tell the assistant to save them globally

### For Developers Using Rules

#### Initial Setup
Share the rule content with Windsurf assistant:

```
Here are my [Technology] rules: [paste content or share raw GitHub URL]
Please save these as global Rules: [Technology] memory.
```

#### Examples
```
"Save these C# rules as global memory: Rules: CSharp"
"Update Rules: Qt from this URL: https://raw.githubusercontent.com/..."
"Apply my WPF rules to this project"
```

#### Management Commands
```
"List my global rules"                    # See what's stored
"Update Rules: CSharp with this content"  # Update existing rules  
"Disable Rules: Qt for this repo"         # Override for specific project
"Delete Rules: [Technology]"              # Remove rule set
```

### Why This Workflow?

**Assistant Context Limits**: Windsurf has limited context windows. All conversation history gets cleared periodically, so rules stored only in chat would be lost.

**Persistent Memory**: By saving rules as memories, they persist across:
- Different conversations
- Different projects  
- Different sessions
- Context window resets

**Automatic Retrieval**: The assistant automatically loads relevant rule memories based on detected file types and project structure.

## Rule File Structure

Each rule file should follow this pattern:

```markdown
# [Technology] Coding Rules

## Scope
- Target audience and use cases
- When these rules apply

## [Specific Sections]
- Language features
- Naming conventions  
- Formatting rules
- Best practices
- Anti-patterns to avoid

## Examples
- Code samples showing correct usage
- Before/after comparisons

## Tooling
- Recommended tools and configurations
- CI/CD integration
```

## Contributing

1. **Fork & Edit**: Make changes to rule files
2. **Test**: Validate rules in real projects
3. **PR**: Submit with rationale and examples
4. **Memory Update**: After merge, update assistant memories:
   ```
   "Update Rules: [Technology] from https://raw.githubusercontent.com/JarrydSemmens/windsurf_rules/main/[technology]_rules.md"
   ```

## Maintenance

### Updating Rules
- Edit files in this repository
- Tell assistant to update memories from new URLs
- Assistant will diff and apply changes automatically

### Version Control
- Each rule file includes version and date headers
- Git history provides full change tracking
- Assistant memories can reference specific versions

## FAQ

**Q: Do I need to copy these files to every project?**  
A: No! Once stored in assistant memory, they work globally.

**Q: What if I want project-specific overrides?**  
A: Create `.windsurf/rules/` in your project - local rules take precedence.

**Q: How do I know which rules are active?**  
A: Ask the assistant: "What rules are you using for this project?"

**Q: Can I use multiple rule sets together?**  
A: Yes! The assistant can apply multiple relevant rule sets (e.g., C# + WPF).

**Q: What if the assistant forgets my rules?**  
A: Memories are persistent, but you can always re-share the GitHub raw URL to refresh them.

---

**Repository**: https://github.com/JarrydSemmens/windsurf_rules  
**Owner**: Jarryd Adaens  
**Last Updated**: 2025-08-24
