"""
api/analyzers/generic_analyzer.py
────────────────────────────────────────────────────────────────────────────
Structural + pattern analyser for all non-Python, non-JS languages.
Patterns are imported from api/analyzers/patterns/ — one file per language.

Responsibility:
  • Bracket balance, deep nesting, empty blocks (structural)
  • Route each language through its pattern file (patterns/)
  • Apply universal checks (long lines, TODO, secrets)

Single responsibility: ONLY generic multi-language analysis engine.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re

from .base import make_issue_list
from .patterns import LANG_PATTERNS, UNIVERSAL_CHECKS


def parse_generic(code: str, language: str = "") -> list[dict]:
    """
    Structural + pattern analysis for C, C++, Java, Go, Rust, C#, Ruby, HTML, CSS.
    """
    issues, add = make_issue_list()
    lines = code.splitlines()

    # ── Bracket matching ───────────────────────────────────────────────────────
    stack   = []
    pairs   = {"(": ")", "[": "]", "{": "}"}
    closing = set(pairs.values())
    for lineno, line in enumerate(lines, start=1):
        in_str = False; str_char = None; i = 0
        while i < len(line):
            ch = line[i]
            if in_str and ch == "\\": i += 2; continue
            if in_str:
                if ch == str_char: in_str = False
            elif ch in ('"', "'"):
                in_str = True; str_char = ch
            elif ch in pairs:
                stack.append((ch, lineno))
            elif ch in closing:
                if stack and pairs[stack[-1][0]] == ch:
                    stack.pop()
                else:
                    add(lineno, "error",
                        f"Unexpected closing `{ch}`",
                        f"Found `{ch}` on line {lineno} with no matching opening bracket.")
                    break
            i += 1
    if stack:
        ch, lineno = stack[-1]
        add(lineno, "error",
            f"Unclosed `{ch}` — missing `{pairs[ch]}`",
            f"The `{ch}` opened on line {lineno} was never closed.")

    # ── Deep nesting ───────────────────────────────────────────────────────────
    max_depth = 0; max_lineno = 1
    for lineno, line in enumerate(lines, start=1):
        if not line.strip(): continue
        stripped = line.lstrip()
        leading  = line[:len(line) - len(stripped)]
        depth    = leading.count("\t") + (len(leading) - leading.count("\t")) // 4
        if depth > max_depth: max_depth = depth; max_lineno = lineno
    if max_depth >= 5:
        add(max_lineno, "warning",
            f"Deep nesting ({max_depth} levels)",
            f"Code nested {max_depth} levels deep is hard to read. "
            "Extract inner blocks into functions or use early returns.")

    # ── Empty C-style blocks ───────────────────────────────────────────────────
    if language not in ("html", "css"):
        for lineno, line in enumerate(lines, start=1):
            if line.strip() in ("{}", "{ }"):
                add(lineno, "warning",
                    "Empty code block `{}`",
                    "An empty `{}` may indicate unfinished code. "
                    "Add a comment explaining why it's empty if intentional.")

    # ── Language-specific patterns ─────────────────────────────────────────────
    _comment_chars = {
        "javascript": "//", "typescript": "//", "java": "//",
        "cpp": "//", "c": "//", "csharp": "//", "go": "//", "rust": "//",
    }
    _comment_prefix = _comment_chars.get(language, "")
    _ts_directives  = {"@ts-ignore", "@ts-nocheck", "@ts-expect-error"}

    for fragment, etype, title, explanation in LANG_PATTERNS.get(language, []):
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip comment lines — but not TypeScript directives (they live in comments)
            if _comment_prefix and stripped.startswith(_comment_prefix):
                if not any(d in stripped for d in _ts_directives):
                    continue

            if fragment not in line:
                continue

            # Smart guards: prevent false positives ───────────────────────────
            if fragment == "<img " and "alt=" in line:
                continue
            if fragment == "font-size:" and "px" not in line:
                continue
            if fragment == "font-family:" and any(
                    g in line for g in ("sans-serif", "serif", "monospace", "cursive", "fantasy")):
                continue
            if fragment == 'target="_blank"' and "noopener" in line:
                continue
            if fragment == "gets(" and re.search(r'\b(?:f|s|w)gets\s*\(', line):
                continue
            if fragment == "<=" and (
                    re.search(r'"[^"]*<=[^"]*"', line) or re.search(r"'[^']*<=[^']*'", line)):
                continue
            if fragment == "innerHTML" and (
                    re.search(r'"[^"]*innerHTML[^"]*"', line) or
                    re.search(r"'[^']*innerHTML[^']*'", line) or
                    re.search(r"`[^`]*innerHTML[^`]*`", line)):
                continue
            if fragment == "= fetch(" and re.search(r'["\'].*= fetch\(.*["\']', line):
                continue

            add(lineno, etype, title, explanation)
            break

    # ── Universal checks ───────────────────────────────────────────────────────
    for check_fn, etype, title, explanation in UNIVERSAL_CHECKS:
        for lineno, line in enumerate(lines, start=1):
            try:
                if check_fn(line):
                    add(lineno, etype, title, explanation)
                    break
            except Exception:
                pass

    return issues
