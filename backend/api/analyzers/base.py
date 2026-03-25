"""
api/analyzers/base.py
────────────────────────────────────────────────────────────────
Base utilities shared by every analyser.
"""

from __future__ import annotations


def make_issue_list() -> tuple[list[dict], callable]:
    """
    Factory that returns (issues_list, add_fn).
    add_fn deduplicates by title so the same issue is never reported twice.

    Usage:
        issues, add = make_issue_list()
        add(lineno, "error", "Title", "Explanation…")
        return issues
    """
    issues: list[dict] = []
    seen:   set[str]   = set()

    def add(lineno: int, etype: str, title: str, explanation: str) -> None:
        if title not in seen:
            issues.append({
                "type":        etype,
                "line":        lineno,
                "title":       title,
                "explanation": explanation,
            })
            seen.add(title)

    return issues, add
