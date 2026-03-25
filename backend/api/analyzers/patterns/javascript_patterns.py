"""
api/analyzers/patterns/javascript_patterns.py
──────────────────────────────────────────────
Pattern rules for JavaScript.
Each rule: (fragment, type, title, explanation)
  fragment    — substring to search for in a line
  type        — "error" | "warning"
  title       — short label shown in the UI
  explanation — full explanation shown on expand
"""

PATTERNS: list[tuple] = [
    # ── Async / Promise ──────────────────────────────────────────
    ("= fetch(",           "error",
     "Missing `await` on fetch()",
     "`fetch()` returns a Promise. Without `await` you get the Promise object, not data. "
     "Fix: `const response = await fetch(...)`"),

    ("= response.json()",  "error",
     "Missing `await` on .json()",
     "`response.json()` also returns a Promise. Fix: `const data = await response.json()`"),

    ("= response.text()",  "error",
     "Missing `await` on .text()",
     "`response.text()` returns a Promise. Use: `const text = await response.text()`"),

    ("new Promise(resolve, reject", "error",
     "Promise constructor arguments wrong",
     "The Promise constructor takes a single executor: `new Promise((resolve, reject) => ...)`. "
     "`resolve` and `reject` must be inside the arrow function, not separate arguments."),

    # ── Variables & scope ─────────────────────────────────────────
    ("var ",               "warning",
     "Prefer `const` or `let` over `var`",
     "`var` is function-scoped and hoisted — a source of subtle bugs. "
     "Use `const` for values that don't change, `let` for those that do."),

    ("for (var ",          "error",
     "`for` loop with `var` causes closure bug",
     "Variables declared with `var` in a `for` loop are function-scoped, not block-scoped. "
     "This causes the classic closure bug in callbacks. "
     "Use `let` instead: `for (let i = 0; ...)`."),

    # ── Equality ─────────────────────────────────────────────────
    ("== ",                "warning",
     "Use strict equality `===` instead of `==`",
     "`==` coerces types: `0 == '0'` is `true`, `null == undefined` is `true`. "
     "Use `===` for predictable, type-safe comparisons."),

    ("!= ",                "warning",
     "Use strict inequality `!==` instead of `!=`",
     "`!=` coerces types just like `==`. Use `!==` for strict inequality."),

    # ── Security ─────────────────────────────────────────────────
    ("eval(",              "error",
     "Never use `eval()` — security risk",
     "`eval()` executes arbitrary code strings and is a critical security vulnerability. "
     "Never pass user input to it. Use `JSON.parse()` for JSON, or refactor the logic."),

    ("innerHTML",          "warning",
     "Possible XSS via `innerHTML`",
     "Setting `innerHTML` with user-supplied data enables Cross-Site Scripting (XSS). "
     "Use `textContent` for plain text, or `DOMPurify.sanitize()` before inserting HTML."),

    ("document.write(",    "error",
     "Avoid `document.write()` — overwrites the page",
     "`document.write()` after page load erases the entire document. "
     "Use DOM methods like `createElement` and `appendChild` instead."),

    ('setTimeout("',       "error",
     "`setTimeout` with a string argument is like `eval()`",
     "Passing a string to `setTimeout` evaluates it as code — same risks as `eval()`. "
     "Always pass a function: `setTimeout(() => foo(), 1000)`."),

    # ── Debug artifacts ───────────────────────────────────────────
    ("console.log",        "warning",
     "Debug `console.log` left in code",
     "Remove `console.log` before production or replace with a logging library."),

    ("debugger",           "error",
     "`debugger` statement left in code",
     "A `debugger` statement pauses execution in DevTools. Remove before shipping."),

    # ── Common pitfalls ───────────────────────────────────────────
    ("parseInt(",          "warning",
     "Always pass a radix to `parseInt()`",
     "`parseInt('09')` returns 9 in modern JS but was 0 in old engines (octal). "
     "Always specify base 10: `parseInt(value, 10)`."),

    ("isNaN(",             "warning",
     "Prefer `Number.isNaN()` over global `isNaN()`",
     "Global `isNaN('hello')` returns `true` after coercion. "
     "`Number.isNaN('hello')` returns `false` — correct behaviour."),

    ("delete ",            "warning",
     "Avoid `delete` on object properties in hot paths",
     "`delete` makes JavaScript engines deoptimise the object's hidden class. "
     "Set the property to `undefined` or `null` instead if performance matters."),
]
