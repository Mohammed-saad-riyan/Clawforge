"""Component Library for ClawForge.

Pre-built, tested Flutter/Dart components that can be included in generated apps.
Inspired by shadcn/ui's approach - copy actual code, not use packages.

Categories:
- Authentication: Login, signup, forgot password flows
- Navigation: Drawer, bottom nav, tab bar
- Settings: Settings screen, profile, preferences
- Onboarding: Welcome screens, feature tours
- Common: Empty states, error screens, loading states
- Backend: Firebase, Supabase, REST API integrations
"""

from clawforge.components.library import (
    ComponentLibrary,
    Component,
    ComponentCategory,
    get_component_library,
)
from clawforge.components.auth import get_auth_components
from clawforge.components.navigation import get_navigation_components
from clawforge.components.settings import get_settings_components
from clawforge.components.backend import get_backend_components

__all__ = [
    "ComponentLibrary",
    "Component",
    "ComponentCategory",
    "get_component_library",
    "get_auth_components",
    "get_navigation_components",
    "get_settings_components",
    "get_backend_components",
]
