"""Navigation components for Flutter apps.

Pre-built drawer, bottom nav, and tab bar components.
"""

from clawforge.components.library import Component, ComponentCategory


def get_navigation_components() -> list[Component]:
    """Get all navigation components."""
    return [
        _bottom_nav_scaffold(),
        _drawer_scaffold(),
        _tab_bar_scaffold(),
    ]


def _bottom_nav_scaffold() -> Component:
    """Bottom navigation bar scaffold."""
    return Component(
        id="nav_bottom_scaffold",
        name="Bottom Navigation Scaffold",
        description="Main app scaffold with bottom navigation bar",
        category=ComponentCategory.NAVIGATION,
        tags=["navigation", "bottom", "tabs", "scaffold"],
        dependencies={
            "flutter_riverpod": "^2.5.1",
        },
        files=[
            {
                "path": "lib/core/navigation/bottom_nav_scaffold.dart",
                "content": '''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Navigation state provider
final bottomNavIndexProvider = StateProvider<int>((ref) => 0);

class BottomNavScaffold extends ConsumerWidget {
  final List<BottomNavItem> items;
  final List<Widget> pages;
  final Color? selectedColor;
  final Color? unselectedColor;
  final bool showLabels;

  const BottomNavScaffold({
    super.key,
    required this.items,
    required this.pages,
    this.selectedColor,
    this.unselectedColor,
    this.showLabels = true,
  }) : assert(items.length == pages.length);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentIndex = ref.watch(bottomNavIndexProvider);

    return Scaffold(
      body: IndexedStack(
        index: currentIndex,
        children: pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          ref.read(bottomNavIndexProvider.notifier).state = index;
        },
        destinations: items.map((item) {
          return NavigationDestination(
            icon: Icon(item.icon),
            selectedIcon: Icon(item.selectedIcon ?? item.icon),
            label: item.label,
          );
        }).toList(),
      ),
    );
  }
}

class BottomNavItem {
  final IconData icon;
  final IconData? selectedIcon;
  final String label;

  const BottomNavItem({
    required this.icon,
    this.selectedIcon,
    required this.label,
  });
}

// Example usage:
// BottomNavScaffold(
//   items: const [
//     BottomNavItem(icon: Icons.home_outlined, selectedIcon: Icons.home, label: 'Home'),
//     BottomNavItem(icon: Icons.search_outlined, selectedIcon: Icons.search, label: 'Search'),
//     BottomNavItem(icon: Icons.person_outline, selectedIcon: Icons.person, label: 'Profile'),
//   ],
//   pages: const [
//     HomeScreen(),
//     SearchScreen(),
//     ProfileScreen(),
//   ],
// )
''',
            },
        ],
    )


def _drawer_scaffold() -> Component:
    """Navigation drawer scaffold."""
    return Component(
        id="nav_drawer_scaffold",
        name="Drawer Scaffold",
        description="Main app scaffold with navigation drawer",
        category=ComponentCategory.NAVIGATION,
        tags=["navigation", "drawer", "sidebar", "scaffold"],
        dependencies={
            "flutter_riverpod": "^2.5.1",
        },
        files=[
            {
                "path": "lib/core/navigation/drawer_scaffold.dart",
                "content": '''import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Navigation state provider
final drawerPageIndexProvider = StateProvider<int>((ref) => 0);

class DrawerScaffold extends ConsumerWidget {
  final String appTitle;
  final List<DrawerItem> items;
  final List<Widget> pages;
  final Widget? header;
  final List<Widget>? footerItems;

  const DrawerScaffold({
    super.key,
    required this.appTitle,
    required this.items,
    required this.pages,
    this.header,
    this.footerItems,
  }) : assert(items.length == pages.length);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentIndex = ref.watch(drawerPageIndexProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(items[currentIndex].title),
      ),
      drawer: NavigationDrawer(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          ref.read(drawerPageIndexProvider.notifier).state = index;
          Navigator.pop(context); // Close drawer
        },
        children: [
          // Header
          header ?? DrawerHeader(
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const CircleAvatar(
                  radius: 32,
                  child: Icon(Icons.person, size: 32),
                ),
                const SizedBox(height: 8),
                Text(
                  appTitle,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),

          // Navigation items
          ...items.map((item) {
            return NavigationDrawerDestination(
              icon: Icon(item.icon),
              selectedIcon: Icon(item.selectedIcon ?? item.icon),
              label: Text(item.title),
            );
          }),

          // Divider and footer
          if (footerItems != null) ...[
            const Divider(),
            ...footerItems!,
          ],
        ],
      ),
      body: IndexedStack(
        index: currentIndex,
        children: pages,
      ),
    );
  }
}

class DrawerItem {
  final IconData icon;
  final IconData? selectedIcon;
  final String title;

  const DrawerItem({
    required this.icon,
    this.selectedIcon,
    required this.title,
  });
}

// Example usage:
// DrawerScaffold(
//   appTitle: 'My App',
//   items: const [
//     DrawerItem(icon: Icons.home_outlined, selectedIcon: Icons.home, title: 'Home'),
//     DrawerItem(icon: Icons.settings_outlined, selectedIcon: Icons.settings, title: 'Settings'),
//     DrawerItem(icon: Icons.info_outline, selectedIcon: Icons.info, title: 'About'),
//   ],
//   pages: const [
//     HomeScreen(),
//     SettingsScreen(),
//     AboutScreen(),
//   ],
// )
''',
            },
        ],
    )


def _tab_bar_scaffold() -> Component:
    """Tab bar scaffold."""
    return Component(
        id="nav_tab_scaffold",
        name="Tab Bar Scaffold",
        description="Screen with tab bar navigation",
        category=ComponentCategory.NAVIGATION,
        tags=["navigation", "tabs", "tabbar", "scaffold"],
        files=[
            {
                "path": "lib/core/navigation/tab_scaffold.dart",
                "content": '''import 'package:flutter/material.dart';

class TabScaffold extends StatelessWidget {
  final String title;
  final List<TabItem> tabs;
  final List<Widget>? actions;
  final bool isScrollable;

  const TabScaffold({
    super.key,
    required this.title,
    required this.tabs,
    this.actions,
    this.isScrollable = false,
  });

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        appBar: AppBar(
          title: Text(title),
          actions: actions,
          bottom: TabBar(
            isScrollable: isScrollable,
            tabs: tabs.map((tab) {
              return Tab(
                icon: tab.icon != null ? Icon(tab.icon) : null,
                text: tab.label,
              );
            }).toList(),
          ),
        ),
        body: TabBarView(
          children: tabs.map((tab) => tab.child).toList(),
        ),
      ),
    );
  }
}

class TabItem {
  final IconData? icon;
  final String label;
  final Widget child;

  const TabItem({
    this.icon,
    required this.label,
    required this.child,
  });
}

// Example usage:
// TabScaffold(
//   title: 'Dashboard',
//   tabs: [
//     TabItem(icon: Icons.analytics, label: 'Analytics', child: AnalyticsTab()),
//     TabItem(icon: Icons.people, label: 'Users', child: UsersTab()),
//     TabItem(icon: Icons.settings, label: 'Settings', child: SettingsTab()),
//   ],
// )
''',
            },
        ],
    )
