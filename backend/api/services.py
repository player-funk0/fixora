"""
api/services.py
────────────────────────────────────────────────────────────────────────────
Thin service layer. Owns only:
  • File validation        (validate_code_file)
  • DB persistence         (save_submission)
  • Public re-export       (mock_analyze → delegates to orchestrator)

All analysis logic lives in the sub-packages:
  api/detection/      — language detection
  api/analyzers/      — per-language parsers
  api/fixes/          — report generation
  api/orchestrator.py — pipeline wiring
────────────────────────────────────────────────────────────────────────────
"""

import hashlib
import os

from .models import ErrorLog, Submission
from .analyzers.constants import EXTENSION_TO_LANGUAGE, ALLOWED_EXTENSIONS, MAX_FILE_BYTES
from .orchestrator import analyze as mock_analyze   # public alias for views.py

__all__ = ["mock_analyze", "validate_code_file", "save_submission", "FileValidationError"]


# ── File validation ───────────────────────────────────────────────────────────

class FileValidationError(Exception):
    pass


def validate_code_file(uploaded_file) -> tuple[str, str]:
    """
    Validate an uploaded code file.
    Returns (code_text, language_slug).
    Raises FileValidationError on any problem.
    """
    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    raw = uploaded_file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise FileValidationError(
            f"File too large ({len(raw):,} bytes). Max: {MAX_FILE_BYTES:,} bytes."
        )

    try:
        code = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise FileValidationError("File must be valid UTF-8 text.")

    if not code.strip():
        raise FileValidationError("File is empty.")

    return code, EXTENSION_TO_LANGUAGE[ext]


# ── DB persistence ────────────────────────────────────────────────────────────

def save_submission(
    user,            # ignored — kept for signature compat, always None now
    ip: str,
    language: str,
    code: str,
    result: dict,
    elapsed_ms: int,
    via_upload: bool = False,
    learning_mode: bool = False,   # kept for compat, no longer stored
) -> Submission:
    errors = result.get("errors", [])

    sub = Submission.objects.create(
        language      = result.get("detectedLanguage", language),
        code_hash     = hashlib.sha256(code.encode()).hexdigest()[:16],
        code_length   = len(code),
        error_count   = sum(1 for e in errors if e.get("type") == "error"),
        warning_count = sum(1 for e in errors if e.get("type") == "warning"),
        via_upload    = via_upload,
        response_ms   = elapsed_ms,
        ip_address    = ip,
    )

    ErrorLog.objects.bulk_create([
        ErrorLog(
            submission  = sub,
            error_type  = e.get("type", "error"),
            line_number = e.get("line"),
            title       = (e.get("title") or "")[:255],
        )
        for e in errors
    ])

    return sub
