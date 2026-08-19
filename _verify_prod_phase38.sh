#!/bin/bash
BASE=https://misty-brain.onrender.com
echo "--- Q1: তুমি কি করছো? ---"
curl -s -X POST $BASE/api/chat -H "Content-Type: application/json" -d '{"message":"তুমি কি করছো?"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print('A:',d.get('response','')[:200])"
echo "--- Q2: কি খবর? ---"
curl -s -X POST $BASE/api/chat -H "Content-Type: application/json" -d '{"message":"কি খবর?"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print('A:',d.get('response','')[:200])"
echo "--- Q3: N2L ---"
curl -s -X POST $BASE/api/chat -H "Content-Type: application/json" -d '{"message":"নিউটনের দ্বিতীয় সূত্র কি?"}' | python3 -c "import sys,json;d=json.load(sys.stdin);print('A:',d.get('response','')[:200])"
echo "--- state ---"
curl -s $BASE/api/brain/state | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('active_concepts:', len(d.get('active_concepts',{})))
print('memory_recall:', d.get('memory_recall'))
print('last_confidence:', d.get('last_confidence'))
print('last_uncertainty:', d.get('last_uncertainty'))
print('keys:', sorted(d.keys()))
"
