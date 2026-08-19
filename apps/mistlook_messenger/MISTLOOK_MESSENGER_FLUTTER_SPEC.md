# Mistlook Messenger — Flutter App Full Build Spec

Give this whole document to the Google (Project IDX / Gemini) agent.
It is a **client-only** brief: the backend already exists and must NOT be rebuilt.

---

## 0. Scope & Rules for the Agent

**Build:** A pure-native-feel Flutter (Dart 3, Material 3) messenger app for **existing Mistlook users only** (like Facebook Messenger — no independent signup).

**Hard rules**

1. Do **not** create a new backend, new tables, or new edge functions. Use the endpoints in this document exactly.
2. Do **not** put any service-role key, R2 secret, LiveKit secret, or WS JWT secret in the app. The app only ever holds the anon/publishable key + the user's session JWT.
3. All writes go through PostgREST/RPC with the **user's** JWT so RLS applies.
4. Registration is disabled in this app. Only **login** (email/password + Google) and **session restore**.
5. Offline-first: every read renders from local cache first, then refreshes.
6. Target: Android (min SDK 24) + iOS 14+, 60fps lists, cold start < 2s to conversation list.

---

## 1. Backend Endpoints (constants)

```dart
// lib/core/config.dart
const kApiBase   = 'https://db.mistlook.com';           // Supabase REST/Auth/Functions
const kRestBase  = '$kApiBase/rest/v1';
const kAuthBase  = '$kApiBase/auth/v1';
const kFnBase    = '$kApiBase/functions/v1';
const kWsUrl     = 'wss://ws.mistlook.com';             // realtime relay (also returned by ws-issue-token)
const kCdnBase   = 'https://cdn.mistlook.com';          // media delivery (R2 behind Cloudflare)
const kAnonKey   = String.fromEnvironment('SUPABASE_ANON_KEY'); // inject at build time
```

* Auth = Supabase Auth (GoTrue). Use `supabase_flutter` initialised with `kApiBase` + anon key.
* Every REST call carries `apikey: <anon>` + `Authorization: Bearer <user access_token>`.
* Session must persist across restarts and auto-refresh; on refresh failure show login, **never** silently wipe cache.

---

## 2. Data Model (existing tables — read/write via PostgREST)

Only the columns the messenger needs are listed. Never `SELECT *` — always list columns.

### 2.1 `conversations` (1:1)
`id uuid`, `participant_one_id uuid`, `participant_two_id uuid`, `created_at`, `updated_at`,
`last_message_at`, `last_message_content text`, `last_message_sender_id uuid`,
`is_ai_persona_chat bool`, `ai_persona_id uuid`, `chat_state text`,
`context_type text`, `context_id uuid`, `context_preview jsonb`, `wallpaper_settings jsonb`

> **Critical:** `last_message_*` and `last_message_at` are written by a DB trigger
> (`update_conversation_timestamp`) when a message is inserted. The client must **never**
> UPDATE those columns from the send path.

### 2.2 `chat_groups` + `group_members` + `group_messages`
* `group_members`: `id`, `group_id`, `user_id`, `role text` (`owner|admin|member`), `nickname`, `is_muted`, `muted_until`, `joined_at`, `last_read_at`.
* Group conversation ids are `chat_groups.id`; the relay accepts either shape on `conv:{id}`.

### 2.3 `messages` (the main table)
Core: `id uuid`, `conversation_id uuid`, `sender_id uuid`, `content text NOT NULL`, `created_at`, `updated_at`,
`message_type text` (`text|image|video|audio|file|sticker|gif|call|system`), `is_edited`, `edited_at`, `original_content`.

Attachments: `attachment_url`, `attachment_urls text[]`, `attachment_type`, `attachment_name`, `attachment_size bigint`,
`attachment_duration int`, `attachment_thumbnail_url`, `attachment_waveform real[]`, `blurhash`, `media_url`, `media_group_id uuid`, `file_category`, `file_intent`, `download_allowed bool`, `one_time_view bool`.

Delivery: `delivered_at`, `read_at`, `local_status text` (`sending|sent|delivered|read|failed`), `client_msg_id text`, `preview_b64 text`, `ack_at`.

Replies/forward/pin: `replied_to_message_id`, `reply_to_id`, `is_forwarded`, `forwarded_from_id`, `is_pinned`, `pinned_at`, `pinned_by`.

