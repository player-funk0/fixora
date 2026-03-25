"""
api/analyzers/
──────────────
Per-language analysis engines.

  python_analyzer   — real Python AST analysis
  js_analyzer       — JavaScript + TypeScript structural analysis
  generic_analyzer  — C, C++, Java, Go, Rust, C#, Ruby, HTML, CSS
  constants         — shared language metadata
  base              — shared make_issue_list() factory
"""
from .python_analyzer import _parse_python as analyse_python
from .js_analyzer     import parse_javascript, parse_typescript
from .generic_analyzer import parse_generic

__all__ = ["analyse_python", "parse_javascript", "parse_typescript", "parse_generic"]
