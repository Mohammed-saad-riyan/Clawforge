"""Supabase client initialization.

Provides both anon (user-scoped) and service (admin) clients.
"""

from typing import Any
from supabase import create_client, Client

from clawforge.config import get_settings


# Type alias for clarity
SupabaseClient = Client

# Global client instances
_anon_client: SupabaseClient | None = None
_admin_client: SupabaseClient | None = None


def get_supabase_client() -> SupabaseClient:
    """Get Supabase client with anon key (respects RLS).

    Use this for user-facing operations where RLS should apply.
    """
    global _anon_client

    if _anon_client is None:
        settings = get_settings()

        if not settings.supabase_url or not settings.supabase_anon_key:
            raise ValueError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
            )

        _anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )

    return _anon_client


def get_supabase_admin_client() -> SupabaseClient:
    """Get Supabase client with service key (bypasses RLS).

    Use this for server-side operations that need full access.
    WARNING: This bypasses Row Level Security!
    """
    global _admin_client

    if _admin_client is None:
        settings = get_settings()

        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError(
                "Supabase admin not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY."
            )

        _admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )

    return _admin_client


def reset_clients() -> None:
    """Reset client instances (useful for testing)."""
    global _anon_client, _admin_client
    _anon_client = None
    _admin_client = None
