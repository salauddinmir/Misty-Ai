import 'package:intl/intl.dart';

class Profile {
  const Profile({
    required this.id,
    required this.name,
    required this.username,
    required this.avatarColor,
    this.isOnline = false,
    this.isVerified = false,
  });

  final String id;
  final String name;
  final String username;
  final int avatarColor;
  final bool isOnline;
  final bool isVerified;

  String get initials {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return '${parts.first.substring(0, 1)}${parts.last.substring(0, 1)}'.toUpperCase();
  }
}

class Conversation {
  const Conversation({
    required this.id,
    required this.peer,
    required this.preview,
    required this.updatedAt,
    this.unread = 0,
    this.isPinned = false,
    this.isMuted = false,
    this.isTyping = false,
    this.isAi = false,
  });

  final String id;
  final Profile peer;
  final String preview;
  final DateTime updatedAt;
  final int unread;
  final bool isPinned;
  final bool isMuted;
  final bool isTyping;
  final bool isAi;

  String get timeLabel {
    final now = DateTime.now();
    if (now.difference(updatedAt).inDays == 0) return DateFormat('h:mm a').format(updatedAt);
    if (now.difference(updatedAt).inDays < 7) return DateFormat('EEE').format(updatedAt);
    return DateFormat('d MMM').format(updatedAt);
  }
}

enum MessageStatus { sending, sent, delivered, read, failed }

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderId,
    required this.content,
    required this.createdAt,
    this.status = MessageStatus.read,
    this.isEdited = false,
    this.reaction,
    this.replyPreview,
    this.isAiReply = false,
  });

  final String id;
  final String conversationId;
  final String senderId;
  final String content;
  final DateTime createdAt;
  final MessageStatus status;
  final bool isEdited;
  final String? reaction;
  final String? replyPreview;
  final bool isAiReply;

  bool isMine(String userId) => senderId == userId;
  String get timeLabel => DateFormat('h:mm a').format(createdAt);
}