Deletion & ephemeral: `is_deleted`, `deleted_for_everyone`, `deleted_for uuid[]`, `is_ephemeral`, `expires_at`, `is_disappearing`, `disappear_at`, `lifetime_choice`.

AI / extras: `is_ai_reply`, `ai_persona_id`, `ai_translated_content`, `sentiment_score`, `message_effect`, `scheduled_at`, `scheduled_status`, `call_metadata jsonb`.

E2EE: `e2ee_envelope jsonb`, `e2ee_algo text`.

### 2.4 Support tables
| Table | Purpose | Key columns |
|---|---|---|
| `conversation_settings` | per-user per-conversation prefs | `conversation_id`, `user_id`, `is_muted`, `is_archived`, `is_locked`, `is_deleted`, `theme_color`, `custom_nickname`, `disappearing_messages_enabled/_duration`, `read_receipts_enabled`, `smart_reply_enabled`, `last_read_message_id` |
| `message_reactions` | emoji reactions | `message_id`, `user_id`, `reaction_type` |
| `message_read_receipts` / `message_read_status` | read state | `message_id`, `user_id`, timestamps |
| `starred_messages` | saved messages | `message_id`, `user_id` |
| `chat_folders` | custom folders/tabs | `user_id`, `name`, `icon`, `color`, `filter_type`, `conversation_ids uuid[]`, `position` |
| `chat_themes`, `chat_lists`, `chat_identities` | wallpapers/themes | — |
| `scheduled_messages` | send-later queue | — |
| `muted_conversations`, `blocked_users` | mute/block | `blocker_id`, `blocked_id` |
| `messenger_device_keys` | E2EE public keys per device | `user_id`, `device_id`, public key material |
| `voice_messages` | voice note metadata | — |
| `group_calls`, `group_call_participants` | call sessions | `livekit_room_name`, `call_type`, `status`, `context_type` |
| `push_tokens` | push registration | `user_id`, `expo_push_token`, `platform`, `device_name` |
| `profiles` | user identity/presence | `id`, `username`, `full_name`, `avatar_url`, `is_online`, `last_seen_at`, `hide_last_seen`, `hide_online_status`, `is_verified`, `is_ai_persona`, `is_suspended` |
| `flagged_messages` | reports | — |

### 2.5 Queries the app needs

**Conversation list** (single round trip per page, 30 rows):
```
GET /rest/v1/conversations
  ?select=id,participant_one_id,participant_two_id,last_message_at,last_message_content,last_message_sender_id,is_ai_persona_chat,ai_persona_id
  &or=(participant_one_id.eq.<uid>,participant_two_id.eq.<uid>)
  &order=last_message_at.desc
  &limit=30
```
Then batch-fetch peer `profiles` by id (`id=in.(...)`) and `conversation_settings` for `<uid>`.
Hide rows where `conversation_settings.is_deleted = true` (until a new message arrives — the trigger clears it).

**Messages page** (newest first, 30/page, keyset on `created_at`):
```
GET /rest/v1/messages?select=<explicit columns>
  &conversation_id=eq.<cid>&order=created_at.desc&limit=30
  &created_at=lt.<cursor>            // for older pages
```
Filter client-side: skip rows where `deleted_for_everyone` or `<uid> = any(deleted_for)`.

**Send** = plain `INSERT` into `messages` with `client_msg_id` (uuid v4 generated locally) — nothing else. No conversation UPDATE.

**Search** (trigram indexes exist): `messages?content=ilike.*term*&conversation_id=eq.<cid>` and global via `websearch`-style ilike on the user's conversations.

---

## 3. Realtime Relay Protocol (`wss://ws.mistlook.com`)

The relay is a pure fanout (Redis pub/sub). It never persists messages — **Postgres is the source of truth**.

### 3.1 Getting a token
```
POST /functions/v1/ws-issue-token
Authorization: Bearer <user jwt>
body: { "device_id": "<stable device uuid, <=64 chars>" }
→ 200 { "token": "<HS256 jwt, short TTL>", "expires_in": <seconds>, "ws_url": "wss://ws.mistlook.com" }
```
Connect as `wss://ws.mistlook.com/?token=<token>` (also accepted via `Authorization: Bearer` header).
Refresh the token before `expires_in` elapses and reconnect transparently.

