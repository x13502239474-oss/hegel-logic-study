# -*- coding: utf-8 -*-
"""读取《小逻辑》原文分节文本（贺麟译本），用于核对引文。

用法：
    python tools/sec.py 86          # 打印 §86
    python tools/sec.py 86 89       # 打印 §86–§89
    python tools/sec.py 86 --brief  # 只打印每节前 200 字
"""
import json, os, sys, re

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", ".work", "_epub", "sections.json")
DATA = json.load(open(os.path.abspath(BASE), encoding="utf-8"))

args = [a for a in sys.argv[1:] if not a.startswith("--")]
brief = "--brief" in sys.argv

if not args:
    print("用法: python tools/sec.py 86 [89] [--brief]")
    sys.exit(0)

if len(args) == 1:
    lo = hi = int(args[0])
else:
    lo, hi = int(args[0]), int(args[1])

for n in range(lo, hi + 1):
    key = str(n)
    if key not in DATA:
        print(f"\n[§{n} 未找到]")
        continue
    text = DATA[key].strip()
    text = re.sub(r"\n{2,}", "\n", text)
    if brief:
        text = text[:200]
    print("\n" + "=" * 60)
    print(text)
