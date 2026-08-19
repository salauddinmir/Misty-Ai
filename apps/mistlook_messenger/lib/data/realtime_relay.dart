import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/config.dart';
import 'mistlook_api.dart';

class RealtimeRelay {
  RealtimeRelay({required this.api});

  final MistlookApiClient api;
  WebSocketChannel? _channel;
  Timer? _heartbeat;
  Timer? _reconnect;
  int _attempt = 0;
  bool _closed = false;
  final Set<String> _conversations = <String>{};
  final Set<String> _users = <String>{};
  final StreamController<Map<String, dynamic>> _events = StreamController.broadcast();

  Stream<Map<String, dynamic>> get events => _events.stream;

  Future<void> connect() async {
    _closed = false;
    final tokenResponse = await api.callFunction('ws-issue-token', {'device_id': 'flutter-device'});
    final token = tokenResponse['token'] as String?;
    final url = (tokenResponse['ws_url'] as String?) ?? AppConfig.wsUrl;
    if (token == null || token.isEmpty) return;
    _channel = WebSocketChannel.connect(Uri.parse('$url/?token=$token'));
    _attempt = 0;
    _channel!.stream.listen(_onFrame, onDone: _scheduleReconnect, onError: (_) => _scheduleReconnect());
    _heartbeat?.cancel();
    _heartbeat = Timer.periodic(const Duration(seconds: 25), (_) => _send({'type': 'ping', 't': DateTime.now().millisecondsSinceEpoch}));
    for (final id in _conversations) {
      subscribeConversation(id);
    }
    for (final id in _users) {
      subscribeUser(id);
    }
  }

  void subscribeConversation(String id) {
    _conversations.add(id);
    _send({'type': 'subscribe_conv', 'conv_id': id});
  }

  void unsubscribeConversation(String id) {
    _conversations.remove(id);
    _send({'type': 'unsubscribe_conv', 'conv_id': id});
  }

  void subscribeUser(String id) {
    _users.add(id);
    _send({'type': 'subscribe_user', 'user_id': id});
  }

  void sendRelay(String channel, Map<String, dynamic> payload) {
    _send({'type': 'relay', 'channel': channel, 'payload': payload});
  }

  void _send(Map<String, dynamic> frame) {
    _channel?.sink.add(jsonEncode(frame));
  }

  void _onFrame(dynamic raw) {
    if (raw is! String) return;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map) _events.add(Map<String, dynamic>.from(decoded));
    } catch (_) {
      // Ignore malformed relay frames; the database remains the source of truth.
    }
  }

  void _scheduleReconnect() {
    if (_closed || _reconnect?.isActive == true) return;
    _heartbeat?.cancel();
    const delays = [1, 2, 5, 10, 30];
    final seconds = delays[_attempt.clamp(0, delays.length - 1)];
    _attempt++;
    _reconnect = Timer(Duration(seconds: seconds), () => connect());
  }

  Future<void> dispose() async {
    _closed = true;
    _reconnect?.cancel();
    _heartbeat?.cancel();
    await _channel?.sink.close();
    await _events.close();
  }
}
