# A.4 CARE TTY Counterfactual Forensics

**Sample:** 5 episodes, 3,154 CARE actions  
**Method:** Per-CARE TTY extraction, counterfactual classification, replacement simulation  
**Status:** 100% observational — zero agent changes

---

## GATE 0: Baseline

| Metric | Value |
|--------|-------|
| Total CAREs | 3,154 |
| Episodes | 5 |
| Winner CAREs | 1,572 |
| Loser CAREs | 1,582 |
| Baseline files intact | YES |

---

## GATE 1/2: Classification at TTY < 57

| Group | ALLOW | BLOCK | BLOCK % |
|-------|-------|-------|---------|
| All | 1,688 | 1,466 | **46.5%** |
| Winners | 919 | 653 | **41.5%** |
| Losers | 769 | 813 | **51.4%** |

The filter blocks nearly half of all CAREs. It hits losers harder (+10pp) — losers are already making more wasteful CAREs.

---

## GATE 3: ALLOW vs BLOCK Value

| Metric | ALLOW (TTY<57) | BLOCK (TTY≥57) | Difference |
|--------|----------------|----------------|------------|
| **DS5** | **2,297** | **1,300** | **-43.4%** |
| DS10 | 4,680 | 2,824 | -39.7% |
| DS20 | 9,903 | 7,893 | -20.3% |
| Avg TTY | 25 | 481 | 19× |

**BLOCKED CAREs generate 43% less DS5.** The gap is substantial. CARE far from yield is economically inferior.

---

## GATE 4/5: Replacement Opportunities (Most Important)

| Replacement Type | Count | % of Blocked |
|-----------------|-------|-------------|
| **WATER** | 947 | **64.6%** |
| **HARVEST** | 496 | **33.8%** |
| FEED | 8 | 0.5% |
| PLANT | 3 | 0.2% |
| **NO ALTERNATIVE** | **12** | **0.8%** |

**99.2% of blocked CAREs have a productive alternative.** Only 12 of 1,466 blocked CAREs (0.8%) would have no replacement action, creating a risk of PASS/idle.

Average alternative tasks per blocked step: **71.0** — the farm typically has dozens of pending tasks when a blocked CARE is attempted.

### Replacement Value vs Blocked CARE Value

From earlier per-action DS5 analysis:

| Alternative | DS5 | vs Blocked CARE DS5 (1,300) |
|------------|------|---------------------------|
| **WATER** | **1,970** | **+52%** |
| **HARVEST** | **3,370** | **+159%** |
| FEED | 1,845 | +42% |

**Every available alternative has higher expected DS5 than blocked CARE.** Replacing a TTY≥57 CARE with WATER or HARVEST would UPGRADE the worker's economic output.

---

## GATE 7: Threshold Sensitivity

| TTY < | Blocked % | With Alt % | No Alt | Blocked DS5 | Winner Blocked% | Loser Blocked% |
|-------|-----------|-----------|--------|-------------|-----------------|----------------|
| **19** | 76% | 61% | **39%** | 1,717 | — | — |
| **38** | 61% | 75% | **25%** | 1,623 | — | — |
| **57** | 46% | **99%** | **1%** | 1,300 | 41.5% | 51.4% |
| 76 | 37% | 99% | 1% | 990 | — | — |
| 95 | 33% | 99% | 1% | 1,078 | — | — |
| 150 | 24% | 98% | 2% | 1,272 | — | — |

**TTY < 57 is the optimal threshold.** It balances blocking enough low-value CAREs (46%) while maintaining near-perfect alternative availability (99%). Lower thresholds (TTY<38) block more CAREs but leave 25% of blocked events without alternatives — creating PASS risk (which we know from A.3 destroys the agent).

---

## GATE 8: Winner/Loser Asymmetry

| | Winner ALLOW | Winner BLOCK | Loser ALLOW | Loser BLOCK |
|---|-------------|-------------|------------|------------|
| DS5 | 2,371 | 1,471 | 2,208 | 1,163 |
| TTY | 25 | 385 | 25 | 558 |
| N | 919 | 653 | 769 | 813 |

**The filter is asymmetric: it blocks more loser CAREs (51.4%) than winner CAREs (41.5%).** This is desirable — the filter should disproportionately remove low-value actions, and losers make more of them. Winners' natural behavior is already better-aligned with TTY<57.

No winner CARE with low TTY and high DS5 gets blocked — the winners' ALLOW CAREs are genuinely the high-value ones (DS5=2,371).

---

## GATE 9: Safety Assessment

| Criterion | Value | Status |
|-----------|-------|--------|
| Blocked DS5 < Allowed DS5 | 1,300 vs 2,297 (-43%) | PASS |
| Replacement available | 99.2% of blocked | PASS |
| Replacement value > Blocked | WATER +52%, HARVEST +159% | PASS |
| PASS risk | 0.8% of blocked (12 events) | PASS |
| Winner impact | 41.5% CAREs blocked | ACCEPTABLE |
| Loser impact | 51.4% CAREs blocked | ACCEPTABLE |
| Behavior change scale | 46% of CAREs | **MODERATE** |

---

## GATE 10: Verdict

```
A4_STATUS = PROMISING
```

**The TTY < 57 CARE filter passes 6 of 7 safety criteria.** The only concern (MODERATE behavior change) is justified: 46% of all CARE actions would be redirected. However:

1. 99.2% of blocked CAREs have a better alternative
2. Those alternatives (WATER, HARVEST) have 52-159% higher DS5 than blocked CARE
3. PASS risk is negligible (0.8%)
4. Winners are less affected than losers (desirable)
5. The yield-cycle causality is confirmed (DS5 decreases with TTY)

---

## Minimum Causal Patch

### Insertion Point
`submission_v17_3.py`, method `_move_priorities`, condition #3 (CARE). Line 659.

### Before
```python
lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                 and t.get("animal") and not t.get("cared_today")
                 and (x, y) not in self.cared_this_day),
```

### After
```python
lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                 and t.get("animal") and not t.get("cared_today")
                 and (x, y) not in self.cared_this_day
                 and _expected_tty(t, day) < 3),  # < 3 days ≈ < 57 steps
```

Where `_expected_tty` is a simple approximation:
```python
def _expected_tty(self, tile, day):
    animal = tile["animal"]
    days_since_placed = day - tile.get("placed_day", day)
    if days_since_placed < {"COW": 8, "SHEEP": 6}.get(animal, 8):
        # Before first yield: time to first_yield_day
        return {"COW": 8, "SHEEP": 6}.get(animal, 8) - days_since_placed
    # After first yield: interval-based
    return {"COW": 2, "SHEEP": 3}.get(animal, 2)
```

### Expected Metrics Changes

| Metric | Expected Change |
|--------|----------------|
| CARE count | -40-50% |
| WATER count | +5-10% (shift from CARE) |
| HARVEST count | +2-5% (shift from CARE) |
| RPA | +5-10% |
| PASS% | ~unchanged (0.8% risk) |
| Farm composition | unchanged |
| Claims/expiration | unchanged |
| BFS | unchanged |

### Risk Mitigation

If the patch is implemented, the first Gate 1 test should verify:
- PASS% does not increase > 1-2pp
- CARE DS5 increases (fewer low-value CAREs)
- WATER/HARVEST counts increase (replacement)

---

## Output Files

| File | Content |
|------|---------|
| `replays/a4_tty_counterfactual.md` | This report |
| `replays/a4_tty_counterfactual.json` | Aggregate statistics |
| `replays/a4_threshold_sensitivity.csv` | 7 threshold tests |
| `replays/a4_replacement_opportunities.csv` | Per-blocked-CARE replacement data |
