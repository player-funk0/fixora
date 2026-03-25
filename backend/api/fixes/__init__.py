"""
api/fixes/
──────────
Report generation and (future) auto-fix suggestions.

  report_generator — summary, correctedCode, hints
"""
from .report_generator import _generate_summary, _generate_corrected_code

__all__ = ["_generate_summary", "_generate_corrected_code"]
