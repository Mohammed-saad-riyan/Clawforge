"""Backend integration components for Flutter apps.

Pre-built Supabase, Firebase, and REST API client templates.
"""

from clawforge.components.library import Component, ComponentCategory


def get_backend_components() -> list[Component]:
    """Get all backend integration components."""
    return [
        _supabase_client(),
        _supabase_auth_provider(),
        _supabase_database_service(),
        _firebase_core(),
        _firebase_auth_provider(),
        _firestore_service(),
        _rest_api_client(),
        _api_interceptor(),
    ]


def _supabase_client() -> Component:
    """Supabase client initialization."""
    return Component(
        id="supabase_client",
        name="Supabase Client",
        description="Supabase client initialization and configuration",
        category=ComponentCategory.BACKEND,
        tags=["supabase", "backend", "client", "database"],
        dependencies={
            "supabase_flutter": "^2.3.0",
            "flutter_dotenv": "^5.1.0",
        },
        files=[
            {
                "path": "lib/core/supabase/supabase_client.dart",
                "content": '''import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class SupabaseClientService {
  static SupabaseClient? _client;

  static Future<void> initialize() async {
    await dotenv.load(fileName: ".env");

    await Supabase.initialize(
      url: dotenv.env['SUPABASE_URL'] ?? '',
      anonKey: dotenv.env['SUPABASE_ANON_KEY'] ?? '',
      authOptions: const FlutterAuthClientOptions(
        authFlowType: AuthFlowType.pkce,
      ),
      realtimeClientOptions: const RealtimeClientOptions(
        logLevel: RealtimeLogLevel.info,
      ),
    );

    _client = Supabase.instance.client;
  }

  static SupabaseClient get client {
    if (_client == null) {
      throw Exception('Supabase client not initialized. Call initialize() first.');
    }
    return _client!;
  }

  static GoTrueClient get auth => client.auth;
  static SupabaseStorageClient get storage => client.storage;
  static RealtimeClient get realtime => client.realtime;

  // Helper to get typed database reference
  static SupabaseQueryBuilder from(String table) => client.from(table);
}
''',
            },
            {
                "path": ".env.example",
                "content": '''# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
''',
            },
        ],
    )


def _supabase_auth_provider() -> Component:
    """Supabase authentication provider with Riverpod."""
    return Component(
        id="supabase_auth_provider",
        name="Supabase Auth Provider",
        description="Riverpod provider for Supabase authentication",
        category=ComponentCategory.BACKEND,
        tags=["supabase", "auth", "riverpod", "provider"],
        requires=["supabase_client"],
        dependencies={
            "supabase_flutter": "^2.3.0",
            "flutter_riverpod": "^2.5.1",
        },
        files=[
            {
                "path": "lib/core/supabase/supabase_auth_provider.dart",
                "content": '''import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'supabase_client.dart';

// Auth state enum
enum AuthStatus { initial, authenticated, unauthenticated, loading }

// Auth state class
class AuthState {
  final AuthStatus status;
  final User? user;
  final String? errorMessage;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.errorMessage,
  });

  AuthState copyWith({
    AuthStatus? status,
    User? user,
    String? errorMessage,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage,
    );
  }

  bool get isAuthenticated => status == AuthStatus.authenticated;
  bool get isLoading => status == AuthStatus.loading;
}

// Auth notifier
class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState()) {
    _initialize();
  }

  void _initialize() {
    // Listen to auth state changes
    SupabaseClientService.auth.onAuthStateChange.listen((data) {
      final session = data.session;
      if (session != null) {
        state = AuthState(
          status: AuthStatus.authenticated,
          user: session.user,
        );
      } else {
        state = const AuthState(status: AuthStatus.unauthenticated);
      }
    });

    // Check current session
    final session = SupabaseClientService.auth.currentSession;
    if (session != null) {
      state = AuthState(
        status: AuthStatus.authenticated,
        user: session.user,
      );
    } else {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> signInWithEmail(String email, String password) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      final response = await SupabaseClientService.auth.signInWithPassword(
        email: email,
        password: password,
      );
      state = AuthState(
        status: AuthStatus.authenticated,
        user: response.user,
      );
    } on AuthException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signUpWithEmail(String email, String password) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      final response = await SupabaseClientService.auth.signUp(
        email: email,
        password: password,
      );
      if (response.user != null) {
        state = AuthState(
          status: AuthStatus.authenticated,
          user: response.user,
        );
      }
    } on AuthException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signInWithOAuth(OAuthProvider provider) async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      await SupabaseClientService.auth.signInWithOAuth(provider);
    } on AuthException catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signOut() async {
    await SupabaseClientService.auth.signOut();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> resetPassword(String email) async {
    await SupabaseClientService.auth.resetPasswordForEmail(email);
  }

  Future<void> updatePassword(String newPassword) async {
    await SupabaseClientService.auth.updateUser(
      UserAttributes(password: newPassword),
    );
  }
}

// Providers
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});

final currentUserProvider = Provider<User?>((ref) {
  return ref.watch(authProvider).user;
});

final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).isAuthenticated;
});
''',
            },
        ],
    )


