import 'package:uuid/uuid.dart';

import '../models/chat_models.dart';

class MistlookRepository {
  MistlookRepository() {
    _seed();
  }

  static const currentUserId = 'me';
  final _uuid = const Uuid();
  final Map<String, List<ChatMessage>> _messages = {};
  late final List<Conversation> _conversations;

  void _seed() {
    final now = DateTime.now();
    const maya = Profile(
      id: 'maya',
      name: 'Maya Rahman',
      username: '@maya.rahman',
      avatarColor: 0xFF8B5CF6,
      isOnline: true,
      isVerified: true,
    );
    const arif = Profile(
      id: 'arif',
      name: 'Arif Hasan',
      username: '@arifhasan',
      avatarColor: 0xFF0EA5E9,
      isOnline: false,
    );
    const misty = Profile(
      id: 'misty',
      name: 'Misty AI',
      username: '@misty',
      avatarColor: 0xFF14B8A6,
      isOnline: true,
      isVerified: true,
    );
    const nabila = Profile(
      id: 'nabila',
      name: 'Nabila Chowdhury',
      username: '@nabilac',
      avatarColor: 0xFFF97316,
      isOnline: true,
    );

    _conversations = [
      Conversation(
        id: 'c-maya',
        peer: maya,
        preview: 'The new design looks incredible. Let’s ship it.',
        updatedAt: now.subtract(const Duration(minutes: 4)),
        unread: 2,
        isPinned: true,
      ),
      Conversation(
        id: 'c-misty',
        peer: misty,
        preview: 'I found three ways to make your launch smoother.',
        updatedAt: now.subtract(const Duration(minutes: 19)),
        isAi: true,
      ),
      Conversation(
        id: 'c-arif',
        peer: arif,
        preview: 'Voice message',
        updatedAt: now.subtract(const Duration(hours: 2)),
        isMuted: true,
      ),
      Conversation(
        id: 'c-nabila',
        peer: nabila,
        preview: 'See you at the studio tomorrow.',
        updatedAt: now.subtract(const Duration(days: 1)),
      ),
    ];

    _messages['c-maya'] = [
      ChatMessage(
        id: 'm1',
        conversationId: 'c-maya',
        senderId: 'maya',
        content: 'Hey! Did you get a chance to look at the new Mistlook concept?',
        createdAt: now.subtract(const Duration(minutes: 25)),
      ),
      ChatMessage(
        id: 'm2',
        conversationId: 'c-maya',
        senderId: currentUserId,
        content: 'Just opened it. The focus mode and offline queue are exactly what we needed.',
        createdAt: now.subtract(const Duration(minutes: 22)),
      ),
      ChatMessage(
        id: 'm3',
        conversationId: 'c-maya',
        senderId: 'maya',
        content: 'The new design looks incredible. Let’s ship it.',
        createdAt: now.subtract(const Duration(minutes: 4)),
      ),
    ];
    _messages['c-misty'] = [
      ChatMessage(
        id: 'm4',
        conversationId: 'c-misty',
        senderId: 'misty',
        content: 'Welcome to Mistlook. I can help summarize chats, translate messages, or draft a reply.',
        createdAt: now.subtract(const Duration(hours: 1)),
        isAiReply: true,
      ),
    ];
    _messages['c-arif'] = [
      ChatMessage(
        id: 'm5',
        conversationId: 'c-arif',
        senderId: 'arif',
        content: 'Let’s review the launch checklist after lunch.',
        createdAt: now.subtract(const Duration(hours: 2)),
      ),
    ];
    _messages['c-nabila'] = [
      ChatMessage(
        id: 'm6',
        conversationId: 'c-nabila',
        senderId: 'nabila',
        content: 'See you at the studio tomorrow.',
        createdAt: now.subtract(const Duration(days: 1)),
      ),
    ];
  }

  Future<List<Conversation>> getConversations() async {
    await Future<void>.delayed(const Duration(milliseconds: 250));
    return List<Conversation>.of(_conversations);
  }

  Future<List<ChatMessage>> getMessages(String conversationId) async {
    await Future<void>.delayed(const Duration(milliseconds: 180));
    return List<ChatMessage>.of(_messages[conversationId] ?? <ChatMessage>[]);
  }

  Future<ChatMessage> sendMessage({required String conversationId, required String content}) async {
    await Future<void>.delayed(const Duration(milliseconds: 320));
    final message = ChatMessage(
      id: _uuid.v4(),
      conversationId: conversationId,
      senderId: currentUserId,
      content: content,
      createdAt: DateTime.now(),
      status: MessageStatus.read,
    );
    (_messages[conversationId] ??= <ChatMessage>[]).add(message);
    return message;
  }
}
