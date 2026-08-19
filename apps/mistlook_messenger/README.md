# Mistlook Messenger

Mistlook Messenger is a Flutter/Dart client foundation for a faster, privacy-first messaging experience built on the existing Mistlook backend. The client follows the supplied `MISTLOOK_MESSENGER_FLUTTER_SPEC.md` rules: it does not create backend tables or functions, does not contain service-role secrets, and keeps the UI ready for cache-first reads, optimistic sends, realtime relay, and secure media flows.

## Current milestone

The current implementation includes a Material 3 design system with light and dark mode, splash/session entry, existing-user login UI, chat list search and filters, unread and pinned states, verified and presence indicators, responsive chat bubbles, optimistic message sending, calls and settings surfaces, a demo repository, explicit-column REST API client, cache and outbox primitives, and a websocket relay client with heartbeat and reconnect scaffolding.

The application defaults to `MISTLOOK_DEMO_MODE=true` so it can be previewed without backend credentials. Demo mode intentionally uses local sample conversations and does not attempt network authentication.

## Run locally

```bash
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=MISTLOOK_DEMO_MODE=true
```

For backend-connected builds, inject only the publishable/anon key and keep all secrets out of the app:

```bash
flutter run \
  --dart-define=MISTLOOK_DEMO_MODE=false \
  --dart-define=SUPABASE_ANON_KEY=your_publishable_key
```

The endpoints are defined in `lib/core/config.dart`. The REST client is in `lib/data/mistlook_api.dart`, the local cache and offline outbox primitives are in `lib/data/local_cache.dart`, and the relay protocol client is in `lib/data/realtime_relay.dart`.

## Architecture

| Area | Location | Purpose |
|---|---|---|
| Configuration | `lib/core/config.dart` | Build-time endpoint and key injection |
| Domain models | `lib/models/chat_models.dart` | Profiles, conversations, messages, statuses |
| Demo/data adapter | `lib/data/mistlook_repository.dart` | Preview data and optimistic send simulation |
| REST | `lib/data/mistlook_api.dart` | Explicit-column PostgREST and Edge Function calls |
| Cache/outbox | `lib/data/local_cache.dart` | SharedPreferences JSON cache and retryable outbox records |
| Realtime | `lib/data/realtime_relay.dart` | One socket, heartbeat, subscriptions, reconnect |
| UI | `lib/main.dart` | Material 3 screens and interaction shell |

## Next implementation milestones

The next production pass should wire `supabase_flutter` session restoration into the login screen, connect Riverpod state to the REST/cache adapters, add connectivity-aware outbox draining, and then layer in media upload, push/deep links, LiveKit calls, reactions, search, groups, and the optional E2EE feature flag. The backend remains the source of truth for membership, RLS, message delivery, and call authorization.
