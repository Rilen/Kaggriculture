"""
Gate 0.5: Determinism & Benchmark Validity Audit.
Tests: intra-process, inter-process, order, seed 48 canary.
"""
import json, os, sys, subprocess, statistics, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kaggle_environments import make
from submission_v17_3_a4 import KaggricultureAgentV17 as A4
from submission_v17_3 import KaggricultureAgentV17 as V3

SEEDS = [42, 46, 48, 50, 52, 55]
def m(xs): return statistics.mean(xs) if xs else 0

def get_rev(steps, ai):
    r = 0.0
    for s in steps:
        a = s[ai].get("action", {})
        o = s[ai].get("observation", {})
        p = o.get("market", {}).get("prices", {}) if o else {}
        if isinstance(a, dict):
            for mk in a.get("market", []):
                if mk and mk[0] == "SELL" and len(mk) >= 3:
                    r += mk[2] * p.get(mk[1], 0)
    return r

results = {}

# ====== TEST 1: Intra-process reproducibility ======
print("=" * 60)
print("TEST 1: Intra-process reproducibility (same seed, same process, 2 runs)")
print("=" * 60)
intra = []
for seed in SEEDS:
    run_results = []
    for run_id in [1, 2]:
        env = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
        ag = A4()
        steps = env.run([lambda o: ag(o), "submission.py"])
        score_a4 = steps[-1][0].get("reward", 0)
        score_op = steps[-1][1].get("reward", 0)
        rev_a4 = get_rev(steps, 0)
        n_steps = len(steps)
        run_results.append({"run": run_id, "a4": score_a4, "op": score_op, "rev": rev_a4, "n_steps": n_steps})
    
    r1, r2 = run_results
    match = r1["a4"] == r2["a4"] and r1["op"] == r2["op"]
    print(f"  S{seed}: R1={r1['a4']:.0f} R2={r2['a4']:.0f} MATCH={match}")
    intra.append({"seed": seed, "match": match, "r1": r1, "r2": r2})
results["intra"] = intra

# ====== TEST 2: Order test ======
print(f"\n{'='*60}")
print("TEST 2: Execution order test (A4 vs Op vs Op vs A4)")
print("=" * 60)
order = []
for seed in [48, 50, 52]:
    # Order A: A4 as agent 0, submission.py as agent 1
    env_a = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    ag_a = A4()
    s_a = env_a.run([lambda o: ag_a(o), "submission.py"])
    a4_a = s_a[-1][0].get("reward", 0)
    op_a = s_a[-1][1].get("reward", 0)
    n_a = len(s_a)
    
    # Order B: submission.py as agent 0, A4 as agent 1
    env_b = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    ag_b = A4()
    s_b = env_b.run(["submission.py", lambda o: ag_b(o)])
    a4_b = s_b[-1][1].get("reward", 0)
    op_b = s_b[-1][0].get("reward", 0)
    n_b = len(s_b)
    
    match = a4_a == a4_b and op_a == op_b
    print(f"  S{seed}: A4_pos0={a4_a:.0f}/{op_a:.0f} A4_pos1={a4_b:.0f}/{op_b:.0f} step_0={n_a} step_1={n_b} MATCH={match}")
    order.append({"seed": seed, "a4_0": a4_a, "a4_1": a4_b, "op_0": op_a, "op_1": op_b, "match": match})
results["order"] = order

# ====== TEST 3: Head-to-head vs isolated ======
print(f"\n{'='*60}")
print("TEST 3: Head-to-head vs isolated comparison")
print("=" * 60)
h2h_v_iso = []
for seed in [48, 50]:
    # Head-to-head
    env_h = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    a_v3 = V3(); a_a4 = A4()
    s_h = env_h.run([lambda o: a_v3(o), lambda o: a_a4(o)])
    v3_h = s_h[-1][0].get("reward", 0)
    a4_h = s_h[-1][1].get("reward", 0)
    
    # Isolated: V3 vs submission.py
    env_v = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    av = V3()
    s_v = env_v.run([lambda o: av(o), "submission.py"])
    v3_i = s_v[-1][0].get("reward", 0)
    
    # Isolated: A4 vs submission.py
    env_a4 = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": seed})
    aa = A4()
    s_a4 = env_a4.run([lambda o: aa(o), "submission.py"])
    a4_i = s_a4[-1][0].get("reward", 0)
    
    print(f"  S{seed}: H2H A4={a4_h:.0f} V3={v3_h:.0f} | ISO A4={a4_i:.0f} V3={v3_i:.0f}")
    h2h_v_iso.append({"seed": seed, "h2h_a4": a4_h, "h2h_v3": v3_h, "iso_a4": a4_i, "iso_v3": v3_i})
results["h2h_vs_iso"] = h2h_v_iso