### 3.2 Client → server frames (JSON)
```json
{ "type": "ping", "t": 1699999999 }
{ "type": "subscribe_conv",   "conv_id": "<uuid>" }
{ "type": "unsubscribe_conv", "conv_id": "<uuid>" }
{ "type": "subscribe_user",   "user_id": "<uuid>" }   // watch a peer's presence
{ "type": "unsubscribe_user", "user_id": "<uuid>" }
{ "type": "relay", "channel": "conv:<uuid>" | "user:<uuid>", "payload": { ... }, "ack_id": "<opt>" }
```
Constraints: max payload **256 KB**; only `user:` / `conv:` channels; the server enforces
membership (`conversations` participants or `group_members`) — subscribing to a foreign
conversation is rejected.

### 3.3 Payload shapes carried inside `relay`
| Payload | Shape | Server side-effect |
|---|---|---|
| Typing | `{ "type":"typing", "isTyping": true\|false }` | `typing:{cid}:{uid}` in Redis, TTL **6s** |
| Presence | `{ "type":"presence", "online": true\|false }` | `presence:{uid}` TTL **60s**; expiry flushed to `profiles.last_seen_at` every 30s |
| New message echo | `{ "type":"message", "conv_id":..., "message": {...}, "client_msg_id":... }` | fanout only |
| Read receipt | `{ "type":"read", "conv_id":..., "message_ids":[...] }` | batched flush to DB every 5s |

### 3.4 Server → client frames
Same JSON envelopes are delivered verbatim on subscribed channels, plus:
* `{ "type":"pong", "t":... }`
* `{ "type":"ack", "ack_id":... }` when the client sent `ack_id`
* Offline inbox: envelopes addressed to `user:{uid}` while offline are queued in Redis
  (max **500** per user, TTL **7 days**) and replayed on connect.

### 3.5 Client rules
* One socket per app process; heartbeat `ping` every **25s**; expect server ping every 30s.
* Exponential reconnect backoff: 1s → 2s → 5s → 10s → 30s (cap), reset on success.
* On reconnect: resubscribe the open conversation + the peers visible in the list, then
  **refetch** messages since the last known `created_at` from Postgres (relay is lossy by design).
* De-dupe by `client_msg_id` first, then `id`.

### 3.6 HTTP fallbacks (when WS is down)
```
POST /functions/v1/typing-broadcast     { conversationId, isTyping }            → { ok:true }
GET  /functions/v1/typing-broadcast?conversationId=<cid>                        → { ok:true, typing:[uids] }
POST /functions/v1/presence-heartbeat   { mode:"ping" }                          → { ok:true, ttl }
POST /functions/v1/presence-heartbeat   { mode:"check", userIds:[...] }          → { ok:true, online:{uid:bool} }
POST /functions/v1/messenger-read-batch { messageIds:[...], userId, conversationId }
```
All return `503` when Redis is unavailable — treat as "feature off", never as a crash.

---

## 4. Edge Functions the App Calls

| Function | Method / body | Returns | Use |
|---|---|---|---|
`ws-issue-token` | `{device_id}` | `{token, expires_in, ws_url}` | WS auth
`typing-broadcast` | `{conversationId,isTyping}` / GET | `{ok}` / `{typing:[]}` | typing fallback
`presence-heartbeat` | `{mode:'ping'\|'check',userIds?}` | `{ok,online?}` | presence fallback
`messenger-read-batch` | `{messageIds,userId,conversationId}` | `{ok}` | read receipts
`messenger-call` | `{action, ...params}` — actions: `start`, `join`, `end`, `decline`, `status` | `{room, token, url, call_id}` | LiveKit call signalling + permission checks
`messenger-translate` | `{text, target_lang}` | `{translated}` | inline translate (429 = rate limit, 402 = credits out)
`ai-message-assistant` / `ai-smart-replies` / `ai-message-reply` | `{conversation_id, ...}` | suggestion text | compose help & smart replies
`chat-summarize` | `{conversation_id}` | summary | "catch me up"
`push-token-upsert` | `{user_id, expo_push_token, platform:'android'\|'ios', device_name, action:'register'\|'unregister'}` | `{success, action}` | push registration
`cloudflare-r2-presigned` | `{action:'generate', fileName, folder, contentType, fileSize}` then `{action:'confirm', fileKey, fileName, fileSize, contentType, folder}` | `{presigned_url, file_key, cdn_url, headers}` / `{url, file_key}` | media upload
`cleanup-expired-messages` | cron only | — | do not call from app

**Error contract:** functions return `{ "error": "<raw message>" }` with a real HTTP status.
Surface the raw message in the UI (project standard: never mask backend errors).

