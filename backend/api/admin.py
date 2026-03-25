from django.contrib import admin
from .models import Submission, ErrorLog


class ErrorLogInline(admin.TabularInline):
    model   = ErrorLog
    extra   = 0
    readonly_fields = ("error_type", "line_number", "title", "created_at")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display  = ("id", "language", "error_count", "warning_count",
                     "code_length", "response_ms", "submitted_at")
    list_filter   = ("language", "via_upload")
    search_fields = ("code_hash", "ip_address")
    readonly_fields = ("code_hash", "submitted_at")
    inlines       = [ErrorLogInline]
