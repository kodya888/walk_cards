"""Minimize Lottie JSON: round floats to 2 decimals, compact dump."""
import json, re, sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'C:\Users\ADMIN\Documents\ai_moi\walk_cards\img\flowers\_lottie_tmp\flower\animations\02d27d65-79dd-4578-be75-412438235c45.json'
DST = r'C:\Users\ADMIN\Documents\ai_moi\walk_cards\img\flowers\04_flowerbloom.json'

def round_floats(obj):
    if isinstance(obj, float):
        r = round(obj, 2)
        return int(r) if abs(r - round(r)) < 1e-9 else r  # 3.0 -> 3
    if isinstance(obj, list):
        return [round_floats(x) for x in obj]
    if isinstance(obj, dict):
        return {k: round_floats(v) for k, v in obj.items()}
    return obj

raw = open(SRC, encoding='utf-8').read()
d = json.loads(raw)
d = round_floats(d)
out = json.dumps(d, separators=(',', ':'), ensure_ascii=False)
open(DST, 'w', encoding='utf-8').write(out)
print('raw bytes:', len(raw), ' rounded:', len(out), ' ratio: %.2f' % (len(out) / len(raw)))
