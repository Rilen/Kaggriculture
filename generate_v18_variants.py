import os
import re

with open('submission.py', 'r', encoding='utf-8') as f:
    base_code = f.read()

def write_variant(filename, code):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)

# ----------------- v18a -----------------
code_a = base_code.replace('KaggricultureAgentV17', 'KaggricultureAgentV18A')
code_a = code_a.replace('TARGET_COW      = 8', 'TARGET_COW = 0')
code_a = code_a.replace('TARGET_SHEEP    = 6', 'TARGET_SHEEP = 0')

opening_a = '''
        if hour == 1:
            market = [
                ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                ["BUY_SEED", "STRAWBERRY", 5],
                ["BUY_SEED", "MELON", 10],
                ["BUY_SEED", "WHEAT", 10],
            ]
        elif hour == 2:
            market = []
'''
# Using exactly the lines to replace safely
old_open = '''        if hour == 1:
            # v17 vs v15: MELON 12 -> MELON 9 + STRAWBERRY 3
            market = [
                ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                ["BUY_ANIMAL", "SHEEP", 2],
                ["BUY_ANIMAL", "COW",   2],
                ["BUY_SEED",   "WHEAT", 7],
                ["BUY_SEED",   "MELON", 9],         # era 12
                ["BUY_SEED",   "STRAWBERRY", 3],    # NOVO — alto valor + lojas
            ]
        elif hour == 2:
            market = [["BUY_PRODUCT", "WHEAT", 2]]'''
            
code_a = code_a.replace(old_open, opening_a.strip('\n'))

# 1. Sell everything (no keep for WHEAT)
code_a = re.sub(r'if item == "WHEAT":.*?elif item == "FERTILIZER":', 
r'''if item == "WHEAT":
                sell = qty
            elif item == "FERTILIZER":''', code_a, flags=re.DOTALL)

# 2. Block BUY_ANIMAL and BUY_PRODUCT WHEAT
code_a = re.sub(r'# BUY_PRODUCT WHEAT.*?# HIRE adaptativo', '# HIRE adaptativo', code_a, flags=re.DOTALL)
code_a = re.sub(r'# BUY_ANIMAL.*?# BUY_LAND', '# BUY_LAND', code_a, flags=re.DOTALL)

# 3. Seeds logic
seed_logic_a = '''
        # Seeds adaptativo para v18A (Crop Heavy, no pure-spam)
        if len(orders) < MAX_MARKET_ORDERS:
            total_seeds = sum(seeds.values())
            needed = max(0, tasks["empty"] - total_seeds)
            if needed > 0 and money > 400:
                if days_left >= 12 and money > 100 * needed + 200:
                    orders.append(["BUY_SEED", "STRAWBERRY", min(needed, 5)])
                    money -= 100 * min(needed, 5)
                elif days_left >= 10 and money > 80 * needed + 200:
                    orders.append(["BUY_SEED", "MELON", min(needed, 5)])
                    money -= 80 * min(needed, 5)
                elif days_left >= 4 and money > 10 * needed + 50:
                    orders.append(["BUY_SEED", "WHEAT", min(needed, 5)])
                    money -= 10 * min(needed, 5)
'''
code_a = re.sub(r'# Seeds — MUDANCA 5: adiciona STRAWBERRY conservadora.*?return orders', seed_logic_a + '\n        return orders', code_a, flags=re.DOTALL)

# 4. _decide: disable EMERGENCY BUILD PASTURE and BUILD PASTURE
code_a = re.sub(r'# Caso 1: emergencia.*?if animal_in_shed > 0 and empty_past == 0 and day <= 15:.*?return \["BUILD_PASTURE"\]', '', code_a, flags=re.DOTALL)
code_a = re.sub(r'# BUILD_PASTURE para expansao normal.*?if animal_in_shed > 0 and day <= 15:.*?return \["BUILD_PASTURE"\]', '', code_a, flags=re.DOTALL)

# Remove emergency build pasture from move priorities
code_a = re.sub(r'# 7\. Cirurgia B — EMERGENCY BUILD PASTURE:.*?lambda t, x, y: \(.*?day <= 15.*?\),', '', code_a, flags=re.DOTALL)

write_variant('submission_v18a.py', code_a)


# ----------------- v18b -----------------
code_b = base_code.replace('KaggricultureAgentV17', 'KaggricultureAgentV18B')
code_b = code_b.replace('TARGET_COW      = 8', 'TARGET_COW = 2')
code_b = code_b.replace('TARGET_SHEEP    = 6', 'TARGET_SHEEP = 0')

opening_b = '''
        if hour == 1:
            market = [
                ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
                ["BUY_ANIMAL", "COW", 2],
                ["BUY_SEED", "STRAWBERRY", 5],
                ["BUY_SEED", "MELON", 5],
            ]
        elif hour == 2:
            market = [["BUY_PRODUCT", "WHEAT", 2]]
'''
code_b = code_b.replace(old_open, opening_b.strip('\n'))

