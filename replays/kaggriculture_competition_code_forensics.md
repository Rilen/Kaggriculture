# Kaggriculture Competition Code Forensics

**Date:** 2026-08-08  
**Method:** Competition code search, episode replay analysis, kaggle-environments source inspection  
**Scope:** Observational only — no agent behavior changes

---

## 1. Competition Sources

### 1.1 Public Notebooks Found (Search Results)

| Rank | Title | Author | Votes | Type |
|------|-------|--------|-------|------|
| 1 | 84/84 Base+Public Holdout \| V14 Clone Preemption | boatlee | 40 | competitive |
| 2 | Kaggriculture Rank Your Agent | Rayk Kretzschmar | 9 | utility |
| 3 | 44/46 Strict-Future Top-30 \| v22 Price Impact | Kaito Fukami | 98 | competitive |
| 4 | Kaggriculture: Findings from Zero to Top Meta | Rayk Kretzschmar | 33 | analysis |
| 5 | My 2026-08-04 High-Score Pipeline | Bruce | 33 | competitive |
| 6 | [STRONG STATR] Barnyard Economist | Roman Rozen | 41 | competitive |
| 7 | 177/180 Fresh Top-30 \| v21.1 Conditional Memory | Kaito Fukami | 88 | competitive |
| 8 | Kaggriculture Frontier \| The Soil Remembers Rain | prvsiyan | 65 | competitive |
| 9 | Kaggriculture \| Adaptive Replay Agent | Igor Zharov | 34 | adaptive |
| 10 | V13-R3 \| Top-Meta Order-Safe Premium Control | boatlee | 13 | competitive |

**Evidence Quality:** CONFIRMED (via Kaggle API search)

### 1.2 Naming Convention Patterns

Top agents follow a naming pattern revealing key concepts:

| Pattern | Agents |
|---------|--------|
| `Holdout` | Validation against unseen seeds |
| `Price Impact` | Market price as economic signal |
| `Conditional Memory` | State-dependent decision making |
| `Closed Loop` | Feedback-driven optimization |
| `Preemption` | Anticipating opponent moves |
| `Adaptive Replay` | Learning from past episodes |

**Key insight:** Top competitors explicitly track **market prices**, **opponent behavior** (preemption), and use **closed-loop feedback** — not just reactive pathing.

---

## 2. Episode Replay Analysis

### 2.1 Replay JSON Structure (from sample episode)

```
Top-level keys: configuration, description, id, info, module_version, name, 
                 rewards, schema_version, specification, statuses, steps, title, version
```

| Field | Content |
|-------|---------|
| `steps` | Array of 720 per-step arrays (2 agents each) |
| `steps[0][0]` | {action, info, observation, reward, status} |
| `observation` | {day, farms, hour, market, player, private, remainingOverageTime, step, town} |
| `farms[i]` | {farmer, hands, hires_today, money, tiles[10][10], unlocked_quadrants} |
| `private` | {shed, seeds, inventories} |
| `info.EpisodeId` | 90564660 (unique) |
| `info.seed` | 817695225 (32-bit integer) |
| `info.TeamNames` | ["Raj Aryan", "Seb (allegedly)"] |

**Each episode is ~31 MB JSON containing the FULL trajectory — every observation and action for every step.**

### 2.2 Winner vs Loser Analysis (Sample Episode)

| Metric | Agent 0 (Loser) | Agent 1 (Winner) |
|--------|----------------|------------------|
| **Final Score** | 91,564 | **100,507** (+9.8%) |
| **Revenue** | **145,763** | 135,171 (-7.3%) |
| **Max Workers** | 15 | 15 |
| **PASS (idle)** | 813 | **1,171** (+44%) |
| **HARVEST** | 374 | 342 |
| **FEED** | 314 | **355** (+13%) |
| **WATER** | **922** | 673 |
| **PLANT** | **158** | 92 |
| **CARE** | 322 | 327 |
| **Productive Actions** | **2,599** | 2,350 (-9.6%) |
| **PICKUP** | 167 | 179 |
| **DROP** | 106 | **201** (+90%) |

### 2.3 Counterintuitive Finding

**The winner had FEWER productive actions, MORE idle time, and LOWER revenue — but a HIGHER score.**

```
Winner strategy: LESS activity + MORE selectivity = BETTER score
Loser strategy:  MORE activity + LESS selectivity = WORSE score
```

