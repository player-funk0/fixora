"""
api/analyzers/metrics.py
────────────────────────────────────────────────────────────────────────────
Codebase Metrics Calculator — like cloc but built-in.

Responsibility:
  • Count lines: total, code, blank, comment
  • Count functions, classes, imports
  • Estimate cyclomatic complexity (simple heuristic)
  • Compute per-language stats for the Project Statistics panel

Single responsibility: ONLY metrics calculation. Nothing else.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import ast
import re


# ── Per-submission code metrics ───────────────────────────────────────────────

def compute_code_metrics(code: str, language: str) -> dict:
    """
    Analyse a single code submission and return detailed metrics.

    Returns:
        {
            "lines":        int,   # total lines
            "code_lines":   int,   # non-blank, non-comment lines
            "blank_lines":  int,
            "comment_lines":int,
            "functions":    int,   # function/method definitions
            "classes":      int,   # class definitions
            "imports":      int,   # import statements
            "max_line_len": int,   # longest line
            "avg_line_len": float, # average line length (non-blank)
            "complexity":   int,   # cyclomatic complexity estimate
        }
    """
    lines = code.splitlines()
    total = len(lines)

    blank = sum(1 for l in lines if not l.strip())

    comment_lines = _count_comment_lines(lines, language)
    code_lines    = total - blank - comment_lines

    non_blank = [l for l in lines if l.strip()]
    avg_len   = round(sum(len(l) for l in non_blank) / len(non_blank), 1) if non_blank else 0.0
    max_len   = max((len(l) for l in lines), default=0)

    if language == "python":
        funcs, classes, imports, complexity = _python_metrics(code)
    else:
        funcs, classes, imports, complexity = _generic_metrics(lines, language)

    return {
        "lines":         total,
        "code_lines":    max(code_lines, 0),
        "blank_lines":   blank,
        "comment_lines": comment_lines,
        "functions":     funcs,
        "classes":       classes,
        "imports":       imports,
        "max_line_len":  max_len,
        "avg_line_len":  avg_len,
        "complexity":    complexity,
    }


def _count_comment_lines(lines: list[str], language: str) -> int:
    """Count comment lines based on language syntax."""
    count = 0
    in_block = False
    for line in lines:
        s = line.strip()
        if language == "python":
            if s.startswith("#") or s.startswith('"""') or s.startswith("'''"):
                count += 1
        elif language in ("html",):
            if s.startswith("<!--") or in_block:
                count += 1
                if "-->" in s: in_block = False
                elif "<!--" in s: in_block = True
        elif language == "css":
            if s.startswith("/*") or in_block:
                count += 1
                if "*/" in s: in_block = False
                elif "/*" in s: in_block = True
        else:  # C-style // and /* */
            if s.startswith("//") or s.startswith("*"):
                count += 1
            elif s.startswith("/*") or in_block:
                count += 1
                if "*/" in s: in_block = False
                elif "/*" in s: in_block = True
    return count


