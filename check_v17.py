import submission as sub

print("[OK] Import")
ag = sub.KaggricultureAgentV17()
print("[OK] Instantiation:", ag.__class__.__name__)

import inspect
src = inspect.getsource(submission)

checks = [
    ("MELON 9 opening",    "'MELON', 9"),
    ("STRAWBERRY 3 open",  "'STRAWBERRY', 3"),
    ("STRAWBERRY decide",  "STRAWBERRY_MIN_DAYS_LEFT"),
    ("Dynamic wheat price","buy_n * wheat_price"),
    ("PICKUP gate",        "empty_past > 0"),
    ("BFS intact",         "_bfs"),
    ("TARGET_COW=8",       "TARGET_COW      = 8"),
]
all_ok = True
for name, pattern in checks:
    found = pattern in src
    status = "OK" if found else "FAIL"
    if not found:
        all_ok = False
    print(f"  [{status}] {name}")

if all_ok:
    print()
    print("All 7 checks passed.")
else:
    print()
    print("Some checks FAILED.")