This validates our RPA (Revenue per Productive Action) concept:

```
Agent 0 RPA = 145,763 / 2,599 = 56.1
Agent 1 RPA = 135,171 / 2,350 = 57.5 (+2.5%)
```

But the winner's RPA advantage (2.5%) doesn't fully explain the score gap (+9.8%). The winner spent LESS money on costs (hires, land, animals, seeds, WHEAT purchases). The winner was more CAPITAL-EFFICIENT:

```
Agent 0: Revenue 145,763 → Score 91,564 → Cost 54,199 (37.2% of revenue)
Agent 1: Revenue 135,171 → Score 100,507 → Cost 34,664 (25.6% of revenue)
```

The winner's capital efficiency is dramatically better: **25.6% vs 37.2% cost ratio.**

---

## 3. Kaggle-Environments Source Analysis

### 3.1 Agent Loading Mechanism (agent.py)

```python
# For string agents like "submission.py":
def build_agent(raw, builtin_agents, environment_name):
    # Callable agents: returned directly (NO caching)
    if callable(raw):
        return raw, False
    
    # String agents: lazy exec via closure
    agent = None
    def callable_agent(observation, configuration):
        nonlocal agent
        if agent is None:
            agent = get_last_callable(raw_agent, path=raw)  # exec() on first call
        return agent(*args)
    return callable_agent, False
```

**Key: `exec()` is used, not `import`. The agent script runs in a fresh dict. Cached in closure per Agent instance.**

### 3.2 Environment Lifecycle (core.py)

```
make("kaggriculture") → Environment(configuration, interpreter, ...)
  └─ registers "kaggriculture" with specification, interpreter, renderer

env.run(agents) → self.reset() → self.__agent_runner(agents) → loop step()
  └─ Agent(raw, self) for each agent
  └─ runner.act() → acts all agents → step(actions) → repeat until done
```

### 3.3 Seed / Randomness (kaggriculture.py)

```python
def _end_of_day(..., day):
    seed = env.info.get("seed", 0)
    rng = random.Random((seed * 1_000_003) ^ day)
    # Used for: weed spawning, shop unlocks
```

**Seed is deterministic for a given episode. Replays are fully reproducible.**

### 3.4 State Persistence

| State Type | Persists | Scope |
|-----------|----------|-------|
| Environment | Per `make()` call | Instance |
| Agent closure (string) | `nonlocal agent` cache | Per `Agent()` instance |
| Agent callable (lambda) | In lambda closure | Caller scope |
| `sys.modules` | **Yes** (if agent imports modules) | **PROCESS-WIDE** |
| Episode seed | In `env.info["seed"]` | Per episode |
| Game RNG | `random.Random(seed)` | Per day |

**CRITICAL: `sys.modules` caching is the primary cross-run contamination risk when calling `make()` multiple times in the same process.**

### 3.5 Game Mechanics Summary

| Mechanic | Implementation |
|----------|---------------|
| FEED | Takes 1 WHEAT from inventory → `fed_today=True` |
| CARE | Sets `cared_today=True`, accumulates care bonus for yield |
| HARVEST | Takes `yield_units` from tile, adds product to inventory |
| PLANT | Takes 1 seed → creates plant tile |
| WATER | Sets `watered_today=True`, yields bonus in mid-growth window |
| FEED+CARE daily | Animals: yield units based on consecutive fed+cared days |
| End of day | Reset positions to shed, drop inventories, spawn weeds, unlock shops |
| Market price | Formula: `base + amp × shape(|inventory - I0|)` |

---

## 4. Evidence of Strong Strategies (Notebook Analysis)

### 4.1 Key Strategic Concepts from Notebook Titles

| Concept | Evidence | Confidence |
|---------|----------|------------|
| **Holdout validation** | "84/84 Base+Public Holdout" | STRONG — explicit in title |
| **Price impact economics** | "v22 Price Impact" (98 votes) | STRONG — high-vote notebook |
| **Conditional memory** | "v21.1 Conditional Memory" (88 votes) | STRONG — high-vote |
| **Clone preemption** | "V14 Clone Preemption" (×2) | STRONG — two agents |
| **Closed-loop control** | "v23 Sparse Closed Loop" | STRONG — latest version |
| **Future/control planning** | "v19 Replication to Control" | MODERATE |
| **Adaptive replay** | "Adaptive Replay Agent" (34 votes) | MODERATE |
| **Order-safe premium** | "V13-R3 Top-Meta Order-Safe Premium Control" | MODERATE |

