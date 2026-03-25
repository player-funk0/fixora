"""
api/serializers.py
──────────────────
Only the analyze request serializer remains.
Auth and plan serializers removed.
"""

from rest_framework import serializers


class AnalyzeRequestSerializer(serializers.Serializer):
    code     = serializers.CharField(max_length=50_000)
    language = serializers.ChoiceField(choices=[
        "python", "javascript", "typescript", "cpp", "c",
        "java", "go", "rust", "csharp", "ruby", "html", "css",
    ])