def _supabase_database_service() -> Component:
    """Supabase database service with CRUD operations."""
    return Component(
        id="supabase_database_service",
        name="Supabase Database Service",
        description="Generic database service for Supabase with CRUD operations",
        category=ComponentCategory.BACKEND,
        tags=["supabase", "database", "crud", "service"],
        requires=["supabase_client"],
        dependencies={
            "supabase_flutter": "^2.3.0",
        },
        files=[
            {
                "path": "lib/core/supabase/supabase_database_service.dart",
                "content": '''import 'package:supabase_flutter/supabase_flutter.dart';
import 'supabase_client.dart';

/// Generic database service for Supabase operations
class SupabaseDatabaseService<T> {
  final String tableName;
  final T Function(Map<String, dynamic> json) fromJson;
  final Map<String, dynamic> Function(T item) toJson;

  SupabaseDatabaseService({
    required this.tableName,
    required this.fromJson,
    required this.toJson,
  });

  SupabaseQueryBuilder get _table => SupabaseClientService.from(tableName);

  /// Get all records
  Future<List<T>> getAll({
    String? orderBy,
    bool ascending = true,
    int? limit,
    int? offset,
  }) async {
    var query = _table.select();

    if (orderBy != null) {
      query = query.order(orderBy, ascending: ascending);
    }
    if (limit != null) {
      query = query.limit(limit);
    }
    if (offset != null) {
      query = query.range(offset, offset + (limit ?? 10) - 1);
    }

    final response = await query;
    return (response as List).map((json) => fromJson(json)).toList();
  }

  /// Get a single record by ID
  Future<T?> getById(String id, {String idColumn = 'id'}) async {
    final response = await _table
        .select()
        .eq(idColumn, id)
        .maybeSingle();

    return response != null ? fromJson(response) : null;
  }

  /// Get records with a filter
  Future<List<T>> getWhere(
    String column,
    dynamic value, {
    String? orderBy,
    bool ascending = true,
  }) async {
    var query = _table.select().eq(column, value);

    if (orderBy != null) {
      query = query.order(orderBy, ascending: ascending);
    }

    final response = await query;
    return (response as List).map((json) => fromJson(json)).toList();
  }

  /// Create a new record
  Future<T> create(T item) async {
    final response = await _table
        .insert(toJson(item))
        .select()
        .single();

    return fromJson(response);
  }

  /// Update a record
  Future<T> update(String id, T item, {String idColumn = 'id'}) async {
    final response = await _table
        .update(toJson(item))
        .eq(idColumn, id)
        .select()
        .single();

    return fromJson(response);
  }

  /// Partial update (only specified fields)
  Future<T> patch(String id, Map<String, dynamic> fields, {String idColumn = 'id'}) async {
    final response = await _table
        .update(fields)
        .eq(idColumn, id)
        .select()
        .single();

    return fromJson(response);
  }

  /// Delete a record
  Future<void> delete(String id, {String idColumn = 'id'}) async {
    await _table.delete().eq(idColumn, id);
  }

  /// Upsert (insert or update)
  Future<T> upsert(T item, {String? onConflict}) async {
    final response = await _table
        .upsert(toJson(item), onConflict: onConflict)
        .select()
        .single();

    return fromJson(response);
  }

  /// Count records
  Future<int> count({String? column, dynamic value}) async {
    if (column != null && value != null) {
      final response = await _table
          .select()
          .eq(column, value)
          .count(CountOption.exact);
      return response.count;
    }

    final response = await _table.select().count(CountOption.exact);
    return response.count;
  }

  /// Search with text search
  Future<List<T>> search(String column, String query) async {
    final response = await _table
        .select()
        .ilike(column, '%$query%');

    return (response as List).map((json) => fromJson(json)).toList();
  }

  /// Subscribe to realtime changes
  RealtimeChannel subscribe({
    void Function(Map<String, dynamic>)? onInsert,
    void Function(Map<String, dynamic>)? onUpdate,
    void Function(Map<String, dynamic>)? onDelete,
  }) {
    return SupabaseClientService.client
        .channel('public:$tableName')
        .onPostgresChanges(
          event: PostgresChangeEvent.insert,
          schema: 'public',
          table: tableName,
          callback: (payload) => onInsert?.call(payload.newRecord),
        )
        .onPostgresChanges(
          event: PostgresChangeEvent.update,
          schema: 'public',
          table: tableName,
          callback: (payload) => onUpdate?.call(payload.newRecord),
        )
        .onPostgresChanges(
          event: PostgresChangeEvent.delete,
          schema: 'public',
          table: tableName,
          callback: (payload) => onDelete?.call(payload.oldRecord),
        )
        .subscribe();
  }
}

// Example usage:
//
// class UserService extends SupabaseDatabaseService<User> {
//   UserService() : super(
//     tableName: 'users',
//     fromJson: User.fromJson,
//     toJson: (user) => user.toJson(),
//   );
// }
''',
            },
        ],
    )