def _python_metrics(code: str) -> tuple[int, int, int, int]:
    """Use real AST for accurate Python metrics."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _generic_metrics(code.splitlines(), "python")

    funcs     = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    classes   = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    imports   = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)))

    # Cyclomatic complexity = decision points + 1
    # Decision points: if/elif/for/while/except/with/assert/comprehension
    decision_nodes = (
        ast.If, ast.For, ast.AsyncFor, ast.While,
        ast.ExceptHandler, ast.With, ast.AsyncWith,
        ast.Assert, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    )
    complexity = sum(1 for n in ast.walk(tree) if isinstance(n, decision_nodes)) + 1

    return funcs, classes, imports, complexity


def _generic_metrics(lines: list[str], language: str) -> tuple[int, int, int, int]:
    """Regex-based metrics for non-Python languages."""
    # Function patterns per language
    fn_patterns = {
        "javascript":  [r'\bfunction\b', r'=>\s*\{', r'\basync\s+function\b'],
        "typescript":  [r'\bfunction\b', r'=>\s*\{', r'\basync\s+function\b'],
        "java":        [r'(public|private|protected|static)\s+\w+\s+\w+\s*\('],
        "cpp":         [r'\b\w+\s+\w+\s*\([^)]*\)\s*(const\s*)?\{', r'^\s*\w+::'],
        "c":           [r'^\w[\w\s\*]+\s*\([^)]*\)\s*\{'],
        "go":          [r'\bfunc\s+\w+'],
        "rust":        [r'\bfn\s+\w+'],
        "csharp":      [r'(public|private|protected|internal|static)\s+\w+\s+\w+\s*\('],
        "ruby":        [r'^\s*def\s+\w+'],
    }
    cls_patterns = {
        "python":      [r'^\s*class\s+\w+'],
        "javascript":  [r'\bclass\s+\w+'],
        "typescript":  [r'\bclass\s+\w+', r'\binterface\s+\w+'],
        "java":        [r'\b(class|interface|enum)\s+\w+'],
        "cpp":         [r'\b(class|struct)\s+\w+'],
        "c":           [r'\bstruct\s+\w+'],
        "csharp":      [r'\b(class|interface|struct|enum)\s+\w+'],
        "ruby":        [r'^\s*class\s+\w+'],
        "go":          [r'\btype\s+\w+\s+(struct|interface)\b'],
        "rust":        [r'\b(struct|enum|trait|impl)\s+\w+'],
    }
    imp_patterns = {
        "javascript":  [r'\bimport\b', r'\brequire\('],
        "typescript":  [r'\bimport\b'],
        "java":        [r'^\s*import\s+'],
        "cpp":         [r'^\s*#include\s+'],
        "c":           [r'^\s*#include\s+'],
        "go":          [r'^\s*import\s+', r'"[\w/]+"'],
        "rust":        [r'^\s*use\s+'],
        "csharp":      [r'^\s*using\s+'],
        "ruby":        [r'^\s*require\b', r'^\s*require_relative\b'],
    }
    # Decision point keywords for complexity
    decision_kws = ["if ", "elif ", "else:", "for ", "while ", "switch ", "case ",
                    "catch ", "except ", "&&", "||", "? "]

    code = "\n".join(lines)
    count_pattern = lambda pats: sum(
        1 for line in lines for p in (pats or []) if re.search(p, line)
    )

    funcs     = count_pattern(fn_patterns.get(language, []))
    classes   = count_pattern(cls_patterns.get(language, []))
    imports   = count_pattern(imp_patterns.get(language, []))
    complexity = sum(1 for line in lines if any(kw in line for kw in decision_kws)) + 1

    return funcs, classes, imports, min(complexity, 200)


# ── Project-wide statistics (cloc-style) ─────────────────────────────────────

def compute_project_stats(file_paths: list[str]) -> dict:
    """
    Compute cloc-style stats across multiple files.

    Args:
        file_paths: list of absolute paths to source files

    Returns:
        {
            "total_files": int,
            "total_lines": int,
            "total_code":  int,
            "total_blank": int,
            "total_comments": int,
            "by_language": {
                "Python": {"files": 12, "lines": 1842, "code": 1100, ...},
                ...
            }
        }
    """
    from .constants import EXTENSION_TO_LANGUAGE, LANG_LABELS
    import os

    by_lang: dict[str, dict] = {}
    total_files = total_lines = total_code = total_blank = total_comments = 0

    for path in file_paths:
        _, ext = os.path.splitext(path)
        lang = EXTENSION_TO_LANGUAGE.get(ext.lower())
        if not lang:
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except OSError:
            continue

        m = compute_code_metrics(code, lang)
        label = LANG_LABELS.get(lang, lang.title())

        if label not in by_lang:
            by_lang[label] = {"files": 0, "lines": 0, "code": 0, "blank": 0, "comments": 0}

        by_lang[label]["files"]    += 1
        by_lang[label]["lines"]    += m["lines"]
        by_lang[label]["code"]     += m["code_lines"]
        by_lang[label]["blank"]    += m["blank_lines"]
        by_lang[label]["comments"] += m["comment_lines"]

        total_files    += 1
        total_lines    += m["lines"]
        total_code     += m["code_lines"]
        total_blank    += m["blank_lines"]
        total_comments += m["comment_lines"]

    return {
        "total_files":    total_files,
        "total_lines":    total_lines,
        "total_code":     total_code,
        "total_blank":    total_blank,
        "total_comments": total_comments,
        "by_language":    dict(sorted(by_lang.items(), key=lambda x: x[1]["lines"], reverse=True)),
    }
