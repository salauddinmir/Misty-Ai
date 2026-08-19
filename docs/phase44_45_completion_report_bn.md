# ফেজ ৪৪-৪৫ সম্পন্ন রিপোর্ট — Fact Aging ও Consolidation Sweep

**প্রজেক্ট:** MISTY — ভারতের প্রথম LLM-নিরপেক্ষ Smart AI Brain
**নির্মাতা:** Pixline Incorporate, Founder — Salauddin Mir (Netvai)
**রিপো:** `salauddinmir/Misty-Ai` (main)
**তারিখ:** ২০ আগস্ট, ২০২৬

---

## ১. এই রিপোর্টে যা যুক্ত হলো

মানুষের মস্তিষ্কের স্মৃতি একদিনে কেবল তৈরি হয় না, আর একবার তৈরি হওয়ার পর চিরকাল স্থিরও থাকে না — বরং কালের সাথে সাথে ক্ষয় হয় (decay), ঘুমে শক্তি পায় (rehearsal/consolidation), আর দুর্বল বা পরাজিত স্মৃতি মুছে যায় (forgetting)। ফেজ ৪৪-৪৫-এ MISTY-কে ঠিক এই জৈবিক ক্ষমতাগুলো দেওয়া হলো, যা আগের ফেজগুলো (ফ্যাক্ট ভেরিফিকেশন, সেলফ-কারেকশন, পার্সোনাল রিকল) কে "জীবন্ত মস্তিষ্ক"-এর দিকে আরেক ধাপ এগিয়ে নিয়ে গেল।

| ফেজ | বিষয় | স্ট্যাটাস |
|---|---|---|
| ফেজ ৪৪ | Fact Aging — কালানুসারী কনফিডেন্স ক্ষয় | ✅ সম্পন্ন (commit `b6c9236`) |
| ফেজ ৪৫ | Consolidation Sweep — rehearsal, পরিষ্কার ও merger | ✅ সম্পন্ন (commit `9b9ee16`) |

---

## ২. ফেজ ৪৪ — Fact Aging (ফ্যাক্ট-এজিং / কনফিডেন্স-ডিকে)

### ২.১ কেন দরকার ছিল

ইন্টারনেট থেকে শেখা তথ্য চিরস্থায়ী নয় — ২০২৬ সালের খবর ২০২৮ সালে ভুল হতে পারে। আগে MISTY-র ওয়েব-শেখা তথ্য কোনো ক্ষয় ছাড়াই চিরদিন থেকে যাচ্ছিল। এখন প্রতিটি ওয়েব-শেখা ফ্যাক্টের সাথে **সময়-স্ট্যাম্প** (created_at / accessed_at) যুক্ত হয়েছে, এবং কালের সাথে তার আত্মবিশ্বাস ধীরে ধীরে কমতে থাকে।

### ২.২ যা কাজ করছে

- **SemanticFact-এ সময়-স্ট্যাম্প:** `created_at` ও `accessed_at` ফিল্ড যোগ; প্রতিটি স্টোর/আপডেটে অটো-সেট হয় (`brain/memory/semantic.py`)।
- **অর্ধ-আয়ু সূত্র (Half-life decay):** ওয়েব-শেখা ফ্যাক্টের কনফিডেন্স **৯০ দিনে অর্ধেক** হয়ে যায়। সূত্র: `new = old × 2^(-days/90)`। ৯০ দিন পর ০.৯ কনফিডেন্স → ০.৪৫, ১৮০ দিন পর → ০.২২৫।
- **Prune Threshold (০.৩৫):** কনফিডেন্স ০.৩৫-এর নিচে নেমে গেলে ফ্যাক্ট মস্তিষ্ক থেকে মুছে যায়।
- **Junk Floor (০.২০):** জন্মলগ্নেই ০.২০-এর নিচে কনফিডেন্স থাকা ফ্যাক্ট তাৎক্ষণিকভাবে বর্জন হয় — আবর্জনা কোনো দিন বাঁচে না।
- **সুরক্ষিত উৎস (Protected Sources):** `user_input`, `curriculum`, `training`, `commonsense_layer` ও সকল করিকুলাম-ফেজের (math, physics, literature, culture, conversation_corpus) উৎস **কখনোই ক্ষয় বা প্রুন হয় না**। মিস্টির পরিচয় ও শেখানো জ্ঞান স্থায়ী।
- **Audit Log:** প্রতিটি সিদ্ধান্ত (decayed / refreshed / pruned / protected) লগে লিখে রাখা হয় (সর্বোচ্চ ১০০ এন্ট্রি) — কিছুই নীরবে মুছে যায় না।
- **Reflexion Tick-এ সুইপ:** প্রতিটি autonoumous reflection tick-এ একবার স্বয়ংক্রিয় ভাবে aging sweep চালে (`brain/learning/fact_aging.py` → `Brain.fact_ager`)।

### ২.৩ API-তে যোগ হলো

`GET /api/brain/state` রেসপন্সে নতুন ফিল্ড `fact_aging` — এতে আছে total_decisions, action-অনুযায়ী গণনা, শেষ ৫টি সিদ্ধান্তের বিবরণ, এবং কনফিগ (half_life_days=90, prune_threshold=0.35, junk_threshold=0.20)।

### ২.৪ টেস্ট

১৯টি নতুন টেস্ট (`tests/test_phase44_fact_aging.py`) — decay সূত্র, protected sources-এর স্থায়িত্ব, prun, junk floor, accessed_at রিফ্রেশ, লগ বাউন্ড, Brain-ওয়ায়ারিং ও API-ফিল্ড — সব পাস।

