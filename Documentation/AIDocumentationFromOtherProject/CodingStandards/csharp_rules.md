Version: 1.0
Date Created: 5:31 PM 24/08/2025
Last Edit Date: 5:45 PM 24/08/2025
Owner: "Jarryd Adaens"

# C# Coding Rules
- We use Microsoft's C# coding conventions with some modifications.

## Scope
- Applies to all C# in this workspace.
- Intent: readability, consistency, modern C#.

## Language
- Prefer modern features. Avoid obsolete constructs.
- Catch only exceptions you can handle. Don’t catch `System.Exception` without a filter.
- Use async/await for I/O-bound work.
- Use C# keywords for built-in types: `string`, `int`, etc. (incl. `nint`, `nuint`).
- Use `int` unless unsigned semantics are required.
- Use `var` only when the RHS makes the type obvious; otherwise spell the type.
- Prefer string interpolation; use `StringBuilder` for large/loop appends. Prefer raw string literals when helpful.
- Use `using` statements (including declaration form) instead of `try/finally` for `Dispose`.
- Use `&&` and `||` for comparisons (short-circuit).
- Use concise `new()` forms when the variable type matches. Use object/collection initializers.
- Use lambdas for event handlers you won’t remove.
- Call static members via the type name.
- LINQ: meaningful range/result names, alias anonymous properties, rename ambiguous properties; use implicit typing in queries.

## Using directives
- Place `using` directives **outside** namespaces. Use `global::` if needed.

## Style and Layout
- Indent with 4 spaces. No tabs.
- Allman braces: `{` and `}` on their own lines.
- One statement per line. One declaration per line.
- Add a blank line between members. Indent continuation lines by one level.
- Use parentheses to make precedence clear when needed.

## Comments
- Use `//` for short explanations. Avoid block comments for long prose; move prose to docs.
- XML doc comments for public APIs. Start with uppercase, end with a period; one space after `//`.

## Naming
- PascalCase: namespaces, types, all public/protected members, and local functions.
- Interfaces start with `I`; attribute types end with `Attribute`.
- Enums: singular for non-flags; plural for flags.
- Avoid `__` (double underscore); reserved for compiler. Prefer clear, descriptive names. Avoid unclear acronyms.
- Locals: camelCase.
- Constants: **PascalCase** (fields and local const).
- Private instance fields: `_camelCase`. Private/internal static fields: `s_`. Thread-static: `t_`.
- Primary constructors: classes/structs use camelCase parameters; records use PascalCase (they become public props).
- Avoid single-letter names except simple loop counters.
- Parameters: camelCase with the prefix `in_`.

## Do Not

- Don’t place using inside namespaces.
- Don’t overuse var when the type is unclear.
- Don’t catch broad exceptions without handling.

## Examples (concise)
```csharp
// Using directives
using System.Text;

// Naming + fields
public class DataService(IWorkerQueue in_workerQueue, ILogger in_logger)
{
    private static IWorkerQueue s_fallbackQueue;
    private IWorkerQueue _workerQueue = in_workerQueue;

    public ILogger Logger { get; } = in_logger;

    public async Task<string> LoadAsync(string in_id)
    {
        // var only when obvious
        var sb = new StringBuilder();
        sb.Append($"{Logger?.GetType().Name}: {in_id}");
        using var stream = await FetchAsync(in_id).ConfigureAwait(false);
        return sb.ToString();
    }
}

``` 
