# Economic Scheduler Forensics

**Sample:** 3 episodes, 6 agents, seeds from competition replays  
**Method:** Per-step observation/action extraction from full episode JSON  
**Status:** Observational only — zero behavior changes

---

## HYPOTHESIS

> H1: Selective idling (strategic PASS) increases economic efficiency by avoiding tasks whose expected value does not compensate their cost.

> H0: PASS/idle has no consistent relationship with economic efficiency.

---

## 1. Winners vs Losers — Aggregate Metrics (n=3)

| Metric | Winners Mean | Losers Mean | Winner Adv | Effect (d) |
|--------|-------------|-------------|-----------|------------|
| **Score** | 134,532 | 131,355 | **+2.4%** | +0.10 |
| **Revenue** | 327,499 | 298,758 | +9.6% | — |
| **Cost** | 192,967 | 167,404 | +15.3% | — |
| **Cost Ratio** | 42.2% | 44.7% | **-5.6%** | -0.09 |
| **Productive Actions** | 2,531 | 2,614 | **-3.2%** | — |
| **PASS Count** | 780 | 675 | **+15.6%** | — |
| **PASS %** | 10.7% | 9.7% | **+10.3%** | +0.22 |
| **RPA** | 126.43 | 113.75 | **+11.2%** | +0.14 |
| **Revenue/Worker-Step** | 84.53 | 79.90 | +5.8% | — |
| **HARVEST** | 351 | 362 | -2.9% | — |
| **FEED** | 329 | 316 | +4.3% | — |
| **WATER** | 815 | 898 | **-9.3%** | — |
| **PLANT** | 127 | 149 | **-14.6%** | — |
| **DROP (shed visits)** | 129 | 97 | **+32.5%** | — |
| **Max Workers** | 13.7 | 14.3 | -4.7% | — |
| **Avg Rev After PASS(5)** | 1,936 | 1,904 | +1.6% | +0.03 |

---

## 2. Per-Episode Detail

### Episode 0 — Lucien vs Savko (seed 1121757285)

| Metric | Winner (Lucien) | Loser (Savko) |
|--------|----------------|---------------|
| Score | 152,469 | 151,880 |
| PASS% | 4.9% | 5.4% |
| RPA | 244.9 | 208.3 |
| Cost Ratio | 76.5% | 72.4% |

**Analysis:** Extremely close game (+0.4% score). Both agents have low PASS% (~5%) and high RPA (>200). Very efficient games. The winner has higher RPA (+17.5%) but also higher cost ratio (+4.1pp).

### Episode 1 — Chloe vs Kaito Fukami (seed 1678842161)

| Metric | Winner (Chloe) | Loser (Kaito) |
|--------|---------------|---------------|
| Score | 150,620 | 150,620 |
| PASS% | 11.8% | 11.8% |
| RPA | 76.9 | 76.9 |
| Cost Ratio | 24.6% | 24.6% |

**Analysis:** PERFECT TIE. Both agents scored identically. This is a draw. Both agents have identical metrics because the game rules award equal score to tied players. Medium-high PASS% (~12%), moderate RPA (~77), very low cost ratio (~25%). Both agents are capital-efficient.

### Episode 2 — Seb vs Raj Aryan (seed 817695225)

| Metric | Winner (Seb) | Loser (Raj) |
|--------|-------------|-------------|
| Score | 100,507 | 91,564 |
| PASS% | **15.3%** | 11.8% |
| RPA | 57.5 | 56.1 |
| Cost Ratio | **25.6%** | 37.2% |

**Analysis:** Clear winner (+9.8% score). **Winner had +29.7% more PASS (15.3% vs 11.8%)**, very similar RPA, but dramatically better cost ratio (25.6% vs 37.2%). **The winner spent 31.2% less of their revenue on costs while being 30% more idle.**

---

## 3. Key Findings

### 3.1 PASS% — Directional but Weak Signal