def _firebase_core() -> Component:
    """Firebase core initialization."""
    return Component(
        id="firebase_core",
        name="Firebase Core",
        description="Firebase initialization and configuration",
        category=ComponentCategory.BACKEND,
        tags=["firebase", "backend", "client", "google"],
        dependencies={
            "firebase_core": "^2.25.0",
        },
        files=[
            {
                "path": "lib/core/firebase/firebase_service.dart",
                "content": '''import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';

class FirebaseService {
  static bool _initialized = false;

  static Future<void> initialize() async {
    if (_initialized) return;

    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );

    _initialized = true;
  }

  static bool get isInitialized => _initialized;
}
''',
            },
            {
                "path": "lib/core/firebase/firebase_options.dart",
                "content": '''// Generated file - Replace with your Firebase configuration
// Run: flutterfire configure

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for windows - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  // TODO: Replace with your Firebase configuration
  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'YOUR_WEB_API_KEY',
    appId: 'YOUR_WEB_APP_ID',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    projectId: 'YOUR_PROJECT_ID',
    authDomain: 'YOUR_AUTH_DOMAIN',
    storageBucket: 'YOUR_STORAGE_BUCKET',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'YOUR_ANDROID_API_KEY',
    appId: 'YOUR_ANDROID_APP_ID',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_STORAGE_BUCKET',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'YOUR_IOS_API_KEY',
    appId: 'YOUR_IOS_APP_ID',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_STORAGE_BUCKET',
    iosBundleId: 'YOUR_IOS_BUNDLE_ID',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'YOUR_MACOS_API_KEY',
    appId: 'YOUR_MACOS_APP_ID',
    messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_STORAGE_BUCKET',
    iosBundleId: 'YOUR_MACOS_BUNDLE_ID',
  );
}
''',
            },
        ],
    )


