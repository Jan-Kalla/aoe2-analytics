import random
import functools


# [NOWE] Funkcja transparentna - zaspokaja głód DEAP-a na "Primitives" dla typu liczbowego,
# a podczas kompilacji po prostu oddaje czystą liczbę do skryptu AoE2.
def i_val(x):
    return x


def add_tactics_nodes(pset, Condition, Action):
    # ==========================================
    # MODUŁ TAKTYCZNY (Mikro, SN, Handel, UserPatch)
    # ==========================================

    # --- 0. Używamy wbudowanego typu 'int' zamiast lokalnych klas ---

    # Dodajemy ERC (Ewoluujące Liczby) jako czyste Integery
    pset.addEphemeralConstant("rand_int_100", functools.partial(random.randint, 0, 100), int)
    pset.addEphemeralConstant("rand_int_40", functools.partial(random.randint, 1, 40), int)
    pset.addEphemeralConstant("rand_int_255", functools.partial(random.randint, 50, 255), int)

    # Rejestrujemy naszą przezroczystą funkcję dla liczb całkowitych
    pset.addPrimitive(i_val, [int], int, name="i_val")

    # --- 1. Numery Strategiczne (Makro-Taktyka i Agresja) ---
    def set_attack_group_size(size):
        return f"(set-strategic-number sn-maximum-attack-group-size {size})"

    def set_attack_percent(percent):
        return f"(set-strategic-number sn-percent-attack-soldiers {percent})"

    def set_camp_distance(dist):
        return f"(set-strategic-number sn-camp-max-distance {dist})"

    # Klocki taktyczne przyjmują teraz wbudowany typ 'int'
    pset.addPrimitive(set_attack_group_size, [int], Action, name="a_dynamic_group_size")
    pset.addPrimitive(set_attack_percent, [int], Action, name="a_dynamic_atk_percent")
    pset.addPrimitive(set_camp_distance, [int], Action, name="a_dynamic_camp_dist")

    # W tactics_primitives.py
    pset.addTerminal("(game-time > 1000)", Condition, name="c_game_time_15min")
    pset.addTerminal("(game-time > 2000)", Condition, name="c_game_time_30min")

    # --- 1.5 Eksploracja i Zwiad (Scouting Engine) ---
    pset.addTerminal("(set-strategic-number sn-total-number-explorers 1)", Action, name="a_enable_scout")
    pset.addTerminal("(set-strategic-number sn-total-number-explorers 0)", Action, name="a_disable_scout")
    pset.addTerminal("(set-strategic-number sn-number-explore-groups 1)", Action, name="a_explore_enable_groups")

    # [NOWE] Zamiast zakazywać, pozwalamy ewolucji samej ustalić limity!
    def set_civ_scout_cap(cap):
        return f"(set-strategic-number sn-cap-civilian-explorers {cap})"

    def set_civ_scout_pct(pct):
        return f"(set-strategic-number sn-percent-civilian-explorers {pct})"

    # Klocki taktyczne przyjmują ewoluującą liczbę (int)
    pset.addPrimitive(set_civ_scout_cap, [int], Action, name="a_dynamic_civ_scout_cap")
    pset.addPrimitive(set_civ_scout_pct, [int], Action, name="a_dynamic_civ_scout_pct")

    # --- 2. Magia UserPatch 1.5 (Mikrozarządzanie i Planowanie Przestrzenne) ---
    pset.addTerminal("(town-under-attack)", Condition, name="c_under_attack")
    pset.addTerminal("(up-micro-reverse c: archery-class c: infantry-class)", Action, name="a_micro_kiting_archers")
    pset.addTerminal("(up-micro-forward c: infantry-class c: archery-class)", Action, name="a_micro_charge_infantry")
    pset.addTerminal("(up-target-objects c: archery-class action-default c: siege-weapon-class c: 0)", Action,
                     name="a_focus_fire_siege")
    pset.addTerminal("(up-retreat-to town-center c: 0)", Action, name="a_retreat_tc")
    pset.addTerminal("(up-retreat-to castle c: 0)", Action, name="a_retreat_castle")

    # Budynki w bazie wroga i sztuczne murowanie
    pset.addTerminal("(up-build place-forward 82 c: 0)", Action, name="a_forward_castle")
    pset.addTerminal("(up-build place-forward 79 c: 0)", Action, name="a_forward_tower")
    pset.addTerminal("(up-build place-forward 12 c: 0)", Action, name="a_forward_barracks")

    pset.addTerminal("(set-strategic-number sn-placement-zone 0)", Action, name="a_zone_defensive")
    pset.addTerminal("(set-strategic-number sn-placement-zone 1)", Action, name="a_zone_forward")
    pset.addTerminal("(set-strategic-number sn-allow-adjacent-dropsites 1)", Action, name="a_compact_dropsites")

    # --- 3. Ekonomia Zaawansowana (Handel na Rynku) ---
    commodities = ["wood", "food", "stone"]
    for res in commodities:
        pset.addTerminal(f"(can-buy-commodity {res})", Condition, name=f"c_can_buy_{res}")
        pset.addTerminal(f"(buy-commodity {res})", Action, name=f"a_buy_{res}")
        pset.addTerminal(f"(can-sell-commodity {res})", Condition, name=f"c_can_sell_{res}")
        pset.addTerminal(f"(sell-commodity {res})", Action, name=f"a_sell_{res}")

    # --- 4. Relikwie i Mnisi ---
    pset.addTerminal("(unit-type-count monk > 0)", Condition, name="c_has_monk")
    pset.addTerminal("(train monk)", Action, name="a_train_monk")
    pset.addTerminal("(set-strategic-number sn-relic-return-distance 255)", Action, name="a_hunt_relics")

    return pset