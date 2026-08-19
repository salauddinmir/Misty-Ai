"""Temporary diagnostic: why active_concepts stays empty for user messages."""
from brain.core.brain import Brain
from brain.nlu.parser import NLUParser

messages = [
    'ভুলভাল বকছো কেনো?',
    'কি খবর?',
    'কর্মখেত্র ভাই',
    'মিস্টি কেমন আছো?',
    '2+2=?',
    'তুমি কি করছো?',
    'আমার নাম সালাউদ্দিন',
]

parser = NLUParser()
for msg in messages:
    b = Brain()
    pr = parser.parse(msg)
    entities = pr.entities if pr else None
    result = b.process(msg)
    print(f'MSG {msg!r}')
    print(f'  intent={pr.intent if pr else None} entities={entities}')
    print(f'  active={len(b.state.active_concepts)} {list(b.state.active_concepts)[:6]}')
    resp = result.get('response', '')
    print(f'  resp={resp[:90]!r}')
    print()