def _firebase_auth_provider() -> Component:
    """Firebase authentication provider with Riverpod."""
    return Component(
        id="firebase_auth_provider",
        name="Firebase Auth Provider",
        description="Riverpod provider for Firebase authentication",
        category=ComponentCategory.BACKEND,
        tags=["firebase", "auth", "riverpod", "provider"],
        requires=["firebase_core"],
        dependencies={
            "firebase_auth": "^4.17.0",
            "flutter_riverpod": "^2.5.1",
            "google_sign_in": "^6.2.1",
        },
        files=[
            {
                "path": "lib/core/firebase/firebase_auth_provider.dart",
                "content": '''import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

// Auth state enum
enum FirebaseAuthStatus { initial, authenticated, unauthenticated, loading }

// Auth state class
class FirebaseAuthState {
  final FirebaseAuthStatus status;
  final User? user;
  final String? errorMessage;

  const FirebaseAuthState({
    this.status = FirebaseAuthStatus.initial,
    this.user,
    this.errorMessage,
  });

  FirebaseAuthState copyWith({
    FirebaseAuthStatus? status,
    User? user,
    String? errorMessage,
  }) {
    return FirebaseAuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage,
    );
  }

  bool get isAuthenticated => status == FirebaseAuthStatus.authenticated;
  bool get isLoading => status == FirebaseAuthStatus.loading;
}

// Auth notifier
class FirebaseAuthNotifier extends StateNotifier<FirebaseAuthState> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  FirebaseAuthNotifier() : super(const FirebaseAuthState()) {
    _initialize();
  }

  void _initialize() {
    _auth.authStateChanges().listen((user) {
      if (user != null) {
        state = FirebaseAuthState(
          status: FirebaseAuthStatus.authenticated,
          user: user,
        );
      } else {
        state = const FirebaseAuthState(
          status: FirebaseAuthStatus.unauthenticated,
        );
      }
    });
  }

  Future<void> signInWithEmail(String email, String password) async {
    state = state.copyWith(status: FirebaseAuthStatus.loading);
    try {
      final credential = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.authenticated,
        user: credential.user,
      );
    } on FirebaseAuthException catch (e) {
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signUpWithEmail(String email, String password) async {
    state = state.copyWith(status: FirebaseAuthStatus.loading);
    try {
      final credential = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.authenticated,
        user: credential.user,
      );
    } on FirebaseAuthException catch (e) {
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signInWithGoogle() async {
    state = state.copyWith(status: FirebaseAuthStatus.loading);
    try {
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        state = const FirebaseAuthState(
          status: FirebaseAuthStatus.unauthenticated,
        );
        return;
      }

      final googleAuth = await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.authenticated,
        user: userCredential.user,
      );
    } on FirebaseAuthException catch (e) {
      state = FirebaseAuthState(
        status: FirebaseAuthStatus.unauthenticated,
        errorMessage: e.message,
      );
      rethrow;
    }
  }

  Future<void> signOut() async {
    await Future.wait([
      _auth.signOut(),
      _googleSignIn.signOut(),
    ]);
    state = const FirebaseAuthState(
      status: FirebaseAuthStatus.unauthenticated,
    );
  }

  Future<void> resetPassword(String email) async {
    await _auth.sendPasswordResetEmail(email: email);
  }

  Future<void> updatePassword(String newPassword) async {
    await _auth.currentUser?.updatePassword(newPassword);
  }

  Future<void> updateDisplayName(String displayName) async {
    await _auth.currentUser?.updateDisplayName(displayName);
    // Refresh user
    await _auth.currentUser?.reload();
    state = state.copyWith(user: _auth.currentUser);
  }

  Future<void> updatePhotoURL(String photoURL) async {
    await _auth.currentUser?.updatePhotoURL(photoURL);
    await _auth.currentUser?.reload();
    state = state.copyWith(user: _auth.currentUser);
  }
}

// Providers
final firebaseAuthProvider =
    StateNotifierProvider<FirebaseAuthNotifier, FirebaseAuthState>((ref) {
  return FirebaseAuthNotifier();
});

final firebaseCurrentUserProvider = Provider<User?>((ref) {
  return ref.watch(firebaseAuthProvider).user;
});

final firebaseIsAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(firebaseAuthProvider).isAuthenticated;
});
''',
            },
        ],
    )


