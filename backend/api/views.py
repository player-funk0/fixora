"""
api/views.py
────────────────────────────────────────────────────────────────────────────
Endpoints:
  POST /api/analyze/         — analyze code (JSON)
  POST /api/analyze/upload/  — analyze uploaded file
  GET  /api/health/          — health check
  GET  /api/stats/           — project statistics (cloc-style)
────────────────────────────────────────────────────────────────────────────
No authentication. No rate limits. Free for everyone.
"""

import glob as _glob
import os as _os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import AnalyzeRequestSerializer
from .services import (
    FileValidationError,
    mock_analyze,
    save_submission,
    validate_code_file,
)


def _get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


# ── Analyze ───────────────────────────────────────────────────────────────────

def _run_analysis(request, code: str, language: str, via_upload: bool = False):
    """Shared analysis logic for both endpoints."""
    try:
        result, elapsed_ms = mock_analyze(code, language, learning_mode=False)
    except Exception as exc:
        return Response(
            {"error": f"Analysis engine error: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Persist anonymously (no user)
    save_submission(None, _get_client_ip(request), language, code,
                    result, elapsed_ms, via_upload, False)

    result["_meta"] = {"response_ms": elapsed_ms}
    return Response(result)


@api_view(["POST"])
@permission_classes([AllowAny])
def analyze(request):
    ser = AnalyzeRequestSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    return _run_analysis(
        request,
        code=ser.validated_data["code"],
        language=ser.validated_data["language"],
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def analyze_upload(request):
    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        code, language = validate_code_file(uploaded)
    except FileValidationError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    language = request.data.get("language", language)
    return _run_analysis(request, code=code, language=language, via_upload=True)


# ── Health ────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "version": "2.0.0"})


# ── Project Statistics ────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def project_stats(request):
    """Returns cloc-style statistics for the Fixora codebase."""
    from .analyzers.metrics import compute_project_stats

    base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    patterns = ["**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx",
                "**/*.html", "**/*.css"]
    files = []
    for pat in patterns:
        files.extend(_glob.glob(_os.path.join(base, pat), recursive=True))

    excluded = ("node_modules", "__pycache__", ".venv", "migrations", "dist", "build")
    files = [f for f in files if not any(e in f for e in excluded)]

    return Response(compute_project_stats(files))