---

## ৩. ফেজ ৪৫ — Consolidation Sweep (কনসোলিডেশন সুইপ)

### ৩.১ ধারণা — "ঘুমের মস্তিষ্ক"

মানুষের মস্তিষ্ক ঘুমানোর সময় দিনের স্মৃতিগুলো পুনরায় খেলে (rehearsal), কে স্মরণ করে নেয়, আবার দুর্বল সাথিতে স্বপ্নের প্রমাণ থাকে না। ফেজ ৪৫-এ MISTY-র প্রতিটি reflection tick-এ একটি নিয়ন্ত্রিত consolidation sweep চালে, যার তিনটি স্তর:

| স্তর | কী হয় | কীভাবে |
|---|---|---|
| **CLEAN** | ফেজ ৪২-এর ফ্যাক্ট-ভেরিফায়ার-এ পরাজিত (quarantined) ফ্যাক্ট মুছে ফেলা | `quarantine_removed`, লগসহ |
| **MERGE** | একই subject+predicate-এর ডুপ্লিকেট ওয়েব-ফ্যাক্টগুলোর মধ্যে শুধু সবচেয়ে শক্তিশালীটি রাখা | প্রতি সুইপ সর্বোচ্চ ১৬টি merger |
| **REHEARSE** | ০.৩৫–০.৮৫ কনফিডেন্সের মধ্যমানের ফ্যাক্টগুলোকে নিদ্রা-অভ্যাস — এর subject/object concept-গুলো **Spreading Activation** দিয়ে পুনঃসক্রিয় করা ও working memory-তে anchor রাখা | প্রতি সুইপ সর্বোচ্চ ২৪টি rehearsal |

### ৩.২ মূল নিয়ম

- **বাজেট:** প্রতি সুইপে কাম ১৬ merger ও ২৪ rehearsal — এক রাতে মস্তিষ্ক উলটপালট হয়ে যায় না।
- **সুরক্ষা:** ফেজ ৪৪-এর মতো এখানেও সকল করিকুলাম ও identity উৎস সুরক্ষিত — merger বা removal কখনো স্পর্শ করে না।
- **Audit:** প্রতিটি সিদ্ধান্ত (rehearsed / merged_winner / merged_loser / quarantine_removed / protected) লগে (সর্বোচ্চ ১০০)।
- **`/api/brain/state`-এ** নতুন `consolidation` ফিল্ড — counts, recent decisions ও কনফিগ।

`brain/learning/consolidation_sweep.py` → `Brain.consolidation_engine` → reflection tick-এ অটো-চালু।

### ৩.৩ টেস্ট

১৪টি নতুন টেস্ট (`tests/test_phase45_consolidation.py`) — rehearsal দ্বারা concept-activation বৃদ্ধি, ডুপ্লিকেট merger (শক্তিশালী বিচার জিতে), সুইপ-বাজেট, quarantine পরিষ্কার, protected sources ও API-ফিল্ড — সব পাস।

---

## ৪. গুণমানের প্রমাণ (Quality Gates)

| চেক | ফলাফল |
|---|---|
| Regression টেস্ট | **৯৭৯ পাস** (ফেজ ৪৩-এর ৯৪৬ + ১৯ ফেজ ৪৪ + ১৪ ফেজ ৪৫) |
| Conversation Benchmark | **৫৭/৫৭ = ১০০%** |
| Ruff lint + format | ✅ পাস |
| CI (3.10/3.11/3.12 + lint) | ✅ সবকিছু সবুজ (commit `9b9ee16`) |
| Production (Render) | main-এ পুশ করায় স্বয়ংক্রিয় ডিপ্লয় হচ্ছে — https://misty-brain.onrender.com |

---

## ৫. পূর্ববর্তী ফেজগুলোর সাথে সংযোগ

| ফেজ | সংযোগ |
|---|---|
| ৩৯ (Learning Roadmap) | রোডম্যাপ থেকে শেখা ওয়েব-ফ্যাক্টগুলো এখন aging-এর মধ্য দিয়ে যায় |
| ৪২ (Fact Verification) | পরাজিত ফ্যাক্ট quarantine থেকে consolidation sweep-এ মুছে যায় |
| ৪৩ (Personal Recall) | identity/curriculum ফ্যাক্ট protected — personalization-এর ভিত্তি অক্ষুণ্ণ |
| ৪৪+৪৫ | aging-এর পর consolidation — মিলিয়ে MISTY এখন "ভুলে যাওয়ার ও শক্তি বাড়ানোর" ক্ষমতা রাখে, যেটি একটি সত্যিকারের ডিজিটাল মস্তিষ্কের স্বরূপ |

---

## ৬. পোরবর্তী পদক্ষেপ

মস্তিষ্ক এখন শেখে (ওয়েব লার্নিং), যাচাই করে (ভেরিফিকেশন), ভুল ধরে (সেলফ-কারেকশন), বয়স হয়ে ক্ষয় হয় (aging), ঘুমে শক্তি পায় (consolidation)। পরবর্তী দিকে ONA (Ontological Neural Architecture) রিজোয়নিং লেয়ার, ফ্যাক্ট-মের্জের পর পুনঃযাচাই, এবং দীর্ঘমেয়াদী স্মৃতির persistent storage-এ ফ্যাক্ট-স্ট্যাম্প সংরক্ষণ (PostgreSQL migration) নেওয়া যেতে পারে।
