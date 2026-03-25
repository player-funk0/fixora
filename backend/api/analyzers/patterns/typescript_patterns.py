"""
api/analyzers/patterns/typescript_patterns.py
──────────────────────────────────────────────
Pattern rules for TypeScript.
TypeScript inherits all JavaScript patterns PLUS these TS-specific ones.
"""

PATTERNS: list[tuple] = [
    # ── Type safety ───────────────────────────────────────────────
    (": any",              "warning",
     "Avoid the `any` type",
     "Using `any` disables TypeScript's type checking entirely. "
     "Use `unknown` if the type is truly unknown, or a proper type/generic."),

    ("as any",             "warning",
     "Avoid `as any` type assertion",
     "Casting to `any` bypasses type safety. Fix the underlying type mismatch instead."),

    ("any[]",              "warning",
     "Avoid `any[]` — specify element type",
     "Use `string[]`, `number[]`, `User[]`, or `Array<T>` for type safety."),

    (": object",           "warning",
     "Avoid the broad `object` type",
     "`object` accepts anything non-primitive. "
     "Use a specific interface or `Record<K,V>` instead."),

    # ── Null safety ───────────────────────────────────────────────
    ("!.",                 "warning",
     "Non-null assertion `!` may hide null errors",
     "The `!` operator tells TypeScript to ignore null/undefined. "
     "Write an explicit check: `if (x !== null && x !== undefined)` instead."),

    ("!)",                 "warning",
     "Non-null assertion `!` on expression",
     "Using `!` silences TypeScript's null checks. "
     "Use optional chaining `?.` or an explicit null check instead."),

    # ── Async ─────────────────────────────────────────────────────
    ("= fetch(",           "error",
     "Missing `await` on async call",
     "Without `await` you're working with the Promise object, not its resolved value."),

    ("= response.json()",  "error",
     "Missing `await` on .json()",
     "`response.json()` returns a Promise. Use `await response.json()`."),

    # ── Enums & directives ────────────────────────────────────────
    ("enum ",              "warning",
     "Prefer `const enum` or union types over `enum`",
     "TypeScript `enum` generates extra JavaScript code and can have surprising runtime behaviour. "
     "Consider `const enum` for compile-time enums, or a union type: `type Dir = 'left'|'right'`."),

    ("@ts-ignore",         "warning",
     "`@ts-ignore` suppresses type errors — fix the root cause",
     "`@ts-ignore` silences TypeScript on the next line. "
     "Use `@ts-expect-error` if suppression is intentional, or fix the underlying type issue."),

    ("@ts-nocheck",        "error",
     "`@ts-nocheck` disables type checking for the whole file",
     "This disables all TypeScript benefits. Remove it and fix the type errors properly."),
]