---

## 5. Media Pipeline (R2 + CDN)

1. Pick/capture file → compress locally (see §6).
2. `POST /functions/v1/cloudflare-r2-presigned {action:'generate', fileName, folder:'messenger', contentType, fileSize}`.
3. `PUT` the bytes **directly** to `presigned_url` with the returned `headers` (streamed, with progress). Never proxy large files through the API host (100 MB proxy limit).
4. `POST ... {action:'confirm', fileKey, ...}` → canonical `cdn_url`.
5. Insert the message with `attachment_url = cdn_url` (+ `attachment_thumbnail_url`, `blurhash`, `attachment_duration`, `attachment_waveform`).

**Display:** always render from `https://cdn.mistlook.com/...`. Use Cloudflare image resizing for thumbnails
(`/cdn-cgi/image/width=<w>,quality=70,format=auto/<path>`); never download full-size images into list rows.

**Upload limits are DB-driven** (level-based media limits). Read the caps from
`app_settings` / level entitlements instead of hardcoding; hard ceiling 500 MB / 10 min video.

---

## 6. Local Storage, Cache & Offline

* **DB:** `isar` (or `drift`) with boxes/tables: `conversations`, `messages`, `profiles`, `outbox`, `kv`.
* **Fast KV:** `shared_preferences` for session flags; `flutter_secure_storage` for E2EE private keys.
* **Media cache:** LRU disk cache, cap ~50 MB, evict by last access.
* **Render order everywhere:** local cache → paint → network refresh → diff-merge.

### Offline outbox (mirror of the native app)
* On send, write the **full payload** to `outbox` immediately with `local_status='sending'` and a `client_msg_id`; render optimistically.
* A global drainer watches connectivity (`connectivity_plus`) + app lifecycle and flushes the outbox in order.
* Retry with exponential backoff **2s → 8s → 30s → 120s → 300s**, max 5 attempts, then `local_status='failed'` with a retry button.
* Emit `outbox:sent` / `outbox:failed` events so open chat screens update.
* Never send the same `client_msg_id` twice; treat a unique-violation as success.

---

## 7. Push Notifications

* Firebase project for `com.mistlook.messenger` (separate `google-services.json` / `GoogleService-Info.plist`).
* Register the FCM/APNs token via `push-token-upsert` after login; unregister on logout.
* Android channels must match the backend payload channel ids exactly (`messages`, `calls`, `general`) — a mismatch silently drops notifications.
* Data payload carries `conversation_id` (and `call_id` for calls) → deep link.
* Deep links: scheme `mistlookmessenger://` + universal links on `mistlook.com/m/*`.
  * `mistlookmessenger://chat/<conversation_id>`
  * `mistlookmessenger://call/<call_id>`
* Show call invites as a full-screen intent / CallKit incoming-call UI, backed by a foreground service on Android.

---

## 8. Calls (LiveKit)

1. `POST /functions/v1/messenger-call {action:'start', conversation_id, call_type:'audio'|'video'}` → `{call_id, room, token, url}`.
2. Join with `livekit_client` using the returned token + url. Never mint tokens on device.
3. `action:'join'` for the callee, `action:'end'` / `action:'decline'` to close; `action:'status'` to poll.
4. The function enforces membership, blocks, and stream config — surface `403 {error, reason}` as-is.
5. Group calls use `group_calls` / `group_call_participants`; cap from `group_calls.max_participants`.
6. Adaptive publish profiles by network (mirror native): low 360p/600k, medium 540p/1.5M, high 720p/2.5M.

---

## 9. E2EE (optional phase, parity with native)

* Key pair per device (X25519 + XChaCha20-Poly1305). Publish the **public** key to `messenger_device_keys` (`user_id`, `device_id`); keep the private key only in `flutter_secure_storage`.
* Encrypt the body, store the sealed payload in `messages.e2ee_envelope` with `e2ee_algo`; put a non-sensitive placeholder in `content` so the trigger-written conversation preview stays safe.
* Fan out one envelope entry per recipient device. Unknown device → show "waiting for key".
* Ship this behind a feature flag; plaintext chats must keep working while it rolls out.

---

## 10. Flutter Tech Stack

