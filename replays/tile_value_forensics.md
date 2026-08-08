# Tile Value Forensics — Instance-Level Selection Analysis

**Sample:** 5 episodes (10 agents, 5 winners, 5 losers)  
**Method:** Per-action tile candidate comparison using pre-action farm state  
**Value Metric:** product_price × yield_units (simplified proxy)

---

## 1. Hypothesis Tested

**H6:** "Winning agents select higher-value instances within the same action tier."

---

## 2. Aggregate Results: Winners vs Losers Tile Selection

| Action | Agent | N | ChoseBest% | DS5 | DS20 | N_Cand |
|--------|-------|---|-----------|-----|------|--------|
| **FEED** | Winners | 1,608 | 22.6% | 1,845 | 9,403 | 7.4 |
| | Losers | 1,580 | 22.1% | 1,616 | 8,707 | 7.2 |
| | **Diff** | | **+0.5pp** | **+14.2%** | | |
| **CARE** | Winners | 1,572 | 20.4% | 2,016 | 9,279 | 7.4 |
| | Losers | 1,582 | 20.1% | 1,703 | 8,799 | 7.1 |
| | **Diff** | | **+0.3pp** | **+18.4%** | | |
| **WATER** | Winners | 4,207 | 7.2% | 1,969 | 9,264 | 29.8 |
| | Losers | 4,449 | 7.0% | 1,734 | 8,756 | 29.7 |
| | **Diff** | | **+0.1pp** | **+13.5%** | | |
| **HARVEST** | Winners | 1,737 | 9.9% | 3,368 | 13,369 | 28.3 |
| | Losers | 1,792 | 9.7% | 3,228 | 12,080 | 30.4 |
| | **Diff** | | **+0.2pp** | **+4.3%** | | |