# ====== TEST 4: Subprocess reproducibility ======
print(f"\n{'='*60}")
print("TEST 4: Subprocess reproducibility (same seed, fresh subprocess)")
print("=" * 60)
MATCH_SCRIPT = "run_single_match.py"
subp = []
for seed in [48, 50, 52]:
    run_results = []
    for run_id in [1, 2]:
        cmd = ["python", MATCH_SCRIPT, "submission_v17_3_a4.py", str(seed)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        for line in reversed(res.stdout.splitlines()):
            line = line.strip()
            if line.startswith('{'):
                data = json.loads(line)
                run_results.append(data)
                break
    
    r1, r2 = run_results[0], run_results[1]
    match = r1["score"] == r2["score"]
    print(f"  S{seed}: R1={r1['score']:.0f} R2={r2['score']:.0f} MATCH={match}")
    subp.append({"seed": seed, "match": match, "r1": r1, "r2": r2})
results["subprocess"] = subp

# ====== TEST 5: RNG and global state audit ======
print(f"\n{'='*60}")
print("TEST 5: RNG and global state audit")
print("=" * 60)

# Check if submission.py uses random at module level
import importlib, random

# Snapshot sys.modules before first match
pre_modules = set(sys.modules.keys())

# Run a match
env = make("kaggriculture", configuration={"episodeSteps": 100, "randomSeed": 48})
ag = A4(); steps = env.run([lambda o: ag(o), "submission.py"])

# Check new modules loaded
post_modules = set(sys.modules.keys())
new_mods = post_modules - pre_modules
kagl_mods = [m for m in new_mods if "kaggl" in m.lower() or "submission" in m.lower() or "kaggri" in m.lower()]
print(f"  New sys.modules after match: {kagl_mods}")

# Check RNG state before/after
rng_before = random.getstate()
env2 = make("kaggriculture", configuration={"episodeSteps": 100, "randomSeed": 48})
ag2 = A4(); steps2 = env2.run([lambda o: ag2(o), "submission.py"])
rng_after = random.getstate()
print(f"  RNG state changed by match: {rng_before != rng_after}")

# Check agent internal RNG state
print(f"  A4 telemetry intact after match: {ag.telemetry.get('target_claims', -1) >= 0}")
results["rng"] = {"rng_changed": rng_before != rng_after, "new_mods": kagl_mods}

# ====== TEST 6: Seed 48 canary — action-level comparison ======
print(f"\n{'='*60}")
print("TEST 6: Seed 48 canary — action-level hash comparison")
print("=" * 60)

def action_hash(steps, ai):
    """Create hash of action sequence for comparison."""
    actions = []
    for step in steps:
        a = step[ai].get("action", {})
        if isinstance(a, dict):
            f = a.get("farmer", ["PASS"])
            actions.append(f[0] if f else "PASS")
    return hashlib.md5("-".join(actions[-500:]).encode()).hexdigest()[:8]

env_a = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": 48})
ag_a = A4(); s_a = env_a.run([lambda o: ag_a(o), "submission.py"])
h_a = action_hash(s_a, 0); sc_a = s_a[-1][0].get("reward", 0)

env_b = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": 48})
ag_b = A4(); s_b = env_b.run([lambda o: ag_b(o), "submission.py"])
h_b = action_hash(s_b, 0); sc_b = s_b[-1][0].get("reward", 0)

print(f"  Run A: score={sc_a:.0f} hash={h_a}")
print(f"  Run B: score={sc_b:.0f} hash={h_b}")
print(f"  Match: {h_a == h_b}")

# Also test V17.3 on seed 48
env_v1 = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": 48})
av1 = V3(); sv1 = env_v1.run([lambda o: av1(o), "submission.py"])
hv1 = action_hash(sv1, 0); scv1 = sv1[-1][0].get("reward", 0)

env_v2 = make("kaggriculture", configuration={"episodeSteps": 3000, "randomSeed": 48})
av2 = V3(); sv2 = env_v2.run([lambda o: av2(o), "submission.py"])
hv2 = action_hash(sv2, 0); scv2 = sv2[-1][0].get("reward", 0)

print(f"\n  V17.3 Run A: score={scv1:.0f} hash={hv1}")
print(f"  V17.3 Run B: score={scv2:.0f} hash={hv2}")
print(f"  V17.3 Match: {hv1 == hv2}")
results["seed48_canary"] = {"a4_match": h_a == h_b, "v3_match": hv1 == hv2, "a4_hash": h_a, "v3_hash": hv1}

# ====== Save ======
with open("replays/gate05_determinism_dataset.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nSaved to replays/gate05_determinism_dataset.json")

# Final summary
intra_match = all(i["match"] for i in intra)
order_match = all(o["match"] for o in order)
subp_match = all(s["match"] for s in subp)
print(f"\n=== SUMMARY ===")
print(f"  Intra-process match: {intra_match}")
print(f"  Order-independence: {order_match}")
print(f"  Subprocess match: {subp_match}")
print(f"  A4 Seed 48 canary: {results['seed48_canary']['a4_match']}")
print(f"  V3 Seed 48 canary: {results['seed48_canary']['v3_match']}")