def _firestore_service() -> Component:
    """Firestore database service."""
    return Component(
        id="firestore_service",
        name="Firestore Service",
        description="Generic Firestore service with CRUD operations",
        category=ComponentCategory.BACKEND,
        tags=["firebase", "firestore", "database", "crud"],
        requires=["firebase_core"],
        dependencies={
            "cloud_firestore": "^4.15.0",
        },
        files=[
            {
                "path": "lib/core/firebase/firestore_service.dart",
                "content": '''import 'package:cloud_firestore/cloud_firestore.dart';

/// Generic Firestore service for database operations
class FirestoreService<T> {
  final String collectionPath;
  final T Function(Map<String, dynamic> json, String id) fromJson;
  final Map<String, dynamic> Function(T item) toJson;

  FirestoreService({
    required this.collectionPath,
    required this.fromJson,
    required this.toJson,
  });

  FirebaseFirestore get _firestore => FirebaseFirestore.instance;
  CollectionReference<Map<String, dynamic>> get _collection =>
      _firestore.collection(collectionPath);

  /// Get all documents
  Future<List<T>> getAll({
    String? orderBy,
    bool descending = false,
    int? limit,
  }) async {
    Query<Map<String, dynamic>> query = _collection;

    if (orderBy != null) {
      query = query.orderBy(orderBy, descending: descending);
    }
    if (limit != null) {
      query = query.limit(limit);
    }

    final snapshot = await query.get();
    return snapshot.docs
        .map((doc) => fromJson(doc.data(), doc.id))
        .toList();
  }

  /// Get a single document by ID
  Future<T?> getById(String id) async {
    final doc = await _collection.doc(id).get();
    if (!doc.exists) return null;
    return fromJson(doc.data()!, doc.id);
  }

  /// Get documents with a filter
  Future<List<T>> getWhere(
    String field,
    dynamic value, {
    String? orderBy,
    bool descending = false,
  }) async {
    Query<Map<String, dynamic>> query = _collection.where(field, isEqualTo: value);

    if (orderBy != null) {
      query = query.orderBy(orderBy, descending: descending);
    }

    final snapshot = await query.get();
    return snapshot.docs
        .map((doc) => fromJson(doc.data(), doc.id))
        .toList();
  }

  /// Create a new document
  Future<T> create(T item, {String? id}) async {
    final data = toJson(item);
    data['createdAt'] = FieldValue.serverTimestamp();
    data['updatedAt'] = FieldValue.serverTimestamp();

    DocumentReference<Map<String, dynamic>> docRef;
    if (id != null) {
      docRef = _collection.doc(id);
      await docRef.set(data);
    } else {
      docRef = await _collection.add(data);
    }

    final doc = await docRef.get();
    return fromJson(doc.data()!, doc.id);
  }

  /// Update a document
  Future<T> update(String id, T item) async {
    final data = toJson(item);
    data['updatedAt'] = FieldValue.serverTimestamp();

    await _collection.doc(id).update(data);

    final doc = await _collection.doc(id).get();
    return fromJson(doc.data()!, doc.id);
  }

  /// Partial update
  Future<T> patch(String id, Map<String, dynamic> fields) async {
    fields['updatedAt'] = FieldValue.serverTimestamp();

    await _collection.doc(id).update(fields);

    final doc = await _collection.doc(id).get();
    return fromJson(doc.data()!, doc.id);
  }

  /// Delete a document
  Future<void> delete(String id) async {
    await _collection.doc(id).delete();
  }

  /// Check if document exists
  Future<bool> exists(String id) async {
    final doc = await _collection.doc(id).get();
    return doc.exists;
  }

  /// Get documents count
  Future<int> count({String? field, dynamic value}) async {
    Query<Map<String, dynamic>> query = _collection;

    if (field != null && value != null) {
      query = query.where(field, isEqualTo: value);
    }

    final snapshot = await query.count().get();
    return snapshot.count ?? 0;
  }

  /// Stream a single document
  Stream<T?> streamById(String id) {
    return _collection.doc(id).snapshots().map((doc) {
      if (!doc.exists) return null;
      return fromJson(doc.data()!, doc.id);
    });
  }

  /// Stream all documents
  Stream<List<T>> streamAll({
    String? orderBy,
    bool descending = false,
    int? limit,
  }) {
    Query<Map<String, dynamic>> query = _collection;

    if (orderBy != null) {
      query = query.orderBy(orderBy, descending: descending);
    }
    if (limit != null) {
      query = query.limit(limit);
    }

    return query.snapshots().map((snapshot) {
      return snapshot.docs
          .map((doc) => fromJson(doc.data(), doc.id))
          .toList();
    });
  }

  /// Batch write
  Future<void> batchWrite(List<BatchOperation<T>> operations) async {
    final batch = _firestore.batch();

    for (final op in operations) {
      switch (op.type) {
        case BatchOperationType.create:
          final data = toJson(op.item as T);
          data['createdAt'] = FieldValue.serverTimestamp();
          data['updatedAt'] = FieldValue.serverTimestamp();
          batch.set(_collection.doc(op.id), data);
          break;
        case BatchOperationType.update:
          final data = toJson(op.item as T);
          data['updatedAt'] = FieldValue.serverTimestamp();
          batch.update(_collection.doc(op.id), data);
          break;
        case BatchOperationType.delete:
          batch.delete(_collection.doc(op.id));
          break;
      }
    }

    await batch.commit();
  }
}

enum BatchOperationType { create, update, delete }

class BatchOperation<T> {
  final BatchOperationType type;
  final String id;
  final T? item;

  BatchOperation.create(this.id, this.item) : type = BatchOperationType.create;
  BatchOperation.update(this.id, this.item) : type = BatchOperationType.update;
  BatchOperation.delete(this.id) : type = BatchOperationType.delete, item = null;
}

// Example usage:
//
// class UserService extends FirestoreService<User> {
//   UserService() : super(
//     collectionPath: 'users',
//     fromJson: (json, id) => User.fromJson({...json, 'id': id}),
//     toJson: (user) => user.toJson()..remove('id'),
//   );
// }
''',
            },
        ],
    )


