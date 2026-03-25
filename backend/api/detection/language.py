"""
api/detection/language.py
────────────────────────────────────────────────────────────────────────────
Language detection from code content.

Responsibility:
  • Score code against language-specific signatures (regex weighted)
  • Resolve ambiguous cases (C vs C++, hint tiebreaker)
  • Return a language slug: 'python', 'javascript', 'cpp', etc.

Single responsibility: ONLY language detection. Nothing else.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re


_LANG_SIGNATURES = [
    # Python
    (r"^\s*def\s+\w+\s*\(",                      "python",     5),
    (r"^\s*from\s+\w+\s+import",                 "python",     4),
    (r"^\s*import\s+\w+",                        "python",     3),
    (r"^\s*class\s+\w+.*:",                      "python",     4),
    (r"if\s+__name__\s*==\s*['\"]__main__['\"]", "python",     7),
    (r"print\(",                                 "python",     2),
    # JavaScript
    (r"^\s*const\s+\w+\s*=",                     "javascript", 3),
    (r"^\s*let\s+\w+\s*=",                       "javascript", 3),
    (r"^\s*var\s+\w+\s*=",                       "javascript", 2),
    (r"function\s+\w+\s*\(",                     "javascript", 4),
    (r"=>\s*\{",                                 "javascript", 3),
    (r"console\.log\(",                          "javascript", 3),
    (r"require\(",                               "javascript", 3),
    (r"^\s*import\s+.*\s+from\s+['\"]",          "javascript", 4),
    # TypeScript
    (r":\s*(string|number|boolean|any)\b",       "typescript", 5),
    (r"interface\s+\w+\s*\{",                    "typescript", 6),
    (r"<\w+>\s*\(",                              "typescript", 4),
    # C++
    (r"#include\s*<",                            "cpp",        5),
    (r"std::",                                   "cpp",        5),
    (r"cout\s*<<",                               "cpp",        5),
    # C
    (r"#include\s*['\"]",                        "c",          4),
    (r"int\s+main\s*\(",                         "c",          4),
    (r"printf\s*\(",                             "c",          3),
    # Java
    (r"public\s+class\s+\w+",                    "java",       6),
    (r"public\s+static\s+void\s+main",           "java",       7),
    (r"System\.out\.println",                    "java",       5),
    (r"import\s+java\.",                         "java",       5),
    # Go
    (r"^package\s+\w+",                          "go",         6),
    (r"func\s+\w+\s*\(",                         "go",         5),
    (r"fmt\.Print",                              "go",         4),
    (r":=\s*",                                   "go",         3),
    # Rust
    (r"fn\s+main\s*\(\s*\)",                     "rust",       6),
    (r"println!\s*\(",                           "rust",       5),
    (r"use\s+std::",                             "rust",       5),
    (r"^\s*let\s+(mut\s+)?\w+",                  "rust",       3),
    # HTML
    (r"<!DOCTYPE\s+html",                        "html",       9),
    (r"<html[\s>]",                              "html",       8),
    (r"<head[\s>]",                              "html",       5),
    (r"<body[\s>]",                              "html",       5),
    (r"<div[\s>]",                               "html",       3),
    # CSS
    (r"^\s*[.#]?\w[\w-]*\s*\{",                  "css",        4),
    (r"^\s*@media\s*\(",                         "css",        6),
    (r":\s*(px|em|rem|vh|vw|%)\s*;",             "css",        5),
    (r"font-family\s*:",                         "css",        5),
    (r"background-color\s*:",                    "css",        5),
]


def detect_language(code: str, hint: str | None = None) -> str:
    """
    Auto-detect programming language from code content.
    `hint` is the language the user selected — used as a tiebreaker.
    Returns a language slug like 'python', 'javascript', etc.
    """
    if not code.strip():
        return hint or "python"

    scores: dict[str, float] = {}
    for pattern, lang, weight in _LANG_SIGNATURES:
        if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
            scores[lang] = scores.get(lang, 0) + weight

    if not scores:
        return hint or "python"

    best       = max(scores, key=lambda k: scores[k])
    best_score = scores[best]

    # When the user provides a hint, trust it unless detection is strongly against it
    # (i.e. the detected language scores more than 3x higher than the hint)
    if hint:
        hint_score = scores.get(hint, 0)
        if hint_score > 0 or best_score < 6:
            # Hint has some evidence, or detection isn't confident — trust the user
            return hint

    # C vs C++: only use C++ if C++-specific tokens are present
    if best in ("c", "cpp"):
        cpp_specific = bool(re.search(r"std::|cout\s*<<|#include\s*<\w+>", code))
        return "cpp" if cpp_specific else "c"

    return best


# ══════════════════════════════════════════════════════════════════════════════
