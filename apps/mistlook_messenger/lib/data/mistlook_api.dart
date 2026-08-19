import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/config.dart';

class MistlookApiException implements Exception {
  const MistlookApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'MistlookApiException($statusCode): $message';
}

class MistlookApiClient {
  MistlookApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? accessToken;

  Map<String, String> get _headers => {
        'apikey': AppConfig.anonKey,
        'Authorization': 'Bearer ${accessToken ?? ''}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  Future<List<Map<String, dynamic>>> fetchConversations({required String userId, int limit = 30}) async {
    final uri = Uri.parse('${AppConfig.restBase}/conversations').replace(queryParameters: {
      'select': 'id,participant_one_id,participant_two_id,last_message_at,last_message_content,last_message_sender_id,is_ai_persona_chat,ai_persona_id',
      'or': '(participant_one_id.eq.$userId,participant_two_id.eq.$userId)',
      'order': 'last_message_at.desc',
      'limit': '$limit',
    });
    return _getList(uri);
  }

  Future<List<Map<String, dynamic>>> fetchMessages({required String conversationId, String? before, int limit = 30}) async {
    final parameters = <String, String>{
      'select': 'id,conversation_id,sender_id,content,created_at,updated_at,message_type,attachment_url,attachment_thumbnail_url,delivered_at,read_at,local_status,client_msg_id,replied_to_message_id,is_edited,is_deleted,deleted_for_everyone',
      'conversation_id': 'eq.$conversationId',
      'order': 'created_at.desc',
      'limit': '$limit',
    };
    if (before != null) parameters['created_at'] = 'lt.$before';
    final uri = Uri.parse('${AppConfig.restBase}/messages').replace(queryParameters: parameters);
    return _getList(uri);
  }

  Future<Map<String, dynamic>> insertMessage(Map<String, dynamic> payload) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.restBase}/messages'),
      headers: {..._headers, 'Prefer': 'return=representation'},
      body: jsonEncode(payload),
    );
    final value = _decode(response);
    if (value is List && value.isNotEmpty) return Map<String, dynamic>.from(value.first as Map);
    if (value is Map<String, dynamic>) return value;
    throw MistlookApiException(response.statusCode, 'Unexpected message response');
  }

  Future<Map<String, dynamic>> callFunction(String name, Map<String, dynamic> payload) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.functionsBase}/$name'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    final value = _decode(response);
    if (value is Map<String, dynamic>) return value;
    throw MistlookApiException(response.statusCode, 'Unexpected function response');
  }

  Future<List<Map<String, dynamic>>> _getList(Uri uri) async {
    final response = await _client.get(uri, headers: _headers);
    final value = _decode(response);
    if (value is List) return value.map((item) => Map<String, dynamic>.from(item as Map)).toList();
    throw MistlookApiException(response.statusCode, 'Expected a list response');
  }

  dynamic _decode(http.Response response) {
    dynamic value;
    try {
      value = response.body.isEmpty ? <String, dynamic>{} : jsonDecode(response.body);
    } catch (_) {
      value = <String, dynamic>{'error': response.body};
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = value is Map ? '${value['error'] ?? value['message'] ?? response.reasonPhrase ?? 'Request failed'}' : (response.reasonPhrase ?? 'Request failed');
      throw MistlookApiException(response.statusCode, message);
    }
    return value;
  }
}
