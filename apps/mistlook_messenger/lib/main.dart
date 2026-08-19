import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import 'core/config.dart';
import 'data/mistlook_repository.dart';
import 'models/chat_models.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: MistlookApp()));
}

final repositoryProvider = Provider<MistlookRepository>((ref) => MistlookRepository());
final conversationsProvider = FutureProvider<List<Conversation>>((ref) async {
  return ref.read(repositoryProvider).getConversations();
});
final messagesProvider = FutureProvider.family<List<ChatMessage>, String>((ref, id) async {
  return ref.read(repositoryProvider).getMessages(id);
});
final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);

class MistlookApp extends ConsumerWidget {
  const MistlookApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(themeModeProvider);
    const seed = Color(0xFF6657E8);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Mistlook Messenger',
      themeMode: mode,
      theme: _theme(Brightness.light, seed),
      darkTheme: _theme(Brightness.dark, seed),
      home: const SplashPage(),
    );
  }

  ThemeData _theme(Brightness brightness, Color seed) {
    final scheme = ColorScheme.fromSeed(seedColor: seed, brightness: brightness);
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        centerTitle: false,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surfaceContainerHighest.withValues(alpha: .58),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      ),
      cardTheme: CardThemeData(
        color: scheme.surfaceContainerLow,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      ),
    );
  }
}

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    Future<void>.delayed(const Duration(milliseconds: 950), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute<void>(builder: (_) => const LoginPage()),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 78,
              height: 78,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [scheme.primary, scheme.tertiary]),
                borderRadius: BorderRadius.circular(26),
                boxShadow: [
                  BoxShadow(
                    color: scheme.primary.withValues(alpha: .28),
                    blurRadius: 28,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
              child: const Icon(Icons.forum_rounded, color: Colors.white, size: 40),
            ),
            const SizedBox(height: 22),
            Text(
              'mistlook',
              style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: scheme.onSurface),
            ),
            const SizedBox(height: 8),
            Text('Messages that feel like home.', style: TextStyle(color: scheme.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  bool obscurePassword = true;
  bool busy = false;

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Future<void> continueToApp() async {
    setState(() => busy = true);
    await Future<void>.delayed(const Duration(milliseconds: 450));
    if (mounted) {
      Navigator.of(context).pushReplacement(MaterialPageRoute<void>(builder: (_) => const AppShell()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 32, 24, 28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 58,
                    height: 58,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [scheme.primary, scheme.tertiary]),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.forum_rounded, color: Colors.white, size: 30),
                  ),
                  const SizedBox(height: 28),
                  const Text('Welcome back', style: TextStyle(fontSize: 31, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  Text('Sign in with your existing Mistlook account.', style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 15)),
                  const SizedBox(height: 30),
                  TextField(
                    controller: emailController,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(labelText: 'Email address', prefixIcon: Icon(Icons.alternate_email_rounded)),
                  ),
                  const SizedBox(height: 13),
                  TextField(
                    controller: passwordController,
                    obscureText: obscurePassword,
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock_outline_rounded),
                      suffixIcon: IconButton(onPressed: () => setState(() => obscurePassword = !obscurePassword), icon: Icon(obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined)),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () {}, child: const Text('Forgot password?'))),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: busy ? null : continueToApp,
                      icon: busy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_forward_rounded),
                      label: Text(busy ? 'Opening Mistlook…' : 'Sign in'),
                    ),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: busy ? null : continueToApp,
                      icon: const Icon(Icons.g_mobiledata_rounded, size: 28),
                      label: const Text('Continue with Google'),
                    ),
                  ),
                  const SizedBox(height: 28),
                  Center(child: Text('New to Mistlook?', style: TextStyle(color: scheme.onSurfaceVariant))),
                  Center(child: TextButton(onPressed: () {}, child: const Text('Download the Mistlook app to create an account'))),
                  if (AppConfig.demoMode)
                    Center(child: TextButton(onPressed: busy ? null : continueToApp, child: const Text('Preview in demo mode'))),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [const ChatsPage(), const CallsPage(), const SettingsPage()];
    return Scaffold(
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline_rounded),
            selectedIcon: Icon(Icons.chat_bubble_rounded),
            label: 'Chats',
          ),
          NavigationDestination(
            icon: Icon(Icons.phone_outlined),
            selectedIcon: Icon(Icons.phone_rounded),
            label: 'Calls',
          ),
          NavigationDestination(
            icon: Icon(Icons.tune_rounded),
            selectedIcon: Icon(Icons.tune_rounded),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

class ChatsPage extends ConsumerStatefulWidget {
  const ChatsPage({super.key});

  @override
  ConsumerState<ChatsPage> createState() => _ChatsPageState();
}

class _ChatsPageState extends ConsumerState<ChatsPage> {
  String query = '';
  int selectedTab = 0;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final conversations = ref.watch(conversationsProvider);
    return SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  const Avatar(
                    profile: Profile(id: 'me', name: 'S', username: '@you', avatarColor: 0xFF6657E8),
                    radius: 21,
                  ),
                  const SizedBox(width: 13),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Good evening,', style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
                        const SizedBox(height: 1),
                        const Text('Salauddin', style: TextStyle(fontSize: 23, fontWeight: FontWeight.w800)),
                      ],
                    ),
                  ),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.qr_code_2_rounded)),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.edit_rounded)),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
            sliver: SliverToBoxAdapter(
              child: TextField(
                onChanged: (value) => setState(() => query = value),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search_rounded),
                  hintText: 'Search messages and people',
                ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: SizedBox(
              height: 52,
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                scrollDirection: Axis.horizontal,
                children: [
                  _FilterChip(label: 'All', selected: selectedTab == 0, onTap: () => setState(() => selectedTab = 0)),
                  _FilterChip(label: 'Unread', selected: selectedTab == 1, onTap: () => setState(() => selectedTab = 1)),
                  _FilterChip(label: 'Pinned', selected: selectedTab == 2, onTap: () => setState(() => selectedTab = 2)),
                  _FilterChip(
                    label: 'AI chats',
                    icon: Icons.auto_awesome_rounded,
                    selected: selectedTab == 3,
                    onTap: () => setState(() => selectedTab = 3),
                  ),
                ],
              ),
            ),
          ),
          conversations.when(
            loading: () => const SliverFillRemaining(
              hasScrollBody: false,
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (error, stack) => SliverFillRemaining(
              hasScrollBody: false,
              child: _ErrorState(
                message: error.toString(),
                onRetry: () => ref.invalidate(conversationsProvider),
              ),
            ),
            data: (items) {
              final filtered = items.where((item) {
                final normalized = query.toLowerCase();
                final matchesQuery = query.isEmpty ||
                    item.peer.name.toLowerCase().contains(normalized) ||
                    item.preview.toLowerCase().contains(normalized);
                final matchesTab = switch (selectedTab) {
                  1 => item.unread > 0,
                  2 => item.isPinned,
                  3 => item.isAi,
                  _ => true,
                };
                return matchesQuery && matchesTab;
              }).toList();
              if (filtered.isEmpty) {
                return const SliverFillRemaining(hasScrollBody: false, child: _EmptyState());
              }
              return SliverPadding(
                padding: const EdgeInsets.fromLTRB(12, 5, 12, 24),
                sliver: SliverList.builder(
                  itemCount: filtered.length,
                  itemBuilder: (context, index) => ConversationTile(conversation: filtered[index]),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

class ConversationTile extends StatelessWidget {
  const ConversationTile({required this.conversation, super.key});
  final Conversation conversation;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => ChatPage(conversation: conversation)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
        child: Row(
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Avatar(profile: conversation.peer, radius: 27),
                if (conversation.peer.isOnline)
                  Positioned(
                    right: -1,
                    bottom: 0,
                    child: Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: const Color(0xFF20C978),
                        shape: BoxShape.circle,
                        border: Border.all(color: scheme.surface, width: 3),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          conversation.peer.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                        ),
                      ),
                      if (conversation.peer.isVerified) ...[
                        const SizedBox(width: 4),
                        const Icon(Icons.verified_rounded, size: 16, color: Color(0xFF5E62E8)),
                      ],
                      if (conversation.isPinned) ...[
                        const SizedBox(width: 5),
                        Icon(Icons.push_pin_rounded, size: 14, color: scheme.primary),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          conversation.isTyping ? 'typing…' : conversation.preview,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: conversation.isTyping ? scheme.primary : scheme.onSurfaceVariant,
                            fontStyle: conversation.isTyping ? FontStyle.italic : FontStyle.normal,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(conversation.timeLabel, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
                    ],
                  ),
                ],
              ),
            ),
            if (conversation.unread > 0) ...[
              const SizedBox(width: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: scheme.primary, borderRadius: BorderRadius.circular(20)),
                child: Text(
                  '${conversation.unread}',
                  style: TextStyle(color: scheme.onPrimary, fontWeight: FontWeight.w700, fontSize: 11),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({required this.conversation, super.key});
  final Conversation conversation;

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final controller = TextEditingController();
  final scrollController = ScrollController();
  final uuid = const Uuid();
  List<ChatMessage> localMessages = [];
  bool loading = true;
  bool sending = false;

  @override
  void initState() {
    super.initState();
    ref.read(messagesProvider(widget.conversation.id).future).then((items) {
      if (mounted) setState(() { localMessages = items; loading = false; });
    });
  }

  @override
  void dispose() {
    controller.dispose();
    scrollController.dispose();
    super.dispose();
  }

  Future<void> send() async {
    final content = controller.text.trim();
    if (content.isEmpty || sending) return;
    controller.clear();
    final optimistic = ChatMessage(
      id: uuid.v4(),
      conversationId: widget.conversation.id,
      senderId: MistlookRepository.currentUserId,
      content: content,
      createdAt: DateTime.now(),
      status: MessageStatus.sending,
    );
    setState(() { localMessages = [...localMessages, optimistic]; sending = true; });
    _scrollToBottom();
    try {
      final sent = await ref.read(repositoryProvider).sendMessage(
        conversationId: widget.conversation.id,
        content: content,
      );
      if (mounted) {
        setState(() {
          localMessages = [...localMessages.where((m) => m.id != optimistic.id), sent];
          sending = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => sending = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (scrollController.hasClients) {
        scrollController.animateTo(
          scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_back_rounded)),
        titleSpacing: 0,
        title: Row(
          children: [
            Avatar(profile: widget.conversation.peer, radius: 20),
            const SizedBox(width: 11),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(widget.conversation.peer.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                    if (widget.conversation.peer.isVerified) ...[
                      const SizedBox(width: 4),
                      const Icon(Icons.verified_rounded, size: 15, color: Color(0xFF5E62E8)),
                    ],
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  widget.conversation.peer.isOnline ? 'Active now' : 'Last seen recently',
                  style: TextStyle(
                    fontSize: 11,
                    color: widget.conversation.peer.isOnline ? const Color(0xFF20A968) : scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.phone_outlined)),
          IconButton(onPressed: () {}, icon: const Icon(Icons.videocam_outlined)),
          PopupMenuButton<String>(
            onSelected: (_) {},
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'search', child: Text('Search in chat')),
              PopupMenuItem(value: 'mute', child: Text('Mute notifications')),
              PopupMenuItem(value: 'theme', child: Text('Chat theme')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : localMessages.isEmpty
                    ? const _EmptyChat()
                    : ListView.builder(
                        controller: scrollController,
                        padding: const EdgeInsets.fromLTRB(16, 18, 16, 18),
                        itemCount: localMessages.length,
                        itemBuilder: (context, index) {
                          final message = localMessages[index];
                          return MessageBubble(
                            message: message,
                            isMine: message.isMine(MistlookRepository.currentUserId),
                          );
                        },
                      ),
          ),
          _Composer(controller: controller, onSend: send, onChanged: (_) {}),
        ],
      ),
    );
  }
}

class MessageBubble extends StatelessWidget {
  const MessageBubble({required this.message, required this.isMine, super.key});
  final ChatMessage message;
  final bool isMine;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final bubbleColor = isMine ? scheme.primary : scheme.surfaceContainerHighest;
    final textColor = isMine ? scheme.onPrimary : scheme.onSurface;
    return Align(
      alignment: isMine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 320),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.fromLTRB(15, 11, 13, 8),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: Radius.circular(isMine ? 20 : 5),
            bottomRight: Radius.circular(isMine ? 5 : 20),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (message.isAiReply)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.auto_awesome_rounded, size: 14, color: scheme.tertiary),
                  const SizedBox(width: 5),
                  Text('Misty AI', style: TextStyle(color: scheme.tertiary, fontWeight: FontWeight.w700, fontSize: 11)),
                  const SizedBox(width: 8),
                ],
              ),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(message.content, style: TextStyle(color: textColor, fontSize: 15, height: 1.35)),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(message.timeLabel, style: TextStyle(color: textColor.withValues(alpha: .68), fontSize: 10)),
                if (isMine) ...[
                  const SizedBox(width: 5),
                  Icon(
                    message.status == MessageStatus.sending ? Icons.schedule_rounded : Icons.done_all_rounded,
                    size: 14,
                    color: message.status == MessageStatus.read ? const Color(0xFF8FE9FF) : textColor.withValues(alpha: .68),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.onSend, required this.onChanged});
  final TextEditingController controller;
  final VoidCallback onSend;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 5, 12, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            IconButton(onPressed: () {}, icon: const Icon(Icons.add_circle_outline_rounded)),
            Expanded(
              child: TextField(
                controller: controller,
                onChanged: onChanged,
                minLines: 1,
                maxLines: 5,
                textInputAction: TextInputAction.newline,
                decoration: const InputDecoration(
                  hintText: 'Write a message…',
                  prefixIcon: Icon(Icons.emoji_emotions_outlined),
                  suffixIcon: Icon(Icons.mic_none_rounded),
                ),
              ),
            ),
            const SizedBox(width: 8),
            ValueListenableBuilder<TextEditingValue>(
              valueListenable: controller,
              builder: (context, value, _) {
                final enabled = value.text.trim().isNotEmpty;
                return IconButton(
                  onPressed: enabled ? onSend : null,
                  style: IconButton.styleFrom(
                    backgroundColor: enabled ? scheme.primary : scheme.surfaceContainerHighest,
                    foregroundColor: enabled ? scheme.onPrimary : scheme.onSurfaceVariant,
                  ),
                  icon: const Icon(Icons.arrow_upward_rounded),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class CallsPage extends StatelessWidget {
  const CallsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  const Expanded(child: Text('Calls', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800))),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.search_rounded)),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            sliver: SliverToBoxAdapter(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(color: scheme.primaryContainer, shape: BoxShape.circle),
                        child: Icon(Icons.videocam_rounded, color: scheme.primary),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Crystal-clear calls', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                            SizedBox(height: 4),
                            Text('Start a secure audio or video call.', style: TextStyle(fontSize: 13)),
                          ],
                        ),
                      ),
                      IconButton(onPressed: () {}, icon: const Icon(Icons.arrow_forward_rounded)),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SliverToBoxAdapter(
            child: Padding(
              padding: EdgeInsets.fromLTRB(20, 28, 20, 12),
              child: Text('Recent', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            sliver: SliverList.list(
              children: const [
                _CallTile(name: 'Maya Rahman', time: 'Yesterday, 8:42 PM', incoming: true, video: true),
                _CallTile(name: 'Arif Hasan', time: 'Monday, 11:10 AM', incoming: false, video: false),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CallTile extends StatelessWidget {
  const _CallTile({required this.name, required this.time, required this.incoming, required this.video});
  final String name;
  final String time;
  final bool incoming;
  final bool video;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListTile(
      leading: const Avatar(
        profile: Profile(id: 'call', name: 'Maya Rahman', username: '@maya', avatarColor: 0xFF8B5CF6),
        radius: 24,
      ),
      title: Text(name, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Row(
        children: [
          Icon(incoming ? Icons.call_received_rounded : Icons.call_made_rounded, size: 14, color: incoming ? const Color(0xFF20A968) : scheme.error),
          const SizedBox(width: 5),
          Text(time),
        ],
      ),
      trailing: IconButton(onPressed: () {}, icon: Icon(video ? Icons.videocam_outlined : Icons.phone_outlined)),
    );
  }
}

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    final mode = ref.watch(themeModeProvider);
    return SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 12),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  const Expanded(child: Text('Settings', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800))),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.help_outline_rounded)),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            sliver: SliverToBoxAdapter(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    children: [
                      const Avatar(
                        profile: Profile(id: 'me', name: 'Salauddin Mir', username: '@salauddin', avatarColor: 0xFF6657E8),
                        radius: 29,
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Salauddin Mir', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                            SizedBox(height: 3),
                            Text('@salauddinmir', style: TextStyle(fontSize: 13)),
                          ],
                        ),
                      ),
                      IconButton(onPressed: () {}, icon: const Icon(Icons.chevron_right_rounded)),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
            sliver: SliverToBoxAdapter(
              child: Text('Preferences', style: TextStyle(color: scheme.primary, fontWeight: FontWeight.w700)),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            sliver: SliverList.list(
              children: [
                ListTile(
                  leading: const Icon(Icons.dark_mode_outlined),
                  title: const Text('Appearance'),
                  subtitle: Text(mode == ThemeMode.dark ? 'Dark mode' : mode == ThemeMode.light ? 'Light mode' : 'System default'),
                  trailing: Switch(
                    value: mode == ThemeMode.dark,
                    onChanged: (value) => ref.read(themeModeProvider.notifier).state = value ? ThemeMode.dark : ThemeMode.light,
                  ),
                ),
                const ListTile(leading: Icon(Icons.notifications_none_rounded), title: Text('Notifications'), subtitle: Text('Messages, calls and mentions')),
                const ListTile(leading: Icon(Icons.lock_outline_rounded), title: Text('Privacy and security'), subtitle: Text('Read receipts, disappearing messages, blocked users')),
                const ListTile(leading: Icon(Icons.palette_outlined), title: Text('Chat themes'), subtitle: Text('Personalize every conversation')),
                const ListTile(leading: Icon(Icons.storage_outlined), title: Text('Storage and cache'), subtitle: Text('50 MB media cache · Clear cache')),
              ],
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 30),
            sliver: SliverToBoxAdapter(
              child: Center(
                child: Text(
                  'Mistlook Messenger ${AppConfig.demoMode ? '· Demo mode' : ''}',
                  style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class Avatar extends StatelessWidget {
  const Avatar({required this.profile, required this.radius, super.key});
  final Profile profile;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: radius,
      backgroundColor: Color(profile.avatarColor),
      child: Text(
        profile.initials,
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: radius * .65),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({required this.label, required this.selected, required this.onTap, this.icon});
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        selected: selected,
        onSelected: (_) => onTap(),
        avatar: icon == null ? null : Icon(icon, size: 16),
        label: Text(label),
        labelStyle: TextStyle(
          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          color: selected ? scheme.onSecondaryContainer : scheme.onSurfaceVariant,
        ),
        side: BorderSide(color: selected ? Colors.transparent : scheme.outlineVariant),
        backgroundColor: scheme.surface,
        selectedColor: scheme.secondaryContainer,
        showCheckmark: false,
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();
  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.forum_outlined, size: 46),
            SizedBox(height: 12),
            Text('No conversations found', style: TextStyle(fontWeight: FontWeight.w700)),
            SizedBox(height: 6),
            Text('Try a different search or start a new chat.', textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();
  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.waving_hand_outlined, size: 42),
          SizedBox(height: 12),
          Text('Start the conversation', style: TextStyle(fontWeight: FontWeight.w700)),
          SizedBox(height: 5),
          Text('Messages are end-to-end ready when you are.'),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off_rounded, size: 44),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 14),
            FilledButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
