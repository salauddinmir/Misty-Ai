import 'package:supabase_flutter/supabase_flutter.dart';

import '../core/config.dart';

class AuthService {
  AuthService._();

  static bool _initialized = false;

  static Future<void> initialize() async {
    if (_initialized || AppConfig.demoMode || AppConfig.anonKey.isEmpty) return;
    await Supabase.initialize(url: AppConfig.apiBase, publishableKey: AppConfig.anonKey);
    _initialized = true;
  }

  static Session? get session {
    if (!_initialized) return null;
    return Supabase.instance.client.auth.currentSession;
  }

  static Future<AuthResponse> signInWithPassword({required String email, required String password}) async {
    await initialize();
    if (!_initialized) throw const AuthException('Backend auth is not configured for this build.');
    return Supabase.instance.client.auth.signInWithPassword(email: email, password: password);
  }

  static Future<bool> hasRestorableSession() async {
    await initialize();
    return session != null;
  }

  static Future<void> signOut() async {
    if (_initialized) await Supabase.instance.client.auth.signOut();
  }
}