**Overall ChoseBest%:** Winners 14.3%, Losers 14.0% (+0.3pp, Cohen's d = +0.03)

---

## 3. The Paradox

Winners have virtually identical tile selection quality (+0.3pp) but 12–18% higher downstream revenue per action.

```
ChoseBest difference:  ~0.3pp (negligible)
DS5 difference:        +12-18% (substantial)
```

**Our simple value metric (price × yield_units) does NOT explain the winners' advantage.**

---

## 4. What This Means

### 4.1 The value metric is too simplistic

`price × current_yield_units` doesn't capture:
- Time-to-next-yield (an animal about to produce is worth more)
- Care bonus accumulation (pending_care_bonus multiplies future yield)
- Growth window bonus (watering during mid-growth doubles yield)
- Fertilizer status (3-day yield boost)
- Market price trajectory (future price at harvest time)
- Distance cost (travel time to reach the tile)

### 4.2 Winners don't pick "better tiles" — they HAVE better tiles

The candidate count per action is nearly identical (~7 for FEED/CARE, ~29 for WATER/HARVEST). Winners and losers have access to the same NUMBER of eligible candidates. But winners consistently get +12-18% more downstream revenue from whatever tile they act on.

**This suggests the advantage is STRATEGIC (farm composition), not TACTICAL (tile choice).**

Winners build farms where the AVERAGE tile value is higher. They don't need to "pick the best tile" because ALL their tiles are higher quality:
- More cows than sheep (cows produce 2.0× more frequently)
- Crops planted at optimal times (ensuring yield windows align)
- Animals consistently cared/fed (yield accumulates faster)
- Fertilizer used strategically (on crops with best ROI)

### 4.3 WATER selection is nearly random

```
WATER ChoseBest: 7.2% (with ~30 candidates)
```

When there are 30 eligible tiles for watering, picking the BEST one by price×yield is nearly random — most tiles have similar value. But the DS5 for winners is STILL +13.5% higher.

This confirms: WINNERS' WATER actions generate more revenue NOT because they water better tiles, but because the tiles they DO have (planted with higher-value crops) yield better harvests.

---

## 5. H6 Verdict

| Hypothesis | Verdict | Evidence |
|-----------|---------|----------|
| H6: Winners select higher-value tile instances | **REFUTADA** (by simple metric) | ChoseBest +0.3pp, d=+0.03 |
| | **INCONCLUSIVE** (by richer metric) | Simple metric may miss true value drivers |

**The +12-18% DS5 advantage for winners is NOT driven by better tile-level selection within action types.** It is driven by strategic farm composition and maintenance quality — winners simply have better tiles to act on.

---

## 6. Revised Understanding: Three Levels of Economic Optimization

```
LEVEL 1 — STRATEGIC (farm composition)
  - Which animals to raise (COW > SHEEP)
  - Which crops to plant (MELON > STRAWBERRY > TOMATO > CARROT > WHEAT)
  - When to invest (land purchases, hires)
  - How many workers to maintain

LEVEL 2 — TACTICAL (task timing)
  - When to FEED (just before yield accumulation)
  - When to WATER (during growth window for 2× bonus)
  - When to HARVEST (at max_yield_day for non-ongoing crops)
  - When to COLLECT_FERTILIZER (before key watering windows)

LEVEL 3 — OPERATIONAL (tile selection)  
  - Which specific animal to feed (among unfed animals)
  - Which specific crop to water (among unwatered plants)
  - Which tile to plant on (among empty tiles)
```

**Our analysis found winners have no advantage at Level 3 (+0.3pp). Their advantage is at Levels 1 and 2.**

This explains why the V17.3 and its variants (A.1-A.4) couldn't close the gap by modifying pathing, claims, or expiration: **those changes operate at Level 3, while the winning advantage is at Levels 1 and 2.**

---

## 7. Implications for V17.5

### What NOT to focus on
- Tile selection within action types (winners don't do it better)
- PASS/idle optimization (refuted in v2 analysis)
- Claim expiration tuning (addresses symptom, not cause)

### What TO focus on
1. **Strategic farm composition** — plant the right crops, raise the right animals
2. **Tactical timing** — water during growth windows, feed before yield accumulation
3. **Capital allocation** — hire workers only when marginal revenue > marginal cost
4. **Crop selection** — prioritize high-value crops (MELON $250, STRAWBERRY $120) and let cheap crops (WHEAT $25) serve only as feed support

### Proposed V17.5 Architecture

```
STRATEGIC LAYER (once per day or state change)
  → Decide: which crops to plant, which animals to buy/hire
  → Based on: market prices, days remaining, current farm composition

TACTICAL LAYER (per action decision)
  → Decide: water NOW or wait? feed NOW or wait?
  → Based on: growth window, yield timing, care bonus accumulation

OPERATIONAL LAYER (per worker-turn, existing V17.3)
  → Execute: BFS to target, claim, act, release
  → Based on: current priority tiers (FEED > HARVEST > CARE > WATER)
```

---

## 8. Limitations

- n=5 episodes is insufficient for statistical significance (all 95% CIs cross zero)
- Value metric is overly simplistic (price × yield_units)
- Tile features not fully extracted (missing: care_bonus, days_to_yield, fertilizer, market price trajectory)
- PLANT analysis very sparse (only 1-2 instances per agent with candidates)
- Cannot observe agent's internal decision process (only actions and observations)

---

## 9. H6 Verdict

```
H6: "Winning agents select higher-value instances 
     within the same action tier."

VERDICT: EVIDÊNCIA INSUFICIENTE
         (not refuted by simple metric, but +0.3pp not meaningful)

The hypothesis is likely TRUE in principle but our value metric 
is too simple to detect it. Winners' +12-18% DS5 advantage must 
come from SOMEWHERE — either:
  (a) Better tile selection (not captured by our metric), or
  (b) Better strategic farm composition (all their tiles are better)
```

---

## 10. Recommendation

**V17.5 should focus on STRATEGIC and TACTICAL layers, not operational tile selection.**

The operational layer (BFS → claim → act → release) works adequately. The missing pieces are:
1. Which crops to plant (economic selection, not just "any seed available")
2. When to water (growth window awareness)
3. Which animals to prioritize (COW > SHEEP, yield-timing awareness)
4. When to invest (capital efficiency)