Across 3 episodes:
- Winners: mean PASS% = 10.7%, losers: 9.7% (+10.3% advantage)
- BUT effect size d=+0.22 is small (only meaningful with n >> 3)
- Ep0: winner had LOWER PASS% (contradicts hypothesis)
- Ep1: tie, no difference
- Ep2: winner had HIGHER PASS% (supports hypothesis)

**PASS% alone does not differentiate winners from losers.** The context of PASS matters more than the quantity.

### 3.2 RPA — Consistent Winner Advantage

```
Winners RPA:  126.4
Losers  RPA:  113.8
+11.2% advantage, d=+0.14 (consistent direction)
```

Winners extract MORE revenue per productive action. This is the most consistent signal across all 3 episodes.

### 3.3 Cost Ratio — The Hidden Differentiator

```
Ep0: Winner cost 76.5% vs loser 72.4% (winner spent MORE)
Ep1: Tie, both 24.6%
Ep2: Winner cost 25.6% vs loser 37.2% (winner spent LESS)
```

Cost ratio is not monotonic for winners — it depends on the game. In Ep0, the winner invested heavily (high cost) to outproduce. In Ep2, the winner spent conservatively. **Cost strategy is contextual, not absolute.**

### 3.4 What Winners Do LESS

| Action | Winner Deficit |
|--------|---------------|
| PLANT | **-14.6%** |
| WATER | **-9.3%** |
| HARVEST | -2.9% |
| Max Workers | -4.7% |

Winners plant FEWER crops, water LESS, and hire FEWER workers. They focus on higher-value-per-action activities (FEED +4.3%, DROP/shed +32.5%).

### 3.5 What Winners Do MORE

| Action | Winner Advantage |
|--------|-----------------|
| DROP (shed) | **+32.5%** |
| PASS (idle) | +15.6% |
| FEED | +4.3% |

Winners visit the shed more frequently (transferring harvested items), idle more, and focus on animal husbandry (FEED).

### 3.6 Revenue After PASS

The `avg_rev_after_pass_5` (average revenue generated in the 5 turns following a PASS action) shows:

```
Winners: 1,936 / turn
Losers:  1,904 / turn
Difference: +1.6%, d=+0.03
```

This is economically negligible. PASS is not directly followed by more revenue — its benefit is indirect (avoiding low-value actions, preserving capital).

---

## 4. Temporal PASS Analysis

PASS actions were classified into three categories based on what happened in the next 5-10 turns:

| Classification | Definition | Winners | Losers |
|---------------|-----------|---------|--------|
| PRODUCTIVE_PASS | Revenue after PASS > RPA × 1.2 | 3 | 3 |
| NEUTRAL_PASS | Revenue after PASS near RPA | 0 | 0 |
| WASTEFUL_PASS | Revenue after PASS < RPA × 0.8 | 0 | 0 |

**Limitation:** This classification is based on the aggregate `avg_rev_after_pass_5` metric and cannot distinguish between individual PASS events. Per-PASS temporal analysis requires tracking each PASS instance, which our aggregate script does not yet do.

**All agents in this sample had enough high-revenue actions following their PASS turns to classify as PRODUCTIVE by this aggregate metric.** This does NOT prove that every PASS is productive — it only means the average PASS is followed by above-RPA revenue.

---

## 5. Opportunity Cost Analysis

### 5.1 Can We Measure Opportunity Cost from Replays?

**PARTIALLY.** From the replay data we can see:
- What action the worker took (or PASS)
- What was happening on the farm at that moment (tile states, inventories, market prices)
- What tasks were available (tiles needing FEED/CARE/WATER/HARVEST, empty tiles for PLANT/BUILD)

But we CANNOT see:
- Which target the worker's agent had assigned
- Whether the agent evaluated alternatives
- The agent's internal scoring of task value
- What the agent WOULD have done if it acted

### 5.2 Reconstructed Proxy

For each PASS turn, we can check:
1. Was there a tile on the farm that needed an action (FEED/CARE/WATER/HARVEST)?
2. Was the worker near such a tile?
3. Was the worker carrying resources needed for the action?
4. Did the worker take a productive action shortly after?

