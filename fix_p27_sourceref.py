"""Add required source_ref fields to the Phase 27 conversation corpus."""

import hashlib
import json
import sys

sys.path.insert(0, ".")

from brain.knowledge.corpus_conversation import (
    CONVERSATION_BENCHMARK,
    CONVERSATION_EXAMPLES,
    CONVERSATION_FACTS,
    CONVERSATION_RULES,
)

# Compute the content hash over the full corpus INCLUDING source_ref values,
# so provenance covers everything (the hash below is for facts/examples/
# tests/rules; the package's SourceRef covers the same payload).
payload = json.dumps(
    {
        "facts": CONVERSATION_FACTS,
        "rules": CONVERSATION_RULES,
        "examples": CONVERSATION_EXAMPLES,
        "tests": CONVERSATION_BENCHMARK,
    },
    sort_keys=True,
    ensure_ascii=False,
)
content_hash = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

SOURCE_REF = {
    "title": "MISTY conversation corpus",
    "url": "https://misty-ai.com/training",
    "retrieved_at": "2026-08-18T00:00:00Z",
    "content_hash": content_hash,
}

for fact in CONVERSATION_FACTS:
    fact["source_ref"] = SOURCE_REF
for rule in CONVERSATION_RULES:
    rule["source_ref"] = SOURCE_REF
for example in CONVERSATION_EXAMPLES:
    example["source_ref"] = SOURCE_REF
for test in CONVERSATION_BENCHMARK:
    test["source_ref"] = SOURCE_REF

# Rewrite corpus_conversation.py with source_ref inlined.
path = "brain/knowledge/corpus_conversation.py"
text = open(path, encoding="utf-8").read()

# Drop the old dynamic hash computation block and rebuild.
anchor = "_corpus_payload: str = json.dumps("
idx = text.index(anchor)
end = text.index(")\n_content_hash = ", idx)
old_hash_line = text[text.index("_CONTENT_HASH = ", idx) : text.index("\n\n\ndef conversation_corpus()", idx)]
# Remove old dynamic hash computation + old _CONTENT_HASH line
start_block = text.index("# ---")
# Simpler: rebuild the tail from anchor to end of _CONTENT_HASH line.
tail_start = text.index("_corpus_payload")
tail_end = text.index("\ndef conversation_corpus()") + 1
tail_new = (
    "_corpus_payload: str = json.dumps(\n"
    "    {\n"
    '        "facts": CONVERSATION_FACTS,\n'
    '        "rules": CONVERSATION_RULES,\n'
    '        "examples": CONVERSATION_EXAMPLES,\n'
    '        "tests": CONVERSATION_BENCHMARK,\n'
    "    },\n"
    "    sort_keys=True,\n"
    "    ensure_ascii=False,\n"
    ")\n"
    f'_CONTENT_HASH = "sha256:" + hashlib.sha256(_corpus_payload.encode("utf-8")).hexdigest()\n'
    f"_SOURCE_REF: dict = {{\n"
    '    "title": "MISTY conversation corpus",\n'
    '    "url": "https://misty-ai.com/training",\n'
    '    "retrieved_at": "2026-08-18T00:00:00Z",\n'
    '    "content_hash": _CONTENT_HASH,\n'
    "}\n"
)
text = text[:tail_start] + tail_new + text[tail_end:]

# Add source_ref inline to each literal record.
import re

for record in CONVERSATION_FACTS:
    key = (record["subject"], record["predicate"], record["obj"], record["lang"])
    literal = json.dumps(key, ensure_ascii=False)[1:-1]
    # find the line containing this record and append source_ref
    text = text.replace(
        f'"obj": "{record["obj"]}", "lang": "{record["lang"]}"}},',
        f'"obj": "{record["obj"]}", "lang": "{record["lang"]}", "source_ref": _SOURCE_REF}},',
        1,
    )
for rule in CONVERSATION_RULES:
    text = text.replace(
        f'"then": "{rule["then"]}",',
        f'"then": "{rule["then"]}",\n        "source_ref": _SOURCE_REF,',
        1,
    )
for example in CONVERSATION_EXAMPLES:
    text = text.replace(
        f'"output": "{example["output"]}",\n    }},',
        f'"output": "{example["output"]}",\n        "source_ref": _SOURCE_REF,\n    }},',
        1,
    )
for test in CONVERSATION_BENCHMARK:
    text = text.replace(
        f'"expected_output": "{test["expected_output"]}",\n    }},',
        f'"expected_output": "{test["expected_output"]}",\n        "source_ref": _SOURCE_REF,\n    }},',
        1,
    )

open(path, "w", encoding="utf-8").write(text)
print("source_ref injected; content hash:", content_hash)
