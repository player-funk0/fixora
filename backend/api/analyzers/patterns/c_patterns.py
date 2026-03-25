"""
api/analyzers/patterns/c_patterns.py
─────────────────────────────────────
Pattern rules for C and C++.
C++ also uses all C patterns, plus cpp_extras below.
"""

# ── C patterns (shared by both C and C++) ────────────────────────────────────
C_PATTERNS: list[tuple] = [
    ("<=",                 "error",
     "Off-by-one — array access out of bounds",
     "Array of N elements: valid indices 0 to N-1. "
     "`i <= N` accesses index N — undefined behaviour. Use `<`."),

    ("gets(",              "error",
     "Never use `gets()` — buffer overflow",
     "`gets()` has no bounds checking and was removed in C11. "
     "Use `fgets(buf, sizeof(buf), stdin)`."),

    ("strcpy(",            "warning",
     "Prefer `strncpy()` over `strcpy()`",
     "`strcpy()` can overflow if source is longer than destination. "
     "Use `strncpy(dest, src, sizeof(dest) - 1)` and manually null-terminate."),

    ("strcat(",            "warning",
     "Prefer `strncat()` over `strcat()`",
     "`strcat()` can overflow. Use `strncat(dest, src, sizeof(dest) - strlen(dest) - 1)`."),

    ("sprintf(",           "warning",
     "Prefer `snprintf()` over `sprintf()`",
     "`sprintf()` can overflow the destination buffer. "
     "Use `snprintf(buf, sizeof(buf), fmt, ...)` to limit output length."),

    ("scanf(",             "warning",
     "Limit `scanf` input width to prevent overflow",
     "Unlimited `%s` in `scanf` overflows the buffer. "
     "Use `scanf(\"%255s\", buf)` to limit length."),

    ("malloc(",            "warning",
     "Check `malloc()` return value for NULL",
     "`malloc` returns `NULL` if allocation fails. "
     "Always check: `if (ptr == NULL) { /* handle */ }` before using the pointer."),

    ("free(",              "warning",
     "Set pointer to NULL after `free()`",
     "After `free(ptr)`, the pointer is dangling. "
     "Set it to `NULL` immediately: `free(ptr); ptr = NULL;` to avoid use-after-free."),

    ("realloc(",           "warning",
     "Don't assign `realloc()` directly to the original pointer",
     "`realloc` returns `NULL` on failure, losing the original pointer. "
     "Use: `tmp = realloc(ptr, size); if (tmp) ptr = tmp;`"),

    ("strcmp(",            "warning",
     "Check `strcmp()` return value correctly",
     "`strcmp()` returns 0 when equal, not `true`. "
     "Use `if (strcmp(a, b) == 0)` not `if (strcmp(a, b))` to check equality."),
]

# ── C++-specific extras ───────────────────────────────────────────────────────
CPP_EXTRAS: list[tuple] = [
    ("<=",                 "error",
     "Off-by-one — array access out of bounds",
     "Arrays of size N have valid indices 0 to N-1. "
     "`i <= N` accesses index N — out of bounds (undefined behaviour). Use `<`."),

    ("using namespace std","warning",
     "Avoid `using namespace std`",
     "Pollutes the global namespace and causes name collisions. "
     "Prefer explicit `std::cout`, `std::vector`, etc. or limit to local scope."),

    ("printf(",            "warning",
     "Prefer `std::cout` over `printf`",
     "`printf` is not type-safe in C++. Use `std::cout` or `std::format` (C++20)."),

    ("new ",               "warning",
     "Prefer smart pointers over raw `new`",
     "Raw `new`/`delete` leads to memory leaks. "
     "Use `std::unique_ptr` or `std::shared_ptr`."),

    ("delete ",            "warning",
     "Check `delete` matches every `new`",
     "Every `new` must have exactly one matching `delete`. "
     "Mismatches cause leaks or double-free. Prefer smart pointers."),

    ("malloc(",            "warning",
     "Prefer `new` or smart pointers over `malloc` in C++",
     "`malloc` does not call constructors. Use `new` or `std::make_unique<T>()` in C++."),

    ("NULL",               "warning",
     "Use `nullptr` instead of `NULL` in C++",
     "`NULL` is typically `0` (an integer). "
     "`nullptr` is a proper pointer literal — prevents accidental integer comparisons."),

    ("catch(...)",         "warning",
     "Avoid catching `...` (all exceptions)",
     "Catching `...` swallows every exception including system errors. "
     "Catch specific exception types you can handle."),

    ("#define ",           "warning",
     "Prefer `const`/`constexpr` over `#define` for constants",
     "`#define` macros have no type safety and no scope. "
     "Use `constexpr int MAX = 100;` instead."),

    ("void* ",             "warning",
     "Avoid `void*` — use templates or `std::any`",
     "`void*` loses type information and requires unsafe casts. "
     "Use templates, `std::any`, or `std::variant` for type-safe polymorphism."),

    ("endl",               "warning",
     "Prefer `'\\n'` over `std::endl`",
     "`std::endl` flushes the stream buffer — slow. "
     "Use `'\\n'` unless you need an explicit flush."),
]

# Exported: C gets C_PATTERNS, C++ gets CPP_EXTRAS (which already covers <=)
PATTERNS_C   = C_PATTERNS
PATTERNS_CPP = CPP_EXTRAS
