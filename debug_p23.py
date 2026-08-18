"""Phase 23 debug: inspect parse results and salient entities per turn."""
from brain.core.brain import Brain

b = Brain()
turns = ["আকাশের রঙ কি?", "কারণ কী?", "আর বলো"]
for i, q in enumerate(turns):
    res = b.nlu.parse(q)
    salient = b.dialogue_context.get_salient_entities()
    print(f"--- turn {i}: {q}")
    print("    intent:", res.intent)
    print("    query:", res.query)
    print("    salient BEFORE:", salient)
    full = b.process(q)
    print("    response:", full["response"][:100])
    print("    salient AFTER:", b.dialogue_context.get_salient_entities())
