import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class LocalCache {
  LocalCache(this._preferences);

  final SharedPreferences _preferences;

  static Future<LocalCache> create() async {
    return LocalCache(await SharedPreferences.getInstance());
  }

  Future<void> saveJson(String key, Object value) async {
    await _preferences.setString(key, jsonEncode(value));
  }

  List<Map<String, dynamic>> readList(String key) {
    final raw = _preferences.getString(key);
    if (raw == null) return <Map<String, dynamic>>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return <Map<String, dynamic>>[];
      return decoded.map((item) => Map<String, dynamic>.from(item as Map)).toList();
    } catch (_) {
      return <Map<String, dynamic>>[];
    }
  }

  Future<void> remove(String key) => _preferences.remove(key);
}

class OutboxItem {
  const OutboxItem({
    required this.clientMessageId,
    required this.conversationId,
    required this.content,
    required this.createdAt,
    this.attempts = 0,
    this.nextAttemptAt,
  });

  final String clientMessageId;
  final String conversationId;
  final String content;
  final DateTime createdAt;
  final int attempts;
  final DateTime? nextAttemptAt;

  Map<String, dynamic> toJson() => {
        'client_msg_id': clientMessageId,
        'conversation_id': conversationId,
        'content': content,
        'created_at': createdAt.toIso8601String(),
        'attempts': attempts,
        'next_attempt_at': nextAttemptAt?.toIso8601String(),
      };

  factory OutboxItem.fromJson(Map<String, dynamic> json) => OutboxItem(
        clientMessageId: '${json['client_msg_id']}',
        conversationId: '${json['conversation_id']}',
        content: '${json['content']}',
        createdAt: DateTime.tryParse('${json['created_at']}') ?? DateTime.now(),
        attempts: (json['attempts'] as num?)?.toInt() ?? 0,
        nextAttemptAt: DateTime.tryParse('${json['next_attempt_at']}'),
      );
}

class OutboxStore {
  OutboxStore(this._cache);

  static const key = 'mistlook.outbox.v1';
  final LocalCache _cache;

  List<OutboxItem> readAll() {
    return _cache.readList(key).map(OutboxItem.fromJson).toList();
  }

  Future<void> replaceAll(List<OutboxItem> items) async {
    await _cache.saveJson(key, items.map((item) => item.toJson()).toList());
  }

  Future<void> enqueue(OutboxItem item) async {
    final items = readAll()..add(item);
    await replaceAll(items);
  }

  Future<void> removeByClientId(String clientMessageId) async {
    final items = readAll()..removeWhere((item) => item.clientMessageId == clientMessageId);
    await replaceAll(items);
  }
}
