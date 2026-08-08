# A.4 Implementation Audit

## CARE Predicate Location
File: submission_v17_3.py, lines 659-661
```python
lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                 and t.get("animal") and not t.get("cared_today")
                 and (x, y) not in self.cared_this_day),
```

## Animal Intervals (from kaggriculture.py)
| Animal | interval (days) | interval (steps) | < 57 steps? | < 3 days? |
|--------|----------------|------------------|-------------|-----------|
| COW | 2 | 48 | YES | YES |
| SHEEP | 3 | 72 | NO | Edge |
| GOOSE | 1 | 24 | YES | YES |

## Forensics Threshold
TTY < 57 steps (2.375 days) — DS5 differs by 43%. COW always within threshold. SHEEP sometimes exceeds.

## Planned Diff
ONE additional condition appended to CARE lambda:
```python
and {"COW": 2, "SHEEP": 3, "GOOSE": 1}.get(t.get("animal", ""), 99) < 3
```

This blocks CARE on SHEEP (interval=3 is not < 3). CARE on COW and GOOSE remains unchanged.

## Impact
- COW CARE: unchanged (always allowed)
- SHEEP CARE: BLOCKED (interval 3 days > 2.4 day threshold)
- GOOSE CARE: unchanged (always allowed, interval 1 day)
- FEED, WATER, HARVEST: unchanged
- BFS, claims, expiration: unchanged
- SHEEP will still get FEED (separate priority) and produce reduced yield

## Rationale
Forensics Gate 7: COW pre_yield=0 shows W/L DS5 gap +16.3%. SHEEP pre_yield=0 shows W/L gap +1.7% (negligible). CARE on sheep is not the differentiator; CARE on cows is. The filter removes the low-differentiator, preserving the high-differentiator.