seed_logic_b = seed_logic_a.replace('v18A', 'v18B')
code_b = re.sub(r'# Seeds — MUDANCA 5: adiciona STRAWBERRY conservadora.*?return orders', seed_logic_b + '\n        return orders', code_b, flags=re.DOTALL)
# For v18b we KEEP BUY_ANIMAL logic (just TARGET_COW=2) and we KEEP WHEAT product logic (since it has 2 cows).
# And we KEEP build pasture. So that's all.
write_variant('submission_v18b.py', code_b)


# ----------------- v18c -----------------
code_c = base_code.replace('KaggricultureAgentV17', 'KaggricultureAgentV18C')
code_c = code_c.replace('TARGET_COW      = 0', 'TARGET_COW = 0') # v17 targets
code_c = code_c.replace('TARGET_SHEEP    = 0', 'TARGET_SHEEP = 0')

# For v18c, we add _eval_roi
eval_roi = '''
    def _eval_roi(self, obs, days_left):
        prices = obs.get("market", {}).get("prices", {})
        roi = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0, "CARROT": 0}
        
        # WHEAT (seed: 10, grow: 4, yield: 1)
        if days_left >= 4:
            roi["WHEAT"] = (prices.get("WHEAT", 25) - 10) / 4.0
        # MELON (seed: 80, grow: 10, yield: 1)
        if days_left >= 10:
            roi["MELON"] = (prices.get("MELON", 250) - 80) / 10.0
        # STRAWBERRY (seed: 100, grow: 12, yield: 1)
        if days_left >= 12:
            roi["STRAWBERRY"] = (prices.get("STRAWBERRY", 120) - 100) / 12.0
            
        best = max(roi, key=roi.get)
        if roi[best] <= 0: return None
        return best
'''

code_c = code_c.replace('    def _count_animals(self, farm):', eval_roi.strip('\n') + '\n\n    def _count_animals(self, farm):')

# Adaptive seed logic
seed_logic_c = '''
        # Seeds adaptativo para v18C (ROI Dynamics)
        if len(orders) < MAX_MARKET_ORDERS:
            total_seeds = sum(seeds.values())
            needed = max(0, tasks["empty"] - total_seeds)
            if needed > 0 and money > 400:
                best_crop = self._eval_roi(obs, days_left)
                if best_crop:
                    seed_cost = CROPS[best_crop]["seed_cost"]
                    max_buy = min(needed, 5)
                    if money > seed_cost * max_buy + 200:
                        orders.append(["BUY_SEED", best_crop, max_buy])
                        money -= seed_cost * max_buy
'''
code_c = re.sub(r'# Seeds — MUDANCA 5: adiciona STRAWBERRY conservadora.*?return orders', seed_logic_c + '\n        return orders', code_c, flags=re.DOTALL)
code_c = re.sub(r'# BUY_PRODUCT WHEAT.*?# HIRE adaptativo', '# HIRE adaptativo', code_c, flags=re.DOTALL)
code_c = re.sub(r'# BUY_ANIMAL.*?# BUY_LAND', '# BUY_LAND', code_c, flags=re.DOTALL)
code_c = code_c.replace(old_open, opening_a.strip('\n'))

# Crop logic in _decide
decide_c = '''
            # Casos 2 e 3: PLANT adaptativo
            if hour <= 20:
                for crop_choice in ("STRAWBERRY", "MELON", "WHEAT"):
                    if seeds.get(crop_choice, 0) > 0 and days_left >= CROPS.get(crop_choice, {}).get("first", 99):
                        return ["PLANT", crop_choice]
'''
code_c = re.sub(r'# Casos 2 e 3: PLANT prioritario.*?if animal_in_shed > 0 and day <= 15:', decide_c.strip('\n') + '\n\n            # BUILD_PASTURE para expansao normal\n            if animal_in_shed > 0 and day <= 15:', code_c, flags=re.DOTALL)

# Block emergency pasture build
code_c = re.sub(r'# Caso 1: emergencia.*?if animal_in_shed > 0 and empty_past == 0 and day <= 15:.*?return \["BUILD_PASTURE"\]', '', code_c, flags=re.DOTALL)
code_c = re.sub(r'# BUILD_PASTURE para expansao normal.*?if animal_in_shed > 0 and day <= 15:.*?return \["BUILD_PASTURE"\]', '', code_c, flags=re.DOTALL)
code_c = re.sub(r'# 7\. Cirurgia B — EMERGENCY BUILD PASTURE:.*?lambda t, x, y: \(.*?day <= 15.*?\),', '', code_c, flags=re.DOTALL)

write_variant('submission_v18c.py', code_c)
print("Variantes geradas com sucesso.")
