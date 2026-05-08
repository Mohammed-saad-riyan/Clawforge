"""Webhooks module for ClawForge.

Handles GitHub webhooks for auto-analysis, issue tracking, and automated fixes.
"""

from clawforge.webhooks.github_webhook import (
    GitHubWebhookHandler,
    IssueAnalysis,
    verify_github_signature,
)

__all__ = [
    "GitHubWebhookHandler",
    "IssueAnalysis",
    "verify_github_signature",
]