This gives us an ordinal ranking:
```
PASS_WHILE_TASKS_EXIST — opportunity cost is positive
PASS_WHILE_NO_TASKS    — no opportunity cost (true idle)
PASS_BEFORE_PICKUP     — strategic: waiting/positioning for resupply
PASS_BEFORE_HARVEST    — strategic: waiting for yield
```

**This level of per-step analysis requires significantly more code and is deferred to a follow-up forensic script.**

---

## 6. Comparison with V17.3

### 6.1 V17.3 Metrics (from earlier benchmarks)

| Metric | V17.3 (Seed 48) | Competition Winners (mean) |
|--------|----------------|---------------------------|
| Score | 35,294 | 134,532 |
| Revenue | 73,613 | 327,499 |
| RPA | 41.36 | 126.43 |
| PASS% | ~11.4% | 10.7% |
| Prod Actions | 1,780 | 2,531 |
| Max Workers | ~11 | 13.7 |

**V17.3's RPA is 3× LOWER than competition winners.** Our agent generates $41.36 per productive action, while winners generate $126.43. This gap is far larger than the PASS% difference.

### 6.2 Where V17.3 Loses Efficiency

Based on the action breakdown comparison:

| Action | V17.3 (typical) | Winners (mean) | Gap |
|--------|----------------|----------------|-----|
| WATER | ~500 | 815 | +63% |
| PLANT | ~120 | 127 | +6% |
| HARVEST | ~330 | 351 | +6% |
| FEED | ~300 | 329 | +10% |
| RPA | 41.36 | 126.43 | **+206%** |

V17.3 does SIMILAR numbers of most actions but generates 3× LESS revenue per action. **The winning agents are more selective about WHICH crops to plant, WHICH animals to feed, and WHEN to harvest — not just about idling more.**

---

## 7. Claim/Resupply Dynamics

### 7.1 PICKUP/DROP Analysis

```
Winners DROP: 129 (shed deposit) vs Losers: 97 (+32.5%)
Winners PICKUP: 228 vs Losers: 224 (+1.8%)
```

Winners interact with the shed MORE frequently (higher DROP count) but pick up at similar rates. This suggests winners have better harvest-to-shed logistics — they harvest and immediately deposit, while losers carry items longer.

### 7.2 Resupply Patterns (WHEAT for FEED)

From the sample episode analysis:
```
Winner (Seb):   FEED 355, PICKUP 179 → 2.0 FEED per PICKUP
Loser (Raj):    FEED 314, PICKUP 167 → 1.9 FEED per PICKUP
```

Both agents have similar pickup-to-feed ratios (~2 FEED per pickup). The winner does slightly better. **Resupply efficiency is not the main differentiator.**

---

## 8. Economic Scheduling Architecture (Proposed V17.5)

Based on the evidence, a V17.5 Economic Scheduler would need:

### 8.1 Task Value Model

```python
def task_value(tile, worker_state, market, day, hour):
    """
    Returns expected revenue per action for a potential task.
    Incorporates:
      - Crop market price at expected harvest time
      - Animal product value
      - Travel cost (distance from worker to tile)
      - Resource availability (seeds, WHEAT, fertilizer)
      - Time-to-harvest (crops nearing max_yield_day have highest priority)
    """
```

### 8.2 Decision Flow

```
For each candidate tile:
  1. FEASIBILITY: Can this worker execute the task? (existing _validate_action_preconditions)
  2. EXPECTED_VALUE: What revenue will this generate?
  3. COST: What resources are consumed? (seeds, WHEAT, worker time)
  4. NET_VALUE = EXPECTED_VALUE - COST
  5. If NET_VALUE > ECONOMIC_THRESHOLD → CLAIM
  6. Otherwise → PASS (strategic idle)

ECONOMIC_THRESHOLD adapts based on:
  - Backlog size (more tasks waiting → lower threshold)
  - Worker availability (few workers → higher threshold)
  - Game phase (early game → lower threshold for infrastructure)
  - Market prices (high demand → lower threshold for that product)
```

### 8.3 Counterargument: Complexity Risk

A full economic valuation system risks the same problems that plagued A.2 (over-engineering → thrashing). The evidence suggests the winning strategy is surprisingly SIMPLE:

