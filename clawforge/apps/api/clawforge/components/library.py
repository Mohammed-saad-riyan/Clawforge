"""Component Library for ClawForge.

Manages pre-built Flutter/Dart components that can be included in generated apps.
Similar to shadcn/ui - components are copied as source code, not used as packages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComponentCategory(Enum):
    """Categories of components."""
    AUTH = "auth"
    NAVIGATION = "navigation"
    SETTINGS = "settings"
    COMMON = "common"
    BACKEND = "backend"
    ONBOARDING = "onboarding"


@dataclass
class Component:
    """A reusable Flutter component."""

    id: str  # Unique identifier (e.g., "auth_login_screen")
    name: str  # Display name (e.g., "Login Screen")
    description: str
    category: ComponentCategory

    # The actual component files
    files: list[dict[str, str]] = field(default_factory=list)  # [{path, content}]

    # Dependencies this component needs in pubspec.yaml
    dependencies: dict[str, str] = field(default_factory=dict)
    dev_dependencies: dict[str, str] = field(default_factory=dict)

    # Other components this depends on
    requires: list[str] = field(default_factory=list)  # Component IDs

    # Tags for search/filtering
    tags: list[str] = field(default_factory=list)

    # Preview/thumbnail URL (optional)
    preview_url: str = ""


class ComponentLibrary:
    """Registry of all available components."""

    def __init__(self):
        self.components: dict[str, Component] = {}
        self._load_components()

    def _load_components(self) -> None:
        """Load all components from modules."""
        from clawforge.components.auth import get_auth_components
        from clawforge.components.navigation import get_navigation_components
        from clawforge.components.settings import get_settings_components
        from clawforge.components.backend import get_backend_components

        # Register all components
        for component in get_auth_components():
            self.register(component)

        for component in get_navigation_components():
            self.register(component)

        for component in get_settings_components():
            self.register(component)

        for component in get_backend_components():
            self.register(component)

    def register(self, component: Component) -> None:
        """Register a component in the library."""
        self.components[component.id] = component

    def get(self, component_id: str) -> Component | None:
        """Get a component by ID."""
        return self.components.get(component_id)

    def list_by_category(self, category: ComponentCategory) -> list[Component]:
        """List all components in a category."""
        return [
            c for c in self.components.values()
            if c.category == category
        ]

    def search(self, query: str) -> list[Component]:
        """Search components by name, description, or tags."""
        query = query.lower()
        results = []

        for component in self.components.values():
            if (
                query in component.name.lower()
                or query in component.description.lower()
                or any(query in tag.lower() for tag in component.tags)
            ):
                results.append(component)

        return results

    def get_with_dependencies(self, component_id: str) -> list[Component]:
        """Get a component and all its dependencies."""
        component = self.get(component_id)
        if not component:
            return []

        result = [component]
        visited = {component_id}

        def collect_deps(comp: Component) -> None:
            for dep_id in comp.requires:
                if dep_id not in visited:
                    visited.add(dep_id)
                    dep = self.get(dep_id)
                    if dep:
                        result.append(dep)
                        collect_deps(dep)

        collect_deps(component)
        return result

    def get_all_files(self, component_ids: list[str]) -> list[dict[str, str]]:
        """Get all files for a list of components (with deduplication)."""
        files: dict[str, str] = {}  # path -> content

        for comp_id in component_ids:
            components = self.get_with_dependencies(comp_id)
            for comp in components:
                for file_info in comp.files:
                    path = file_info["path"]
                    # Don't overwrite if already exists (first component wins)
                    if path not in files:
                        files[path] = file_info["content"]

        return [{"path": p, "content": c} for p, c in files.items()]

    def get_all_dependencies(self, component_ids: list[str]) -> tuple[dict[str, str], dict[str, str]]:
        """Get combined pubspec dependencies for components."""
        deps: dict[str, str] = {}
        dev_deps: dict[str, str] = {}

        for comp_id in component_ids:
            components = self.get_with_dependencies(comp_id)
            for comp in components:
                deps.update(comp.dependencies)
                dev_deps.update(comp.dev_dependencies)

        return deps, dev_deps

    def to_dict(self) -> dict[str, Any]:
        """Convert library to dictionary for API response."""
        return {
            "categories": [c.value for c in ComponentCategory],
            "component_count": len(self.components),
            "components": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "category": c.category.value,
                    "tags": c.tags,
                    "file_count": len(c.files),
                    "requires": c.requires,
                }
                for c in self.components.values()
            ],
        }


# Global library instance
_library: ComponentLibrary | None = None


def get_component_library() -> ComponentLibrary:
    """Get the global component library instance."""
    global _library
    if _library is None:
        _library = ComponentLibrary()
    return _library
