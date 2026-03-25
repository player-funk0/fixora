"""
api/orchestrator.py
────────────────────────────────────────────────────────────────────────────
Fixora Analysis Orchestrator — the single entry point.

Responsibility:
  • Receive (code, language, learning_mode)
  • Detect language → select parser → run analysis → generate report + metrics
  • Return the unified JSON result

Pipeline:
  User Code
      ↓
  [1] detection.language.detect_language()
      ↓
  [2] _select_parser()
      ↓
  [3] analyser(code)            → list[Issue]
      ↓
  [4] metrics.compute_code_metrics()  → dict
      ↓
  [5] fixes.report_generator.*  → summary + correctedCode + hints
      ↓
  [6] dict response (new contract: errors, warnings, fixes, metrics)
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import random
import time

from .detection.language import detect_language
from .analyzers.python_analyzer import _parse_python
from .analyzers.js_analyzer import parse_javascript, parse_typescript
from .analyzers.generic_analyzer import parse_generic
from .analyzers.metrics import compute_code_metrics
from .fixes.report_generator import (
    _generate_summary,
    _generate_corrected_code,
    _LEARNING_HINTS,
    _GENERIC_HINTS,
)


# ── Parser router ─────────────────────────────────────────────────────────────

def _select_parser(language: str):
    """Map language slug → analysis function."""
    _PARSER_MAP = {
        "python":     _parse_python,
        "javascript": parse_javascript,
        "typescript": parse_typescript,
    }
    return _PARSER_MAP.get(language, parse_generic)


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze(
    code: str,
    language: str,
    learning_mode: bool,
) -> tuple[dict, int]:
    """
    Full Fixora analysis pipeline.

    Returns (result_dict, elapsed_ms).

    API contract (v2):
    {
        "language":       str,           # detected language slug
        "summary":        str,           # human-readable summary sentence
        "errorCount":     int,
        "warningCount":   int,
        "errors":         list[Issue],   # type, line, title, explanation
        "fixes":          list[Fix],     # future: auto-fix suggestions
        "correctedCode":  str,
        "hints":          list[str],     # learning mode only
        "showCorrection": bool,
        "detectedLanguage": str,
        "metrics": {
            "lines":         int,
            "code_lines":    int,
            "blank_lines":   int,
            "comment_lines": int,
            "functions":     int,
            "classes":       int,
            "imports":       int,
            "max_line_len":  int,
            "avg_line_len":  float,
            "complexity":    int,
        }
    }
    """
    t0 = time.monotonic()
    time.sleep(random.uniform(0.2, 0.6))

    # Step 1 — Detect language
    detected = detect_language(code, hint=language)

    # Step 2 — Select parser
    parser = _select_parser(detected)

    # Step 3 — Run analysis
    issues = parser(code) if detected in ("python", "javascript", "typescript") else parser(code, detected)

    # Step 4 — Compute code metrics
    metrics = compute_code_metrics(code, detected)

    # Step 5 — Generate report
    err_cnt  = sum(1 for i in issues if i["type"] == "error")
    warn_cnt = sum(1 for i in issues if i["type"] == "warning")
    summary  = _generate_summary(detected, issues)

    # Step 6 — Build response (v2 contract)
    base = {
        "language":         detected,          # top-level for convenience
        "detectedLanguage": detected,          # kept for backwards compat
        "summary":          summary,
        "errorCount":       err_cnt,
        "warningCount":     warn_cnt,
        "errors":           issues,
        "fixes":            [],                # placeholder — Auto-Fix coming
        "showCorrection":   not learning_mode,
        "metrics":          metrics,
    }

    if learning_mode:
        hints = _LEARNING_HINTS.get(detected, _GENERIC_HINTS)[:]
        random.shuffle(hints)
        base.update({
            "correctedCode": "",
            "hints":         hints,
        })
    else:
        base.update({
            "correctedCode": _generate_corrected_code(code, detected, issues),
            "hints":         [],
        })

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return base, elapsed_ms
