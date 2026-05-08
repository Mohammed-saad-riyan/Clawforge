"""Supabase integration for ClawForge.

Provides:
- Database client for project storage
- Authentication client for user management
- Real-time subscriptions (future)
"""

from clawforge.supabase.client import (
    get_supabase_client,
    get_supabase_admin_client,
    SupabaseClient,
)
from clawforge.supabase.auth import (
    SupabaseAuth,
    get_auth_client,
    AuthUser,
    AuthSession,
)
from clawforge.supabase.database import (
    SupabaseProjectStore,
    get_supabase_project_store,
)

__all__ = [
    "get_supabase_client",
    "get_supabase_admin_client",
    "SupabaseClient",
    "SupabaseAuth",
    "get_auth_client",
    "AuthUser",
    "AuthSession",
    "SupabaseProjectStore",
    "get_supabase_project_store",
]
