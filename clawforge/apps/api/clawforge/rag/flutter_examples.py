"""Flutter code examples for RAG."""

# Curated Flutter examples for different patterns
# These are included in prompts to help the LLM generate idiomatic code

FLUTTER_EXAMPLES = {
    "riverpod_provider": '''
// Riverpod 3.0 Provider Example
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'todo_provider.g.dart';

@riverpod
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];

  void addTodo(Todo todo) {
    state = [...state, todo];
  }

  void removeTodo(String id) {
    state = state.where((t) => t.id != id).toList();
  }

  void toggleTodo(String id) {
    state = [
      for (final todo in state)
        if (todo.id == id) todo.copyWith(completed: !todo.completed) else todo,
    ];
  }
}

// Async provider with loading state
@riverpod
class UserProfile extends _$UserProfile {
  @override
  Future<User> build() async {
    return await ref.watch(userRepositoryProvider).getCurrentUser();
  }

  Future<void> updateProfile(UserUpdate update) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(userRepositoryProvider).updateUser(update),
    );
  }
}
''',
    "go_router": '''
// go_router Navigation Example
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'router.g.dart';

@riverpod
GoRouter router(RouterRef ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
        routes: [
          GoRoute(
            path: 'details/:id',
            builder: (context, state) {
              final id = state.pathParameters['id']!;
              return DetailsScreen(id: id);
            },
          ),
        ],
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
    ],
    errorBuilder: (context, state) => ErrorScreen(error: state.error),
  );
}
''',
    "drift_database": '''
// Drift Database Example
import 'package:drift/drift.dart';

part 'database.g.dart';

class Todos extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text().withLength(min: 1, max: 100)();
  TextColumn get description => text().nullable()();
  BoolColumn get completed => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime().withDefault(currentDateAndTime)();
}

@DriftDatabase(tables: [Todos])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  // CRUD operations
  Future<List<Todo>> getAllTodos() => select(todos).get();

  Stream<List<Todo>> watchAllTodos() => select(todos).watch();

  Future<int> insertTodo(TodosCompanion todo) => into(todos).insert(todo);

  Future<bool> updateTodo(Todo todo) => update(todos).replace(todo);

  Future<int> deleteTodo(int id) =>
      (delete(todos)..where((t) => t.id.equals(id))).go();
}
''',
    "material3_theme": '''
// Material 3 Theme Configuration
import 'package:flutter/material.dart';

ThemeData createTheme({required Brightness brightness}) {
  final colorScheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF6750A4),
    brightness: brightness,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: colorScheme,
    appBarTheme: AppBarTheme(
      centerTitle: true,
      backgroundColor: colorScheme.surface,
      foregroundColor: colorScheme.onSurface,
    ),
    cardTheme: CardTheme(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: colorScheme.outlineVariant),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: colorScheme.surfaceContainerHighest,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    ),
  );
}
''',
    "async_widget": '''
// Async Data Widget with Loading/Error States
class AsyncDataWidget<T> extends ConsumerWidget {
  final ProviderListenable<AsyncValue<T>> provider;
  final Widget Function(T data) builder;
  final Widget? loadingWidget;
  final Widget Function(Object error, StackTrace stack)? errorBuilder;

  const AsyncDataWidget({
    super.key,
    required this.provider,
    required this.builder,
    this.loadingWidget,
    this.errorBuilder,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncValue = ref.watch(provider);

    return asyncValue.when(
      data: builder,
      loading: () => loadingWidget ?? const Center(
        child: CircularProgressIndicator(),
      ),
      error: (error, stack) => errorBuilder?.call(error, stack) ?? Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 48, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text('Something went wrong', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            FilledButton.tonal(
              onPressed: () => ref.invalidate(provider),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
''',
}

# Keywords to example mapping
KEYWORD_MAPPING = {
    "state": ["riverpod_provider"],
    "provider": ["riverpod_provider"],
    "riverpod": ["riverpod_provider"],
    "navigation": ["go_router"],
    "router": ["go_router"],
    "route": ["go_router"],
    "database": ["drift_database"],
    "sqlite": ["drift_database"],
    "storage": ["drift_database"],
    "persist": ["drift_database"],
    "theme": ["material3_theme"],
    "color": ["material3_theme"],
    "style": ["material3_theme"],
    "loading": ["async_widget"],
    "error": ["async_widget"],
    "async": ["async_widget", "riverpod_provider"],
}


async def get_flutter_examples(requirement: str) -> str:
    """Get relevant Flutter examples based on requirement.

    Uses simple keyword matching for now.
    TODO: Replace with ChromaDB vector search for better matching.
    """
    requirement_lower = requirement.lower()
    matched_examples: set[str] = set()

    for keyword, example_keys in KEYWORD_MAPPING.items():
        if keyword in requirement_lower:
            matched_examples.update(example_keys)

    # Always include at least provider and theme examples
    if not matched_examples:
        matched_examples = {"riverpod_provider", "material3_theme"}

    examples = []
    for key in matched_examples:
        if key in FLUTTER_EXAMPLES:
            examples.append(f"### {key.replace('_', ' ').title()}\n{FLUTTER_EXAMPLES[key]}")

    return "\n\n".join(examples)
