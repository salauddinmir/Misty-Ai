class AppConfig {
  const AppConfig._();

  static const apiBase = String.fromEnvironment(
    'MISTLOOK_API_BASE',
    defaultValue: 'https://db.mistlook.com',
  );
  static const wsUrl = String.fromEnvironment(
    'MISTLOOK_WS_URL',
    defaultValue: 'wss://ws.mistlook.com',
  );
  static const cdnBase = String.fromEnvironment(
    'MISTLOOK_CDN_BASE',
    defaultValue: 'https://cdn.mistlook.com',
  );
  static const anonKey = String.fromEnvironment('SUPABASE_ANON_KEY');
  static const demoMode = bool.fromEnvironment('MISTLOOK_DEMO_MODE', defaultValue: true);

  static String get restBase => '$apiBase/rest/v1';
  static String get authBase => '$apiBase/auth/v1';
  static String get functionsBase => '$apiBase/functions/v1';
}