def _rest_api_client() -> Component:
    """REST API client with Dio."""
    return Component(
        id="rest_api_client",
        name="REST API Client",
        description="HTTP client with Dio for REST API calls",
        category=ComponentCategory.BACKEND,
        tags=["rest", "api", "http", "dio", "client"],
        dependencies={
            "dio": "^5.4.0",
            "flutter_dotenv": "^5.1.0",
        },
        files=[
            {
                "path": "lib/core/api/api_client.dart",
                "content": '''import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiClient {
  static ApiClient? _instance;
  late final Dio _dio;

  ApiClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: dotenv.env['API_BASE_URL'] ?? 'http://localhost:3000',
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
  }

  factory ApiClient() {
    _instance ??= ApiClient._internal();
    return _instance!;
  }

  Dio get dio => _dio;

  /// Add auth token to requests
  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  /// Remove auth token
  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
  }

  /// Add interceptor
  void addInterceptor(Interceptor interceptor) {
    _dio.interceptors.add(interceptor);
  }

  // GET request
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // POST request
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // PUT request
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // PATCH request
  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // DELETE request
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
    );
  }

  // Upload file
  Future<Response<T>> uploadFile<T>(
    String path,
    String filePath, {
    String fieldName = 'file',
    Map<String, dynamic>? extraFields,
    void Function(int, int)? onSendProgress,
    CancelToken? cancelToken,
  }) async {
    final formData = FormData.fromMap({
      fieldName: await MultipartFile.fromFile(filePath),
      if (extraFields != null) ...extraFields,
    });

    return _dio.post<T>(
      path,
      data: formData,
      onSendProgress: onSendProgress,
      cancelToken: cancelToken,
    );
  }

  // Download file
  Future<Response> downloadFile(
    String urlPath,
    String savePath, {
    void Function(int, int)? onReceiveProgress,
    CancelToken? cancelToken,
  }) async {
    return _dio.download(
      urlPath,
      savePath,
      onReceiveProgress: onReceiveProgress,
      cancelToken: cancelToken,
    );
  }
}

// API Response wrapper
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? message;
  final int? statusCode;
  final Map<String, dynamic>? errors;

  ApiResponse({
    required this.success,
    this.data,
    this.message,
    this.statusCode,
    this.errors,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic)? fromJsonT,
  ) {
    return ApiResponse(
      success: json['success'] ?? true,
      data: json['data'] != null && fromJsonT != null
          ? fromJsonT(json['data'])
          : json['data'],
      message: json['message'],
      statusCode: json['statusCode'],
      errors: json['errors'],
    );
  }

  factory ApiResponse.success(T data, {String? message}) {
    return ApiResponse(success: true, data: data, message: message);
  }

  factory ApiResponse.error(String message, {int? statusCode, Map<String, dynamic>? errors}) {
    return ApiResponse(
      success: false,
      message: message,
      statusCode: statusCode,
      errors: errors,
    );
  }
}
''',
            },
        ],
    )


