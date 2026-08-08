# A.4 CARE Timing Filter — Deployment Log

## Submission Details

| Field | Value |
|-------|-------|
| **Kaggle Ref** | #55357436 |
| **Timestamp** | 2026-08-08T18:00Z approx |
| **Competition** | kaggriculture |
| **File submitted** | submission.py (copied from submission_v17_3_a4.py) |
| **Description** | V17.3 + A4 CARE timing filter: CARE only on animals with interval < 3 days (COW/GOOSE, not SHEEP). 20-seed benchmark: +3467 mean score, 55% WR vs V17.3. |

## Baseline

| Item | Status |
|------|--------|
| submission_v17_3.py | INTACT — unchanged |
| submission_v17_3_a4.py | INTACT — unchanged |
| submission_kaggle_v15_backup.py | CREATED — backup of previous submission |
| Previous submission.py | Backed up as submission_kaggle_v15_backup.py |

## Diff

One-line change in `_move_priorities`, condition #3 (CARE):
```diff
- and (x, y) not in self.cared_this_day),
+ and (x, y) not in self.cared_this_day
+ and {"COW": 2, "SHEEP": 3, "GOOSE": 1}.get(t.get("animal", ""), 99) < 3),
```

## Validation

| Check | Result |
|-------|--------|
| Compile | PASS |
| Import | PASS |
| Entry points | agent_fn, main_agent, agent — all present |
| Diff audit | Exactly 1 condition added |
| Submission accepted | YES (ref #55357436) |

## Local Benchmark (20 seeds)

| Metric | V17.3 | A.4 | Delta | 95% CI | Cohen d |
|--------|-------|-----|-------|--------|---------|
| Score | 24,986 | 28,452 | +3,467 | [-4,449, +11,382] | +0.28 |
| Revenue | 64,676 | 67,769 | +3,093 | [-6,015, +12,201] | — |
| Prod Acts | 1,755 | 1,851 | +96 | [-56, +248] | — |
| RPA | 36.8 | 36.6 | -0.2 | — | — |
| Win Rate | — | — | 11/20 (55%) | — | — |
| Median | 23,211 | 27,974 | +4,763 | — | — |

## Deploy Strategy

| Slot | Candidate | Status |
|------|-----------|--------|
| DEPLOY 1 | V17.3-A.4 (CARE filter) | **SUBMITTED** #55357436 |
| DEPLOY 2 | Best observed (V15 / V17.3 / A.4) | PENDING |
| DEPLOY 3 | Micro-variant from leaderboard data | PENDING |
| DEPLOY 4 | Best final candidate | PENDING |

## Next Step

Await Kaggle leaderboard result for #55357436 before deploying slot #2.