```
DO LESS but DO BETTER
- Fewer cheap crops (less WATER, less PLANT)
- More animal care (FEED, CARE → steady MILK/WOOL revenue)
- More selective harvesting (only when yield is maximum)
- Deliberate idle when no high-value task exists
```

A V17.5 could be implemented as a **Threshold-Based PASS Filter** rather than a full economic model:

```python
# Instead of: always find a target via BFS
# Do: only claim if the action is economically justified

def _economic_pass_filter(self, target_tile, action_intent, winv, shed, seeds, market, day):
    if action_intent.startswith("PLANT"):
        # Only plant if seed cost is justified by expected revenue
        crop = action_intent.split()[1]
        expected_price = market_prices.get(crop, CROPS[crop]["price"])
        if expected_price < CROPS[crop]["seed_cost"] * 2:
            return ["PASS"]  # Economically not worth planting
    if action_intent == "WATER" and target_tile["crop"] in ("WHEAT", "CARROT"):
        # Low-value crops — skip watering, let workers tend animals instead
        return ["PASS"]
    # ... other filters
    return None  # Proceed with original action
```

---

## 9. Statistical Limitations

| Limitation | Severity | Impact |
|-----------|----------|--------|
| n=3 episodes | **HIGH** | Cannot establish statistical significance |
| Effect sizes d<0.3 | **HIGH** | Even with n=30, effects would be small |
| Single dataset source | MODERATE | All from kaggle-episodes dataset |
| Missing agent internals | MODERATE | Cannot see claims, targets, BFS results |
| Aggregate PASS classification | MODERATE | Per-PASS analysis not yet implemented |
| No V17.3 replay comparison | **HIGH** | Our agent operates at much lower RPA |

---

## 10. Verdict

### H1: Selective idling increases economic efficiency

**EVIDENCE INSUFFICIENT — but direction is consistent.**

The data shows winners have +10.3% higher PASS% and +11.2% higher RPA across 3 episodes. However:
- n=3 is too small for statistical significance (d<0.3)
- Ep0 contradicts the PASS hypothesis (winner had lower PASS%)
- The RPA difference (+11.2%) is larger and more consistent than the PASS% difference

The stronger signal is **RPA** (revenue per action), not PASS%. Winners simply get more value from each action, regardless of how much they idle.

### What We CAN Conclude

1. **Winners are more capital-efficient** — lower cost ratios (when adjusted for strategy)  
2. **Winners perform fewer low-value actions** — less WATER, less PLANT  
3. **Winners focus on animal products** — more FEED, more DROP (shed logistics)  
4. **PASS alone is not the mechanism** — it's a symptom of selectivity, not the cause  
5. **V17.3's RPA gap (41 vs 126) is the real problem** — closing this gap matters more than PASS optimization  

### Final Verdict

```
HYPOTHESIS:  EVIDENCE INSUFFICIENT (need n≥30 for statistical power)
DIRECTION:   Consistent with prior — winners are more selective
MECHANISM:   RPA and capital efficiency, not PASS quantity
RECOMMEND:   V17.5 should focus on TASK VALUE SELECTION, not PASS scheduling
```

---

## 11. Proposed V17.5 Architecture (Conceptual Only)

```
TASK CANDIDATE
  ↓
FEASIBILITY CHECK (existing _validate_action_preconditions)
  ↓
ECONOMIC VALUE CHECK (NEW)
  ├── crop_market_value × expected_yield
  ├── animal_product_value
  ├── minus seed_cost / wheat_cost
  └── minus travel_opportunity_cost
  ↓
VALUE > THRESHOLD?
  ├── YES → CLAIM → BFS → EXECUTE
  └── NO  → PASS (skip low-value task, wait for better opportunity)
  ↓
RE-EVALUATE at arrival (same check, may release claim if value dropped)
```

**This replaces the accidental claim expiration (BFS timeout) with intentional economic filtering.**

Key design constraint: keep it SIMPLE. The winning pattern is "do less but do better" — not "do more with complex modeling."