def _api_interceptor() -> Component:
    """Dio interceptors for logging, auth, and error handling."""
    return Component(
        id="api_interceptor",
        name="API Interceptors",
        description="Dio interceptors for logging, auth refresh, and error handling",
        category=ComponentCategory.BACKEND,
        tags=["rest", "api", "interceptor", "dio", "logging"],
        requires=["rest_api_client"],
        dependencies={
            "dio": "^5.4.0",
        },
        files=[
            {
                "path": "lib/core/api/interceptors.dart",
                "content": '''import 'dart:developer' as developer;
import 'package:dio/dio.dart';

/// Logging interceptor
class LoggingInterceptor extends Interceptor {
  final bool request;
  final bool requestHeader;
  final bool requestBody;
  final bool responseHeader;
  final bool responseBody;
  final bool error;

  LoggingInterceptor({
    this.request = true,
    this.requestHeader = true,
    this.requestBody = true,
    this.responseHeader = false,
    this.responseBody = true,
    this.error = true,
  });

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (request) {
      developer.log('*** Request ***');
      developer.log('URI: ${options.uri}');
      developer.log('Method: ${options.method}');
    }
    if (requestHeader) {
      developer.log('Headers: ${options.headers}');
    }
    if (requestBody && options.data != null) {
      developer.log('Body: ${options.data}');
    }
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    developer.log('*** Response ***');
    developer.log('Status: ${response.statusCode}');
    if (responseHeader) {
      developer.log('Headers: ${response.headers}');
    }
    if (responseBody) {
      developer.log('Body: ${response.data}');
    }
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (error) {
      developer.log('*** Error ***');
      developer.log('Message: ${err.message}');
      developer.log('Error: ${err.error}');
      if (err.response != null) {
        developer.log('Response: ${err.response?.data}');
      }
    }
    handler.next(err);
  }
}

/// Auth token refresh interceptor
class AuthInterceptor extends Interceptor {
  final Future<String?> Function() getAccessToken;
  final Future<String?> Function()? refreshToken;
  final void Function()? onAuthError;

  AuthInterceptor({
    required this.getAccessToken,
    this.refreshToken,
    this.onAuthError,
  });

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && refreshToken != null) {
      try {
        final newToken = await refreshToken!();
        if (newToken != null) {
          // Retry the request with new token
          err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          final response = await Dio().fetch(err.requestOptions);
          return handler.resolve(response);
        }
      } catch (e) {
        onAuthError?.call();
      }
    }
    handler.next(err);
  }
}

/// Retry interceptor
class RetryInterceptor extends Interceptor {
  final int maxRetries;
  final Duration retryDelay;
  final List<int> retryStatusCodes;

  RetryInterceptor({
    this.maxRetries = 3,
    this.retryDelay = const Duration(seconds: 1),
    this.retryStatusCodes = const [500, 502, 503, 504],
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final statusCode = err.response?.statusCode;

    if (statusCode != null && retryStatusCodes.contains(statusCode)) {
      int retryCount = err.requestOptions.extra['retryCount'] ?? 0;

      if (retryCount < maxRetries) {
        await Future.delayed(retryDelay * (retryCount + 1));

        err.requestOptions.extra['retryCount'] = retryCount + 1;

        try {
          final response = await Dio().fetch(err.requestOptions);
          return handler.resolve(response);
        } catch (e) {
          // Continue to next retry or final error
        }
      }
    }

    handler.next(err);
  }
}

/// Error formatting interceptor
class ErrorFormattingInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    String message;

    switch (err.type) {
      case DioExceptionType.connectionTimeout:
        message = 'Connection timeout. Please check your internet connection.';
        break;
      case DioExceptionType.sendTimeout:
        message = 'Request timeout. Please try again.';
        break;
      case DioExceptionType.receiveTimeout:
        message = 'Server is taking too long to respond. Please try again.';
        break;
      case DioExceptionType.connectionError:
        message = 'Unable to connect to the server. Please check your internet connection.';
        break;
      case DioExceptionType.badResponse:
        message = _getErrorMessage(err.response);
        break;
      case DioExceptionType.cancel:
        message = 'Request was cancelled.';
        break;
      default:
        message = 'An unexpected error occurred. Please try again.';
    }

    final formattedError = DioException(
      requestOptions: err.requestOptions,
      response: err.response,
      type: err.type,
      error: err.error,
      message: message,
    );

    handler.next(formattedError);
  }

  String _getErrorMessage(Response? response) {
    if (response == null) return 'Server error';

    final data = response.data;
    if (data is Map<String, dynamic>) {
      return data['message'] ?? data['error'] ?? 'Server error';
    }

    switch (response.statusCode) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please login again.';
      case 403:
        return 'You don\\'t have permission to access this resource.';
      case 404:
        return 'Resource not found.';
      case 422:
        return 'Validation error. Please check your input.';
      case 500:
        return 'Internal server error. Please try again later.';
      default:
        return 'Server error (${response.statusCode})';
    }
  }
}
''',
            },
        ],
    )