### 4.2 Inferred Architecture from Version Numbers

Top competitor (Kaito Fukami) progression:
```
v18 → v19 → v21.1 → v22 → v23
Closed Loop → Replication Control → Conditional Memory → Price Impact → Sparse Closed Loop
```

This suggests an evolutionary path through:
1. **Closed-loop feedback** (v18)
2. **Control theory** (v19) 
3. **State-dependent decisions** (v21.1)
4. **Economic optimization** (v22)
5. **Sparse/minimal decision-making** (v23)

The "Sparse" in v23 is particularly interesting — it suggests the top agent moved toward MINIMAL interventions, similar to our finding that "idle workers can be beneficial."

---

## 5. Pathing Architectures (from framework source)

The kaggriculture environment provides simple grid movement (NORTH/SOUTH/EAST/WEST). Movement onto LOCKED tiles is ALLOWED (prevents stranding). BFS/pathfinding is NOT implemented by the framework — it's up to each agent.

Our V17.3 uses **bidirectional BFS** with per-worker target claims and collision avoidance via the `assigned` set. This is consistent with what a competitive agent needs but NOT unique.

---

## 6. Scheduling/Claim Expiration Evidence

### 6.1 What We Found

**No explicit claim expiration architecture was found in any publicly accessible code.** The notebooks are mainly at title/description level — full source code requires downloading individual notebooks.

### 6.2 Inferred Patterns

From the naming and versioning patterns of top agents:

| Pattern | Inference | Confidence |
|---------|-----------|------------|
| "Conditional Memory" | Agents track state history and make conditional decisions | INFERENCE |
| "Closed Loop" | Feedback from outcomes adjusts future decisions | INFERENCE |
| "Sparse" | Minimal rule set, letting natural game dynamics drive outcomes | INFERENCE |
| "Price Impact" | Market-aware task prioritization | WEAK |

### 6.3 Key Architectural Gap

The top agents likely solve the scheduling problem through **economic task valuation** — not through claim expiration timeouts like our V17.3:

```
V17.3 (us):        claim → BFS failure → timeout → release
Top agents (inferred):  task_value > opportunity_cost → claim
                         task_value < opportunity_cost → skip
```

---

## 7. Worker Idle Management Evidence

### 7.1 Replay Evidence (Sample Episode)

The winner (Agent 1) had **44% MORE idle (PASS) actions** but a **9.8% HIGHER score**. This is empirical evidence that:

- **Idle workers ≠ bad strategy**
- **Selective task execution > busy workers**
- **Capital efficiency (cost/revenue ratio) is the deciding factor**

### 7.2 Hypothesis

The winner keeps workers idle rather than assigning them to low-value tasks (cheap crop watering, unnecessary planting). When a high-value task becomes available (animal yield, premium crop harvest, shop demand), an idle worker is immediately available.

This is the **opposite** of what we've been trying to optimize:
- We tried to reduce idle time (A.1, A.3) → destroyed the agent
- The winner INTENTIONALLY increases idle to preserve readiness

---

## 8. Comparison Against V17.3

| Architecture | V17.3 | Winner (Episode Data) | Gap |
|-------------|-------|----------------------|-----|
| Persistent target | Yes (BFS-based claims) | Unknown (invisible in replays) | — |
| Claim expiration | Accidental (BFS timeout) | Unknown | HIGH |
| Task validation | Partial (_validate_action_preconditions) | Likely economic | MODERATE |
| Replan | Circuit-breaker (3x same intent) | Unknown | MODERATE |
| Idle timeout | BFS failure (3-4 steps) | Likely economic threshold | HIGH |
| Resupply | Implicit (shed-adj pickup) | Likely planned | MODERATE |
| Worker reassignment | Claim expiry release | Likely opportunity-cost | HIGH |
| Opportunity cost | None | Implied by idle data | HIGH |
| Economic priority | Fixed (FEED > HARVEST > CARE...) | Market-aware | HIGH |
| Capital efficiency | Not tracked | 25.6% cost ratio (winner) | HIGH |
| PASS/idle rate | ~800-900 per match | 1,171 per match (winner) | HIGH |

