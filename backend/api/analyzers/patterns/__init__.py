"""
api/analyzers/patterns/__init__.py
────────────────────────────────────────────────────────────────────────────
Assembles LANG_PATTERNS from individual per-language pattern files.

Adding a new language:
  1. Create  patterns/my_lang_patterns.py  with  PATTERNS = [...]
  2. Import and add it to  LANG_PATTERNS  below — nothing else changes.
────────────────────────────────────────────────────────────────────────────
"""

from .javascript_patterns  import PATTERNS           as _JS
from .typescript_patterns  import PATTERNS           as _TS
from .c_patterns            import PATTERNS_C         as _C
from .c_patterns            import PATTERNS_CPP       as _CPP
from .jvm_systems_patterns  import PATTERNS_JAVA      as _JAVA
from .jvm_systems_patterns  import PATTERNS_GO        as _GO
from .jvm_systems_patterns  import PATTERNS_RUST      as _RUST
from .jvm_systems_patterns  import PATTERNS_CSHARP    as _CSHARP
from .jvm_systems_patterns  import PATTERNS_RUBY      as _RUBY
from .web_patterns          import PATTERNS_HTML      as _HTML
from .web_patterns          import PATTERNS_CSS       as _CSS

import re as _re

UNIVERSAL_CHECKS: list[tuple] = [
    (lambda l: len(l) > 120,
     "warning", "Line too long (>120 chars)",
     "Consider breaking this line up for readability."),
    (lambda l: any(k in l for k in ("TODO", "FIXME", "HACK", "XXX")),
     "warning", "Unresolved TODO/FIXME",
     "A TODO or FIXME comment was found. Make sure this is not forgotten work."),
    (lambda l: bool(_re.search(r"(password|secret|api_key|token)\s*=\s*['\"]", l, _re.I)),
     "warning", "Possible hardcoded credential",
     "Use environment variables or a config file instead of hardcoding secrets."),
]

LANG_PATTERNS: dict[str, list[tuple]] = {
    "javascript": _JS,
    "typescript": _TS,
    "c":          _C,
    "cpp":        _CPP,
    "java":       _JAVA,
    "go":         _GO,
    "rust":       _RUST,
    "csharp":     _CSHARP,
    "ruby":       _RUBY,
    "html":       _HTML,
    "css":        _CSS,
}

__all__ = ["LANG_PATTERNS", "UNIVERSAL_CHECKS"]
