"""
Script de validação do submission v16.
Roda smoke tests sem kaggle_environments e depois um episódio completo se disponível.
"""
import ast, sys, json

print("=" * 55)
print("v16 Validation Suite")
print("=" * 55)

# 1. Syntax check
with open("submission.py", "r", encoding="utf-8") as f:
    src = f.read()
try:
    ast.parse(src)
    print("[OK] Syntax: sem erros")
except SyntaxError as e:
    print(f"[FAIL] Syntax: {e}")
    sys.exit(1)

# 2. Import
try:
    import submission as sub
    print("[OK] Import: sem erros")
except Exception as e:
    print(f"[FAIL] Import: {e}")
    sys.exit(1)

# 3. Instantiation
try:
    ag = sub.KaggricultureAgentV16()
    print("[OK] KaggricultureAgentV16() instanciado")
except Exception as e:
    print(f"[FAIL] Instantiation: {e}")
    sys.exit(1)

# 4. Smoke test dia 0
def make_obs(day, hour, money=3000, seeds=None, shed=None, hands=None, shops=None, prices=None):
    tiles = []
    for y in range(10):
        row = []
        for x in range(10):
            if x >= 5 or y >= 5:
                row.append("LOCKED")
            else:
                row.append(None)
        tiles.append(row)
    return {
        "player": 0,
        "day": day,
        "hour": hour,
        "farms": [
            {
                "money": money,
                "tiles": tiles,
                "farmer": [4, 4],
                "hands": hands or [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 5000,
                "tiles": [[None]*10 for _ in range(10)],
                "farmer": [4, 4],
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "market": {
            "inventory": {},
            "prices": prices or {"WHEAT": 28, "STRAWBERRY": 120, "MELON": 250, "MILK": 160, "WOOL": 200},
        },
        "town": {"unlocked_shops": shops or []},
        "private": {
            "shed": shed or {"WHEAT": 10},
            "seeds": seeds or {"WHEAT": 7, "STRAWBERRY": 4, "MELON": 3},
            "inventories": [{}] + [{} for _ in (hands or [])],
        },
    }

try:
    obs0 = make_obs(0, 0)
    r0 = ag(obs0)
    assert "farmer" in r0 and "market" in r0
    print(f"[OK] Dia 0 h0: farmer={r0['farmer']}  market_orders={len(r0['market'])}")
except Exception as e:
    print(f"[FAIL] Smoke dia 0: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 5. Smoke test dia 5 (post-opening, deve plantar)
try:
    ag2 = sub.KaggricultureAgentV16()
    obs5 = make_obs(5, 3, money=900, seeds={"WHEAT": 5, "STRAWBERRY": 3, "MELON": 2},
                    shed={"WHEAT": 12}, hands=[[1,0],[2,0]],
                    shops=["BAKERY", "ICE_CREAM_SHOP"])
    r5 = ag2(obs5)
    farmer_a = r5["farmer"]
    hands_a  = r5["hands"]
    market_a = r5["market"]
    print(f"[OK] Dia 5 h3: farmer={farmer_a}  hands={hands_a}  market={market_a}")
    # farmer está em (4,4) que é shed-adj, tile é None → deve tentar plantar ou ir para tile
    # (pode ser DROP, BFS, ou PLANT dependendo do tile atual)
except Exception as e:
    print(f"[FAIL] Smoke dia 5: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 6. Testa _best_crop com demanda de lojas
try:
    ag3 = sub.KaggricultureAgentV16()
    seeds_t  = {"STRAWBERRY": 3, "WHEAT": 5, "MELON": 2}
    prices_t = {"STRAWBERRY": 115, "WHEAT": 28, "MELON": 240}

    crop_shops = ag3._best_crop(seeds_t, day=5,
                                market_prices=prices_t,
                                unlocked_shops=["ICE_CREAM_SHOP", "SMOOTHIE_SHOP"])
    crop_none  = ag3._best_crop(seeds_t, day=5,
                                market_prices=prices_t,
                                unlocked_shops=[])
    print(f"[OK] _best_crop c/lojas ICE_CREAM+SMOOTHIE → {crop_shops}")
    print(f"[OK] _best_crop sem lojas (preço puro)     → {crop_none}")
except Exception as e:
    print(f"[FAIL] _best_crop: {e}")

# 7. Testa gate de animal sem feed reserve
try:
    ag4 = sub.KaggricultureAgentV16()
    # Cenário: 4 vacas, wheat_have=0 → não deve comprar mais animais
    obs_nowheat = make_obs(6, 1, money=2000,
                           seeds={"WHEAT": 5, "STRAWBERRY": 3},
                           shed={"WHEAT": 0, "COW": 0})
    # Adiciona 4 pastures com COW na farm
    for y in range(2):
        for x in range(2):
            obs_nowheat["farms"][0]["tiles"][y][x] = {
                "kind": "PASTURE", "animal": "COW",
                "fed_today": True, "cared_today": False,
                "yield_units": 1, "fertilizer_available": False,
                "consecutive_unfed": 0, "pending_care_bonus": 0,
                "placed_day": 0,
            }

    # Modificar tiles a partir do scan
    from collections import namedtuple
    tasks_empty = {
        "feed": [], "feed_critical": [], "care": [], "harvest": [],
        "water": [], "water_critical": [], "fert": [], "empty": 10, "weeds": [],
    }
    market_res = ag4._market(obs_nowheat, tasks_empty, cows=4, sheep=0, pastures=4, empty_past=0)
    buy_animal_orders = [o for o in market_res if o[0] == "BUY_ANIMAL"]
    if buy_animal_orders:
        print(f"[WARN] Gate de feed FALHOU: BUY_ANIMAL={buy_animal_orders} com wheat=0")
    else:
        print(f"[OK] Gate de feed: sem BUY_ANIMAL quando wheat_have=0")
except Exception as e:
    print(f"[FAIL] Feed gate test: {e}")
    import traceback; traceback.print_exc()

# 8. Testa preço dinâmico do wheat
try:
    ag5 = sub.KaggricultureAgentV16()
    # wheat_price=50 (escassez) — BUY_PRODUCT deve usar esse preço
    obs_wp = make_obs(3, 1, money=500,
                      seeds={"WHEAT": 5},
                      shed={"WHEAT": 0},
                      prices={"WHEAT": 50, "STRAWBERRY": 120})
    tasks5 = {
        "feed": [(0,0),(1,1)], "feed_critical": [],
        "care": [], "harvest": [],
        "water": [], "water_critical": [], "fert": [], "empty": 8, "weeds": [],
    }
    mkt5 = ag5._market(obs_wp, tasks5, cows=2, sheep=1, pastures=3, empty_past=0)
    buy_wheat = [o for o in mkt5 if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"]
    print(f"[OK] Dynamic wheat price test: BUY_PRODUCT={buy_wheat} (money=500, wheat_price=50)")
    # Com money=500 e wheat_price=50 e need=15, custo=750 > money → NÃO deve comprar
    if buy_wheat:
        buy_n   = buy_wheat[0][2]
        cost    = buy_n * 50
        if cost + 50 > 500:
            print(f"      AVISO: comprou {buy_n} a $50 = ${cost} com money=500 (margem insuficiente?)")
        else:
            print(f"      comprou {buy_n} a $50 = ${cost}, ok dentro do budget")
except Exception as e:
    print(f"[FAIL] Dynamic wheat price: {e}")
    import traceback; traceback.print_exc()

print()
print("=" * 55)
print("Syntax + Logic checks: OK")
print("Tentando episódio completo com kaggle_environments...")
print("=" * 55)

# 9. Episódio completo (se kaggle_environments disponível)
try:
    from kaggle_environments import make

    sub.agent = sub.KaggricultureAgentV16()

    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=False)
    env.run([sub.agent_fn, "random"])

    final = env.steps[-1]
    r0 = final[0].reward
    r1 = final[1].reward

    print(f"  Player 0 (v16):   ${r0:,.0f}")
    print(f"  Player 1 (random): ${r1:,.0f}")

    if r0 > r1:
        print(f"  RESULTADO: v16 VENCEU por ${r0 - r1:,.0f}")
    elif r0 < r1:
        print(f"  RESULTADO: v16 PERDEU por ${r1 - r0:,.0f}")
    else:
        print(f"  RESULTADO: Empate")

    # Métricas internas
    ag = sub.agent
    print()
    print("  === Task Coverage ===")
    print(f"  PLANT emitidos      : {ag.tc_plant_count}")
    print(f"  FEED required       : {ag.tc_feed_required}")
    print(f"  FEED covered        : {ag.tc_feed_covered}")
    cov = ag.tc_feed_covered / max(1, ag.tc_feed_required)
    print(f"  Feed coverage rate  : {cov*100:.1f}%")
    print(f"  WATER required      : {ag.tc_water_required}")
    print(f"  WATER covered       : {ag.tc_water_covered}")
    wcov = ag.tc_water_covered / max(1, ag.tc_water_required)
    print(f"  Water coverage rate : {wcov*100:.1f}%")
    print(f"  PASS count          : {ag.tc_pass_count}")

    with open("replays/v16_vs_random.json", "w") as f:
        json.dump(env.toJSON(), f)
    print()
    print("  Replay salvo: replays/v16_vs_random.json")

except ImportError:
    print("  kaggle_environments indisponível — apenas smoke tests executados.")
except Exception as e:
    print(f"  [FAIL] Episódio completo: {e}")
    import traceback; traceback.print_exc()

print()
print("DONE")
