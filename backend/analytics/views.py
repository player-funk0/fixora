"""
analytics/views.py
Teacher & admin-only analytics endpoints.

GET /api/analytics/overview/?days=7
GET /api/analytics/languages/?days=7
GET /api/analytics/top-errors/?days=7&limit=10
GET /api/analytics/daily/?days=14
GET /api/analytics/users/
GET /api/analytics/users/<id>/
"""

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.models import DailyUsage, ErrorLog, Submission, User
from api.permissions import IsTeacherOrAdmin
from api.serializers import UserSerializer


def _since(days: int):
    return timezone.now() - timedelta(days=days)


def _int_param(request, name: str, default: int, min_val: int = 1, max_val: int = 365) -> tuple[int, str | None]:
    """
    Safely parse an integer query param.
    Returns (value, error_message_or_None).
    Bug 4 fix: bare int() raises ValueError on non-integer input → 500.
    This returns a descriptive error string instead so callers can return 400.
    """
    raw = request.query_params.get(name, default)
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return default, f"'{name}' must be an integer, got: {raw!r}"
    if val < min_val or val > max_val:
        return default, f"'{name}' must be between {min_val} and {max_val}, got: {val}"
    return val, None


# ── Overview ──────────────────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def overview(request):
    days, err = _int_param(request, "days", 7)
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    qs  = Submission.objects.filter(submitted_at__gte=_since(days))
    agg = qs.aggregate(
        total_submissions = Count("id"),
        total_errors      = Sum("error_count"),
        total_warnings    = Sum("warning_count"),
        avg_errors        = Avg("error_count"),
        unique_users      = Count("user", distinct=True),
        learning_uses     = Count("id", filter=Q(learning_mode=True)),
        upload_uses       = Count("id", filter=Q(via_upload=True)),
        avg_response_ms   = Avg("response_ms"),
    )

    return Response({
        "period_days":        days,
        "total_submissions":  agg["total_submissions"] or 0,
        "total_errors":       agg["total_errors"]      or 0,
        "total_warnings":     agg["total_warnings"]    or 0,
        "avg_errors":         round(agg["avg_errors"] or 0, 2),
        "unique_users":       agg["unique_users"]      or 0,
        "learning_mode_uses": agg["learning_uses"]     or 0,
        "file_upload_uses":   agg["upload_uses"]       or 0,
        "avg_response_ms":    round(agg["avg_response_ms"] or 0),
    })


# ── Breakdown by language ─────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def by_language(request):
    days, err = _int_param(request, "days", 7)
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    rows = (
        Submission.objects
        .filter(submitted_at__gte=_since(days))
        .values("language")
        .annotate(
            count        = Count("id"),
            avg_errors   = Avg("error_count"),
            total_errors = Sum("error_count"),
        )
        .order_by("-count")
    )
    return Response(list(rows))


# ── Top recurring errors ──────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def top_errors(request):
    days,  err1 = _int_param(request, "days",  7)
    limit, err2 = _int_param(request, "limit", 10, min_val=1, max_val=100)
    if err1 or err2:
        return Response({"error": err1 or err2}, status=status.HTTP_400_BAD_REQUEST)

    rows = (
        ErrorLog.objects
        .filter(submission__submitted_at__gte=_since(days))
        .values("title", "error_type")
        .annotate(frequency=Count("id"))
        .order_by("-frequency")[:limit]
    )
    return Response(list(rows))


# ── Daily activity (chart data) ───────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def daily_activity(request):
    days, err = _int_param(request, "days", 14)
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    rows = (
        Submission.objects
        .filter(submitted_at__gte=_since(days))
        .annotate(day=TruncDate("submitted_at"))
        .values("day")
        .annotate(
            submissions  = Count("id"),
            total_errors = Sum("error_count"),
            unique_users = Count("user", distinct=True),
        )
        .order_by("day")
    )
    return Response(list(rows))


# ── User list (teacher view) ──────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def user_list(request):
    days, err = _int_param(request, "days", 30)
    if err:
        return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

    users = (
        User.objects
        .filter(role="student")
        .annotate(
            total_submissions  = Count("submissions"),
            recent_submissions = Count(
                "submissions",
                filter=Q(submissions__submitted_at__gte=_since(days))
            ),
            avg_errors = Avg("submissions__error_count"),
        )
        .order_by("-recent_submissions")
    )

    data = [
        {
            "id":                 u.id,
            "email":              u.email,
            "plan":               u.plan,
            "joined":             u.created_at,
            "total_submissions":  u.total_submissions,
            "recent_submissions": u.recent_submissions,
            "avg_errors_per_sub": round(u.avg_errors or 0, 2),
        }
        for u in users
    ]
    return Response(data)


# ── Individual student detail ─────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def user_detail(request, uid: int):
    try:
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Bug 1 fix: .values() must come BEFORE the slice [:50].
    # Calling .values() after slicing raises:
    #   TypeError: Cannot reuse a query after it has been sliced.
    submissions = list(
        Submission.objects
        .filter(user=user)
        .values(
            "id", "language", "error_count", "warning_count",
            "learning_mode", "via_upload", "submitted_at", "response_ms",
        )
        .order_by("-submitted_at")[:50]
    )

    progress = list(
        Submission.objects
        .filter(user=user)
        .annotate(day=TruncDate("submitted_at"))
        .values("day")
        .annotate(avg_errors=Avg("error_count"), count=Count("id"))
        .order_by("day")
    )

    top_mistakes = list(
        ErrorLog.objects
        .filter(submission__user=user)
        .values("title", "error_type")
        .annotate(frequency=Count("id"))
        .order_by("-frequency")[:5]
    )

    return Response({
        "user":         UserSerializer(user).data,
        "submissions":  submissions,
        "progress":     progress,
        "top_mistakes": top_mistakes,
    })


# ── Usage summary (daily quota across all users) ──────────────────────────────
@api_view(["GET"])
@permission_classes([IsTeacherOrAdmin])
def quota_summary(request):
    # Bug 2 fix: use module-level `timezone` instead of importing `now` inside the function.
    today = timezone.now().date()
    rows = list(
        DailyUsage.objects
        .filter(date=today)
        .order_by("-count")[:50]
        .values("user_key", "count")
    )
    return Response({"date": today, "active_keys": rows})

