"""
A.12 — Cenário Alternativo: "Value-First Agent"

Uso local apenas, sem deploy:
    python scenario_a12.py
    python scenario_a12.py --episode seb_episodes/episode-91150561-replay.json
"""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from submission import KaggricultureAgentV17, CROPS, ANIMALS, STRAWBERRY_MIN_DAYS_LEFT


class KaggricultureAgentA12(KaggricultureAgentV17):
    TASK_VALUE_THRESHOLD = 50
    AGGRESSIVE_ENDGAME_DAY = 26

    def _task_value(self, tile, action_type, day, inv):
        if action_type == "WATER":
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop") or ""
                info = CROPS.get(crop, {})
                age = day - (tile.get("planted_day") or day)
                max_age = info.get("max", 2)
                if age >= max_age:
                    return 0
                yield_units = tile.get("yield_units") or 0
                price = info.get("price", 0)
                days_left = max(1, max_age - age)
                return (yield_units * price) / days_left
            return 0

        if action_type == "FEED":
            if isinstance(tile, dict) and tile.get("animal"):
                animal = tile.get("animal") or ""
                info = ANIMALS.get(animal, {})
                price = info.get("price", 0)
                interval = 2 if animal == "COW" else (3 if animal == "SHEEP" else 1)
                return price / interval
            return 0

        if action_type == "CARE":
            if isinstance(tile, dict) and tile.get("animal"):
                if self._is_care_valuable(tile, day):
                    animal = tile.get("animal") or ""
                    info = ANIMALS.get(animal, {})
                    price = info.get("price", 0)
                    interval = 2 if animal == "COW" else (3 if animal == "SHEEP" else 1)
                    return price / interval
            return 0

        if action_type == "HARVEST":
            if isinstance(tile, dict):
                if tile.get("kind") == "PASTURE" and (tile.get("yield_units") or 0) > 0:
                    animal = tile.get("animal") or ""
                    info = ANIMALS.get(animal, {})
                    return info.get("price", 0) * (tile.get("yield_units") or 0)
                if tile.get("kind") == "PLANT" and (tile.get("yield_units") or 0) > 0:
                    crop = tile.get("crop") or ""
                    info = CROPS.get(crop, {})
                    return info.get("price", 0) * (tile.get("yield_units") or 0)
            return 0

        if action_type == "COLLECT_FERTILIZER":
            if isinstance(tile, dict) and tile.get("fertilizer_available"):
                if self._has_high_value_crops({}):
                    return 100
            return 0

        return 0

    def _is_task_worth_doing(self, tile, action_type, day, inv):
        value = self._task_value(tile, action_type, day, inv)
        return value >= self.TASK_VALUE_THRESHOLD

    def _should_collect_fert(self, tile, day):
        if not isinstance(tile, dict) or tile.get("kind") != "PASTURE":
            return False
        if not tile.get("fertilizer_available"):
            return False
        if not self._has_high_value_crops({}):
            return False
        if day >= self.AGGRESSIVE_ENDGAME_DAY:
            return False
        return True

    def _should_water(self, tile, day):
        if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
            return False
        if tile.get("watered_today"):
            return False
        crop = tile.get("crop") or ""
        info = CROPS.get(crop, {})
        age = day - (tile.get("planted_day") or day)
        max_age = info.get("max", 2)
        if age >= max_age:
            return False
        if crop in ("WHEAT", "CARROT", "MELON") and age >= max_age - 1:
            return False
        return True

    def _decide(self, tile, shed, seeds, day, inv, pos, hour, cows, sheep, empty_past, tasks=None):
        inv = inv or {}
        x, y = pos if pos else (-1, -1)

        if day >= 28:
            if isinstance(tile, dict) and tile.get("kind") == "PASTURE" and tile.get("animal"):
                if tile.get("yield_units", 0) > 0:
                    return ["HARVEST"]
                return ["PASS"]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if tile.get("yield_units", 0) > 0:
                    return ["HARVEST"]
                return ["PASS"]
            return ["PASS"]

        if day >= 27 and tile is None:
            return ["PASS"]

        if day >= 25 and tile is None:
            return ["PASS"]

        if day >= 27 and isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop") or ""
            info = CROPS.get(crop, {})
            age = day - (tile.get("planted_day") or day)
            if crop in ("WHEAT", "CARROT", "MELON"):
                if age >= info.get("max", 2):
                    if tile.get("yield_units", 0) > 0:
                        return ["HARVEST"]
                return ["PASS"]

        if tile is None:
            days_left = 29 - day
            animal_in_shed = shed.get("COW", 0) + shed.get("SHEEP", 0)
            if animal_in_shed > 0 and empty_past == 0 and day <= 15:
                return ["BUILD_PASTURE"]
            if hour <= 20:
                if seeds.get("STRAWBERRY", 0) > 0 and days_left >= STRAWBERRY_MIN_DAYS_LEFT:
                    return ["PLANT", "STRAWBERRY"]
                if seeds.get("MELON", 0) > 0 and day <= 12:
                    return ["PLANT", "MELON"]
                if seeds.get("WHEAT", 0) > 0 and day <= 8:
                    return ["PLANT", "WHEAT"]
            if animal_in_shed > 0 and day <= 15:
                return ["BUILD_PASTURE"]
            return ["PASS"]

        if isinstance(tile, dict) and tile.get("kind") == "WEED":
            return ["DIG"]

        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            crop = tile.get("crop") or ""
            info = CROPS.get(crop, {})
            age = day - (tile.get("planted_day") or day)
            if age >= info.get("max", 2) or tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            if not tile.get("watered_today") and self._should_water(tile, day):
                return ["WATER"]
            return ["PASS"]

        if isinstance(tile, dict) and tile.get("kind") == "PASTURE":
            if tile.get("animal") is None:
                for a in ("COW", "SHEEP"):
                    if inv.get(a, 0) > 0:
                        return ["PLACE", a]
                return ["PASS"]
            fed = tile.get("fed_today") or (pos and (x, y) in self.fed_this_day)
            cared = tile.get("cared_today") or (pos and (x, y) in self.cared_this_day)
            if not fed and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0):
                if self._is_task_worth_doing(tile, "FEED", day, inv):
                    return ["FEED"]
            if tile.get("fertilizer_available") and self._should_collect_fert(tile, day):
                return ["COLLECT_FERTILIZER"]
            if not cared and self._is_care_valuable(tile, day):
                if self._is_task_worth_doing(tile, "CARE", day, inv):
                    return ["CARE"]
            if tile.get("yield_units", 0) > 0:
                return ["HARVEST"]
            return ["PASS"]

        return ["PASS"]

    def _move_priorities(self, shed, day, inv, empty_past=0, farm=None):
        inv = inv or {}
        animal_in_shed = shed.get("COW", 0) + shed.get("SHEEP", 0)
        return [
            lambda t, x, y: (isinstance(t, dict)
                             and ((t.get("kind") == "PASTURE" and (t.get("yield_units") or 0) > 0)
                                  or (t.get("kind") == "PLANT" and (
                                      (t.get("yield_units") or 0) > 0
                                      or (day - (t.get("planted_day") or day))
                                         >= CROPS.get(str(t.get("crop") or ""), {}).get("max", 99))))),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("fed_today")
                             and (x, y) not in self.fed_this_day
                             and (shed.get("WHEAT", 0) > 0 or inv.get("WHEAT", 0) > 0)
                             and self._is_task_worth_doing(t, "FEED", day, inv)),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") and not t.get("cared_today")
                             and (x, y) not in self.cared_this_day
                             and self._is_care_valuable(t, day)
                             and self._is_task_worth_doing(t, "CARE", day, inv)),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PLANT"
                             and self._should_water(t, day)
                             and (x, y) not in self.watered_this_day
                             and self._is_task_worth_doing(t, "WATER", day, inv)),
            lambda t, x, y: (self._should_collect_fert(t, day)),
            lambda t, x, y: (isinstance(t, dict) and t.get("kind") == "PASTURE"
                             and t.get("animal") is None and inv
                             and any(inv.get(a, 0) > 0 for a in ("COW", "SHEEP"))),
            lambda t, x, y: (
                t is None
                and animal_in_shed > 0
                and empty_past == 0
                and day <= 15
            ),
            lambda t, x, y: t is None,
            lambda t, x, y: isinstance(t, dict) and t.get("kind") == "WEED",
        ]


agent_a12 = KaggricultureAgentA12()


def agent_fn(observation, configuration=None):
    return agent_a12(observation)


def main_agent(observation, configuration=None):
    return agent_a12(observation)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A.12 scenario runner")
    parser.add_argument("--episode", type=str, default="seb_episodes/episode-91150561-replay.json")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    import simulate_local
    result = simulate_local.simulate_episode(args.episode, verbose=not args.quiet)
    simulate_local.analyze_actions(result)