| Layer | Package |
|---|---|
Backend SDK | `supabase_flutter`
State | `flutter_riverpod` (or `flutter_bloc` — pick one, stay consistent)
Routing | `go_router` (deep links)
WebSocket | `web_socket_channel`
Local DB | `isar` (or `drift`)
Secure storage | `flutter_secure_storage`
Images | `cached_network_image` + `flutter_blurhash`
Media pick/capture | `image_picker`, `camera`, `file_picker`
Compression | `video_compress`, `flutter_image_compress`
Audio | `record` + `just_audio` (waveform via amplitude sampling)
Calls | `livekit_client`
Push | `firebase_messaging` + `flutter_local_notifications`
Connectivity | `connectivity_plus`
Crypto (E2EE) | `cryptography` / `libsodium`
Lists | `ScrollablePositionedList` / `CustomScrollView` with `RepaintBoundary` rows
Emoji/stickers | `emoji_picker_flutter`

---

## 11. Screens (deliverables)

1. **Splash / session restore** — restore session + hydrate cache before first frame; no logout on refresh error.
2. **Login** — email/password + Google; "New to Mistlook? Download the Mistlook app" (no signup).
3. **Chats** — folders/tabs from `chat_folders`, search, unread badges, presence dots, typing preview, swipe actions (mute/archive/delete), shimmer skeletons.
4. **Chat** — grouped bubbles, replies, reactions (long-press, animated pop-in), edit/delete-for-everyone, forward, pin, star, one-time-view media, voice notes (real waveform + 1x/1.5x/2x + tap-to-seek), disappearing timer, message effects, translate, smart replies, in-line Misty AI typing bubble for `@misty` mentions, jump-to-unread, date separators.
5. **New chat / contacts** — search `profiles`, start conversation.
6. **Group**: create, members, roles (owner/admin/member), add/remove, nickname, mute-until, group info.
7. **Call screens** — outgoing, incoming (full-screen), in-call (mute/camera/flip/speaker/participants), group grid.
8. **Media viewer** — pager, pinch-zoom, video player, save/share (respect `download_allowed`, `one_time_view`).
9. **Profile / peer sheet** — avatar, verified badge, last seen (respect `hide_last_seen`/`hide_online_status`), block/report, shared media.
10. **Settings** — notifications, privacy, wallpaper/theme, read receipts, disappearing default, blocked list, storage/cache, logout.
11. **Archived chats**, **Starred messages**, **Search results**.

**UX standards:** Material 3 with dark/light; shimmer skeletons that match final shapes; no spinners on cached screens; keyboard-avoiding composer with fixed sheet heights; safe-area insets respected on all edges; empty states with an action.

---

## 12. Security Checklist (must hold)

* Only anon key + user JWT on device. No service-role, R2, LiveKit, or WS secret.
* All reads/writes rely on RLS — never widen a policy from the client, never bypass with an RPC you invent.
* Respect `blocked_users` both directions, `profiles.is_suspended`, `hide_last_seen`, `hide_online_status`.
* Validate/limit input client-side too: content length, attachment size/type, 256 KB WS payload cap.
* Never log message content, tokens, or keys. Screenshot protection when `profiles.screenshot_locked`.
* Surface raw backend errors to the user; never swallow them.

---

## 13. Milestones

| Phase | Deliverable |
|---|---|
**M1 (week 1)** | Login + session restore, conversation list from REST + cache, chat screen read-only pagination
**M2** | Send pipeline (optimistic + outbox + drainer), WS connect/subscribe, typing, presence, read receipts
**M3** | Media: image/video/file/voice via presigned R2 + CDN thumbnails, media viewer
**M4** | Reactions, replies, edit/delete, forward, pin, star, disappearing, search, folders, archive
**M5** | Groups + roles, push notifications + deep links
**M6** | Calls (1:1 then group) via `messenger-call` + LiveKit
**M7** | AI (translate, smart replies, Misty mention), E2EE behind a flag, polish/perf pass

## 14. Acceptance Tests

1. Airplane mode → send 3 messages → back online → all 3 arrive once, in order, no duplicates.
2. Two devices, same account → both receive new messages and presence; read state converges.
3. Kill WS server → typing/presence degrade silently, messaging still works via REST.
4. 5,000-message conversation → scroll to top: no jank, memory stable, no full-size image downloads.
5. Cold start with cache → conversation list painted < 2s, no visible spinner.
6. Push tap while app killed → opens the right conversation.
7. Blocked user cannot start a call or a conversation (403 shown verbatim).
8. Token expiry mid-session → transparent refresh + WS reconnect, zero user-visible error.
