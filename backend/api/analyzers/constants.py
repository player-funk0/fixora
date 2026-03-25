"""
api/analyzers/constants.py
────────────────────────────────────────────────────────────────
Shared constants used across all Fixora modules.
Centralised here so there is ONE source of truth.
"""

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".cpp": "cpp", ".cc": "cpp", ".c": "c", ".java": "java",
    ".go": "go", ".rs": "rust", ".cs": "csharp", ".rb": "ruby",
    ".html": "html", ".htm": "html", ".css": "css",
}

ALLOWED_EXTENSIONS: set[str] = set(EXTENSION_TO_LANGUAGE.keys())
MAX_FILE_BYTES = 50_000

LANG_LABELS: dict[str, str] = {
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "cpp": "C++", "c": "C", "java": "Java", "go": "Go", "rust": "Rust",
    "csharp": "C#", "ruby": "Ruby", "html": "HTML", "css": "CSS",
}

COMMENT_PREFIX: dict[str, str] = {
    "python": "#", "ruby": "#",
    "javascript": "//", "typescript": "//", "java": "//",
    "cpp": "//", "c": "//", "csharp": "//", "go": "//", "rust": "//",
    "html": "<!--", "css": "/*",
}