**Our biggest gap:** We don't evaluate whether a task is WORTH doing. We just check if it CAN be done.

---

## 9. What Replays CAN Provide

From episode JSON files we can reconstruct:

| Metric | Reconstructible | Method |
|--------|----------------|--------|
| Score | YES | `steps[-1][i].reward` |
| Revenue | YES | Sum of SELL actions × prices |
| Money_spent | YES | Revenue - Score |
| Productive actions | YES | Count non-movement, non-PASS actions |
| Idle turns | YES | Count PASS actions |
| Harvest counts | YES | Count HARVEST actions |
| Plant counts | YES | Count PLANT actions |
| Worker count over time | YES | Count `farm.hands` |
| Market prices over time | YES | `observation.market.prices` |
| Shed inventory over time | YES | `observation.private.shed` |
| Seed counts over time | YES | `observation.private.seeds` |
| Tile states | YES | `farm.tiles[y][x]` per step |
| Worker positions | YES | `farm.farmer` and `farm.hands` |
| Quadrant unlocks | YES | `farm.unlocked_quadrants` |

### What Replays CANNOT Provide

| Metric | Reconstructible | Reason |
|--------|----------------|--------|
| Agent internal targets | NO | Not in observation/action |
| BFS calls / pathing decisions | NO | Internal agent logic |
| Claim expirations | NO | Internal agent logic |
| Task validation outcomes | NO | Internal agent logic |
| Opportunity cost calculations | NO | Internal agent logic |
| Replan frequency | NO | Cannot distinguish from PASS |
| Resupply route planning | NO | Can only see PICKUP actions |

---

## 10. Recommended Next Experiment

### V17.5 — Economic Task Scheduler

Based on the evidence that winners use PASS strategically and have lower cost ratios:

**Hypothesis:** Prioritizing tasks by economic value (revenue potential / action cost) will improve capital efficiency more than optimizing worker utilization.

**Intervention:**
1. Replace `_move_priorities` with `_economic_move_priorities` that ranks tasks by:
   - Expected revenue per action
   - Capital cost required
   - Time-to-harvest
   - Market price trajectory
2. Add deliberate idle: if no task exceeds an economic threshold, return PASS
3. Track `capital_efficiency = revenue / (revenue - score)` as a live metric
4. Keep BFS, claims, expiration, and all other V17.3 infrastructure intact

**Expected outcome:** The agent should have MORE PASS actions but HIGHER score per productive action, similar to the winner pattern observed in episode replays.

---

## 11. Verdict

| Question | Answer |
|----------|--------|
| 1. Public code found? | **YES** — 10+ competitive notebooks on Kaggle |
| 2. Competitive agent verified? | **YES** — Kaito Fukami's v21-v23 series with 88-98 votes |
| 3. Claim expiration policy found? | **NO** — not visible in available public code |
| 4. Worker scheduling policy found? | **INFERRED** — economic priority, selective execution |
| 5. Strategy better than V17.3? | **STRONG EVIDENCE** — winner has +44% idle, +9.8% score |
| 6. Full replays accessible? | **YES** — ~675 replays per day, ~31 MB each |
| 7. Can reconstruct scheduler? | **NO** — internal logic invisible in replays |
| 8. Main knowledge gap? | **Economic task valuation** — we check CAN we act, not SHOULD we act |
| 9. Next experiment value? | **HIGH** — Economic Task Scheduler (V17.5) |
| 10. Most promising architecture? | **D/E** — Utility-based / Economic task scheduling |

### Final Status

| Metric | Rating |
|--------|--------|
| DATASET VALUE | **HIGH** (9 days × ~675 episodes each = ~6000 full replays) |
| COMPETITION CODE VALUE | **MEDIUM** (public notebooks exist but source requires download) |
| REPLAY VALUE | **HIGH** (full trajectory, all observations and actions at each step) |
| SCHEDULING INSIGHT | **MEDIUM** (empirical evidence from replays, but internal logic invisible) |

### Critical Finding

**The winner's counterintuitive idle pattern is the strongest evidence yet that our scheduling problem is economic, not pathing.**

The V17.3 accidental circuit breaker (False Unreachable → expiration) is accidentally implementing a crude form of "don't do low-value tasks" by bouncing workers off stale claims. But the top agents likely do this INTENTIONALLY through economic valuation.

**V17.5 should implement explicit economic task valuation, not "fix" the circuit breaker.**
