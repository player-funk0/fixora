"""
api/models.py
─────────────
Minimal models — no auth, no users, no rate limiting.
Just submission history and error logs for analytics.
"""

from django.db import models
from django.utils import timezone


class Submission(models.Model):
    LANGUAGE_CHOICES = [
        ("python",     "Python"),
        ("javascript", "JavaScript"),
        ("typescript", "TypeScript"),
        ("cpp",        "C++"),
        ("c",          "C"),
        ("java",       "Java"),
        ("go",         "Go"),
        ("rust",       "Rust"),
        ("csharp",     "C#"),
        ("ruby",       "Ruby"),
        ("html",       "HTML"),
        ("css",        "CSS"),
    ]

    language      = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    code_hash     = models.CharField(max_length=16)
    code_length   = models.PositiveIntegerField()
    error_count   = models.PositiveSmallIntegerField(default=0)
    warning_count = models.PositiveSmallIntegerField(default=0)
    via_upload    = models.BooleanField(default=False)
    submitted_at  = models.DateTimeField(default=timezone.now)
    response_ms   = models.PositiveIntegerField(null=True, blank=True)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "submissions"
        ordering = ["-submitted_at"]
        indexes  = [
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.language} ({self.error_count}E {self.warning_count}W)"


class ErrorLog(models.Model):
    ERROR_TYPES = [("error", "Error"), ("warning", "Warning")]

    submission  = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="errors")
    error_type  = models.CharField(max_length=10, choices=ERROR_TYPES)
    line_number = models.PositiveSmallIntegerField(null=True, blank=True)
    title       = models.CharField(max_length=255)
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "error_logs"

    def __str__(self):
        return f"{self.error_type.upper()} L{self.line_number}: {self.title}"
