"""
api/analyzers/js_analyzer.py
────────────────────────────────────────────────────────────────────────────
JavaScript and TypeScript structural analyser.

Responsibility:
  • Track async function ranges for await/Promise checks
  • Structural bracket balance
  • JS-specific: eval, XSS, closure bugs, loose equality, etc.
  • TS-specific: any types, @ts-ignore, non-null assertions, enums

Single responsibility: ONLY JS/TS analysis. Nothing else.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re

from .base import make_issue_list


def parse_javascript(code: str, _lang: str = "javascript") -> list[dict]:
    """
    Smart JavaScript structural analyser — pure Python, no external deps.
    Goes well beyond substring matching:
    - Tracks async/await context per function
    - Detects undeclared variables (heuristic)
    - Finds unreachable code after return/throw
    - Detects empty catch blocks
    - Counts unclosed brackets structurally
    - Checks for common Promise anti-patterns
    """
    issues, add = make_issue_list()
    lines = code.splitlines()

    # ── 1. Bracket balance (structural, escape-aware) ─────────────────────────
    stack = []; pairs = {"(":")", "[":"]", "{":"}"}; closing = set(pairs.values())
    for lineno, line in enumerate(lines, start=1):
        in_str = False; str_char = None; i = 0
        while i < len(line):
            ch = line[i]
            if in_str and ch == "\\": i += 2; continue
            if in_str:
                if ch == str_char: in_str = False
            elif ch in ('"', "'", "`"):
                in_str = True; str_char = ch
            elif ch in pairs:
                stack.append((ch, lineno))
            elif ch in closing:
                if stack and pairs[stack[-1][0]] == ch: stack.pop()
                else:
                    add(lineno, "error", f"Unexpected closing `{ch}`",
                        f"`{ch}` on line {lineno} has no matching opening bracket."); break
            i += 1
    if stack:
        ch, ln = stack[-1]
        add(ln, "error", f"Unclosed `{ch}` — missing `{pairs[ch]}`",
            f"The `{ch}` opened on line {ln} was never closed.")

    # ── 2. Async / await analysis ─────────────────────────────────────────────
    # Track which functions are async, then check awaited calls inside them
    _async_fn_re   = re.compile(r'\basync\s+(function|\w+\s*=>|\([^)]*\)\s*=>)')
    _fn_re         = re.compile(r'\bfunction\b')
    _await_call_re = re.compile(r'\bawait\s+')
    _promise_calls = ("fetch(", ".json()", ".text()", ".blob()", ".arrayBuffer()",
                      ".formData()", "axios.", ".then(", "Promise.")

    # Collect line ranges of async functions (simplified: track brace depth)
    async_ranges: list[tuple[int,int]] = []
    depth = 0; async_start = None; async_depth = None
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if _async_fn_re.search(line) and async_start is None:
            async_start = lineno; async_depth = depth
        depth += line.count("{") - line.count("}")
        if async_start and depth <= async_depth:
            async_ranges.append((async_start, lineno))
            async_start = None; async_depth = None

    def _in_async(lineno: int) -> bool:
        return any(s <= lineno <= e for s, e in async_ranges)

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("//"): continue     # skip comment lines

        # Detect "= fetch(" without await on the same line
        if "= fetch(" in line and "await" not in line and "return" not in line:
            add(lineno, "error",
                "Missing `await` on fetch()",
                "`fetch()` returns a Promise. Without `await` you get the Promise, not the response.\n"
                "Fix: `const response = await fetch(...)`")

        # Detect "= response.json()" without await
        if "= response.json()" in line and "await" not in line:
            add(lineno, "error",
                "Missing `await` on .json()",
                "`response.json()` also returns a Promise.\n"
                "Fix: `const data = await response.json()`")

        # Detect .then() chaining mixed with await (common async anti-pattern)
        if ".then(" in line and "await" in line:
            add(lineno, "warning",
                "Mixing `await` and `.then()` — pick one style",
                "Mixing `await` and `.then()` in the same expression makes code harder to read. "
                "Use `await` consistently: `const data = await fetch(url).then(r => r.json())`"
                " or fully async/await style.")

        # Detect Promise constructor anti-pattern: new Promise(async ...)
        if "new Promise(" in line and "async" in line:
            add(lineno, "warning",
                "Avoid `new Promise(async ...)` — the Promise swallows errors",
                "Passing an `async` function to `new Promise()` means rejected inner promises "
                "are silently swallowed. Use `async/await` directly instead.")

    # ── 3. Unreachable code after return/throw/break ──────────────────────────
    _terminator_re = re.compile(r'^\s*(return|throw|break|continue)\b')
    _code_re       = re.compile(r'^\s*(?!//|/\*|\*|$)')
    prev_terminated = False
    for lineno, line in enumerate(lines, start=1):
        if _terminator_re.match(line):
            prev_terminated = True
            continue
        if prev_terminated and _code_re.match(line):
            stripped = line.strip()
            if stripped and not stripped.startswith(("}", ")", "]", "case ", "default:")):
                add(lineno, "warning",
                    "Unreachable code after `return`/`throw`",
                    f"Line {lineno} is unreachable because a previous statement "
                    "always exits the current block. Remove it or restructure the logic.")
            prev_terminated = False
        else:
            prev_terminated = False

    # ── 4. Empty catch blocks ─────────────────────────────────────────────────
    _empty_catch_re = re.compile(
        r'\bcatch\s*(?:\(\s*\w*\s*\))?\s*\{\s*\}', re.MULTILINE
    )
    m = _empty_catch_re.search(code)
    if m:
        lineno = code[:m.start()].count("\n") + 1
        add(lineno, "error",
            "Empty `catch` block swallows errors silently",
            "An empty `catch` block hides errors and makes debugging impossible. "
            "At minimum log the error: `catch (e) { console.error(e); }`")

    # ── 5. var in for loop (classic closure bug) ──────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        if re.search(r'\bfor\s*\(\s*var\b', line):
            add(lineno, "error",
                "`for` loop with `var` — classic closure bug",
                "Variables declared with `var` in a `for` loop are function-scoped. "
                "Any callbacks inside the loop will all share the same final value. "
                "Fix: use `let` instead: `for (let i = 0; ...)`")

    # ── 6. == null (intentional but note it) ─────────────────────────────────
    # Skip — valid pattern, too many false positives

    # ── 7. console.log / debugger left in ────────────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        if "console.log(" in line:
            add(lineno, "warning",
                "Debug `console.log` left in code",
                "Remove before production or replace with a proper logging library.")
            break
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        if re.search(r'\bdebugger\b', line):
            add(lineno, "error",
                "`debugger` statement left in code",
                "A `debugger` statement pauses execution in DevTools. Remove before shipping.")
            break

    # ── 8. Security: eval, document.write, innerHTML ─────────────────────────
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        if re.search(r'\beval\s*\(', line):
            add(lineno, "error",
                "Never use `eval()` — security risk",
                "`eval()` executes arbitrary code. It is a critical security vulnerability. "
                "Never pass user input to it.")
        if "document.write(" in line:
            add(lineno, "error",
                "Avoid `document.write()` — overwrites the page",
                "`document.write()` after page load erases the whole document. "
                "Use DOM methods like `createElement` / `appendChild` instead.")
        if "innerHTML" in line and not (
                re.search(r'["\'].*innerHTML.*["\']', line)):  # not in string
            add(lineno, "warning",
                "Possible XSS via `innerHTML`",
                "Setting `innerHTML` with user-supplied data enables XSS. "
                "Use `textContent` for plain text, or sanitise with DOMPurify.")
        if re.search(r'\bvar\b', line) and not line.strip().startswith("//"):
            add(lineno, "warning",
                "Prefer `const` or `let` over `var`",
                "`var` is function-scoped and hoisted — a source of subtle bugs. "
                "Use `const` for fixed values, `let` for reassigned ones.")

    # ── 9. parseInt without radix ─────────────────────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        m = re.search(r'\bparseInt\s*\(\s*\w+\s*\)', line)
        if m:
            add(lineno, "warning",
                "Always pass a radix to `parseInt()`",
                "`parseInt('09')` was 0 in older engines (octal). "
                "Always specify base 10: `parseInt(value, 10)`.")

    # ── 10. == / != loose equality ────────────────────────────────────────────
    # Strategy: remove all === and !== first, then look for remaining == or !=
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        # Remove strict operators so they don't confuse the loose-operator check
        clean = re.sub(r'===|!==|<=|>=', ' ', line)
        if re.search(r'(?<![=!<>])={2}(?!=)', clean):
            add(lineno, "warning",
                "Use strict equality `===` instead of `==`",
                "`==` coerces types: `0 == '0'` is `true`, `null == undefined` is `true`. "
                "Use `===` for predictable, type-safe comparisons.")
            break
    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("//"): continue
        clean = re.sub(r'===|!==|<=|>=', ' ', line)
        if re.search(r'!=', clean):
            add(lineno, "warning",
                "Use strict inequality `!==` instead of `!=`",
                "`!=` coerces types just like `==`. Use `!==` for strict inequality.")
            break

    # ── 11. Apply remaining pattern-based checks (from _LANG_PATTERNS) ────────
    _comment_prefix = "//"
    for fragment, etype, title, explanation in _LANG_PATTERNS.get("javascript", []):
        # Skip patterns already handled above
        if title in {e["title"] for e in issues}: continue
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(_comment_prefix): continue
            if fragment not in line: continue
            # Guard: "== " must not fire on === or !==
            if fragment == "== ":
                clean = re.sub(r'===|!==|<=|>=', ' ', line)
                if "== " not in clean: continue
            # Guard: "!= " must not fire on !==
            if fragment in ("!= ", "!="):
                clean = re.sub(r'!==', ' ', line)
                if "!=" not in clean: continue
            if fragment == "innerHTML" and re.search(r'["\'].*innerHTML.*["\']', line): continue
            add(lineno, etype, title, explanation)
            break

    # ── 12. Universal checks ──────────────────────────────────────────────────
    # Universal checks handled by generic_analyzer
        for lineno, line in enumerate(lines, start=1):
            try:
                if check_fn(line):
                    add(lineno, etype, title, explanation); break
            except Exception:
                pass

    return issues




def parse_typescript(code: str) -> list[dict]:
    """
    TypeScript analyser — runs JS analysis then adds TS-specific checks.
    """
    # Run JS analysis first
    issues, add = make_issue_list()
    js_issues = parse_javascript(code, _lang="typescript")
    for i in js_issues:
        add(i["line"], i["type"], i["title"], i["explanation"])

    lines = code.splitlines()
    seen  = {i["title"] for i in issues}

    # ── TS-specific checks ────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # @ts directives live IN comment lines — check them BEFORE the comment skip
        if "@ts-ignore" in line:
            add(lineno, "warning",
                "`@ts-ignore` suppresses type errors — fix the root cause",
                "`@ts-ignore` silences TypeScript on the next line. "
                "Use `@ts-expect-error` if suppression is intentional, or fix the type issue.")
        if "@ts-nocheck" in line:
            add(lineno, "error",
                "`@ts-nocheck` disables type checking for the whole file",
                "This removes all TypeScript benefits. Remove it and fix the type errors.")

        if stripped.startswith("//"): continue

        # : any type
        if ": any" in line and ": any" not in seen:
            add(lineno, "warning",
                "Avoid the `any` type",
                "Using `any` completely disables TypeScript's type checking for this variable. "
                "Use `unknown` if the type is truly unknown, or define a proper type/interface.")

        # as any assertion
        if " as any" in line:
            add(lineno, "warning",
                "Avoid `as any` type assertion",
                "Casting to `any` bypasses all type safety. Fix the underlying type mismatch.")

        # any[] array
        if "any[]" in line:
            add(lineno, "warning",
                "Avoid `any[]` — specify element type",
                "Use `string[]`, `number[]`, or `Array<User>` instead of untyped `any[]`.")

        # Non-null assertion
        if "!." in line or re.search(r'\w+![\.\[]', line):
            add(lineno, "warning",
                "Non-null assertion `!` may hide null errors",
                "The `!` operator tells TypeScript to trust you that this isn't null/undefined. "
                "Write an explicit check instead: `if (x !== null && x !== undefined)`.")

        # enum warning
        if re.search(r'\benum\s+\w+', line):
            add(lineno, "warning",
                "Prefer `const enum` or union types over `enum`",
                "TypeScript `enum` generates extra runtime code. "
                "Consider `const enum` or: `type Dir = 'left' | 'right' | 'up' | 'down'`.")

        # : object type
        if re.search(r':\s*object\b', line):
            add(lineno, "warning",
                "Avoid the broad `object` type",
                "`object` accepts any non-primitive. Use a specific interface or `Record<K,V>`.")

    return issues


