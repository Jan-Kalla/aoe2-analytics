import random
import functools


# Funkcja transparentna - zaspokaja głód DEAP-a na "Primitives" dla typu liczbowego
def i_val(x):
    return x


def is_valid_ident(val):
    """
    Sprawdza, czy wylosowany argument jest czystym identyfikatorem.
    Odrzuca wszystko, co ma nawiasy (czyli jest komendą Lisp) i spacje,
    ale ZEZWALA na operatory matematyczne niezbędne dla DUC.
    """
    s = str(val).strip()
    # Odrzucamy puste stringi i komendy z nawiasami
    if not s or "(" in s or ")" in s or " " in s:
        return False
    # Zezwalamy na operatory (usunięto blokadę z poprzedniej wersji!)
    return True


def add_tactics_nodes(pset, Condition, Action):
    # ==========================================
    # MODUŁ TAKTYCZNY (Mikro, SN, Handel, UserPatch)
    # ==========================================

    pset.addEphemeralConstant("rand_int_100", functools.partial(random.randint, 0, 100), int)
    pset.addEphemeralConstant("rand_int_40", functools.partial(random.randint, 1, 40), int)
    pset.addEphemeralConstant("rand_int_255", functools.partial(random.randint, 50, 255), int)
    pset.addPrimitive(i_val, [int], int, name="i_val")

    def set_attack_group_size(size):
        return f"(set-strategic-number sn-maximum-attack-group-size {size})"

    def set_attack_percent(percent):
        return f"(set-strategic-number sn-percent-attack-soldiers {percent})"

    def set_camp_distance(dist):
        return f"(set-strategic-number sn-camp-max-distance {dist})"

    pset.addPrimitive(set_attack_group_size, [int], Action, name="a_dynamic_group_size")
    pset.addPrimitive(set_attack_percent, [int], Action, name="a_dynamic_atk_percent")
    pset.addPrimitive(set_camp_distance, [int], Action, name="a_dynamic_camp_dist")

    pset.addTerminal("(game-time > 1000)", Condition, name="c_game_time_15min")
    pset.addTerminal("(game-time > 2000)", Condition, name="c_game_time_30min")

    pset.addTerminal("(set-strategic-number sn-total-number-explorers 1)", Action, name="a_enable_scout")
    pset.addTerminal("(set-strategic-number sn-total-number-explorers 0)", Action, name="a_disable_scout")
    pset.addTerminal("(set-strategic-number sn-number-explore-groups 1)", Action, name="a_explore_enable_groups")

    def set_civ_scout_cap(cap):
        return f"(set-strategic-number sn-cap-civilian-explorers {cap})"

    def set_civ_scout_pct(pct):
        return f"(set-strategic-number sn-percent-civilian-explorers {pct})"

    pset.addPrimitive(set_civ_scout_cap, [int], Action, name="a_dynamic_civ_scout_cap")
    pset.addPrimitive(set_civ_scout_pct, [int], Action, name="a_dynamic_civ_scout_pct")

    pset.addTerminal("(town-under-attack)", Condition, name="c_under_attack")

    # [POPRAWKA] Usunięto nieznane w silniku komendy up-micro-reverse/forward
    pset.addTerminal("(do-nothing)", Action, name="a_micro_kiting_archers")
    pset.addTerminal("(do-nothing)", Action, name="a_micro_charge_infantry")

    pset.addTerminal("(up-target-objects c: archery-class action-default c: siege-weapon-class c: 0)", Action,
                     name="a_focus_fire_siege")
    pset.addTerminal("(up-retreat-to town-center c: 0)", Action, name="a_retreat_tc")
    pset.addTerminal("(up-retreat-to castle c: 0)", Action, name="a_retreat_castle")

    pset.addTerminal("(up-build place-forward 82 c: 0)", Action, name="a_forward_castle")
    pset.addTerminal("(up-build place-forward 79 c: 0)", Action, name="a_forward_tower")
    pset.addTerminal("(up-build place-forward 12 c: 0)", Action, name="a_forward_barracks")

    pset.addTerminal("(set-strategic-number sn-placement-zone 0)", Action, name="a_zone_defensive")
    pset.addTerminal("(set-strategic-number sn-placement-zone 1)", Action, name="a_zone_forward")
    pset.addTerminal("(set-strategic-number sn-allow-adjacent-dropsites 1)", Action, name="a_compact_dropsites")

    commodities = ["wood", "food", "stone"]
    for res in commodities:
        pset.addTerminal(f"(can-buy-commodity {res})", Condition, name=f"c_can_buy_{res}")
        pset.addTerminal(f"(buy-commodity {res})", Action, name=f"a_buy_{res}")
        pset.addTerminal(f"(can-sell-commodity {res})", Condition, name=f"c_can_sell_{res}")
        pset.addTerminal(f"(sell-commodity {res})", Action, name=f"a_sell_{res}")

    pset.addTerminal("(unit-type-count monk > 0)", Condition, name="c_has_monk")
    pset.addTerminal("(set-strategic-number sn-relic-return-distance 255)", Action, name="a_hunt_relics")

    def sn_target_villagers(weight):
        return f"(set-strategic-number sn-special-attack-type1 904) (set-strategic-number sn-special-attack-influence1 {weight})"

    pset.addPrimitive(sn_target_villagers, [int], Action, name="a_target_villagers")
    pset.addTerminal(
        "(set-strategic-number sn-target-evaluation-distance 0) (set-strategic-number sn-target-evaluation-hitpoints 10000)",
        Action, name="a_focus_weak_targets")

    unit_classes = ["infantry-class", "archery-class", "cavalry-class", "siege-weapon-class", "monk-class", "904"]
    for uc in unit_classes:
        pset.addTerminal(uc, Action, name=f"t_class_{uc.replace('-class', '').replace('904', 'villager')}")

    pset.addTerminal("military-units-class", Action, name="t_class_all_military")

    pset.addTerminal("<", Action, name="t_op_lt")
    pset.addTerminal("<=", Action, name="t_op_lte")
    pset.addTerminal(">", Action, name="t_op_gt")

    safe_targets = ["town-center", "castle", "watch-tower", "monastery", "monk"]
    for st in safe_targets:
        pset.addTerminal(st, Action, name=f"t_target_{st.replace('-', '_')}")

    def duc_dynamic_retreat(unit_class, operator, hp_threshold, safe_target):
        if not all(is_valid_ident(x) for x in [unit_class, operator, safe_target]):
            return "(do-nothing)"
        return f"""
        (up-reset-search 1 1 1 1)
        (up-find-local c: {unit_class} c: 5)
        (up-filter-hp c: {operator} c: {hp_threshold})
        (up-target-objects 0 action-move -1 {safe_target})
        """

    def duc_blind_flee(unit_class, operator, hp_threshold, safe_target):
        if not all(is_valid_ident(x) for x in [unit_class, operator, safe_target]):
            return "(do-nothing)"
        return f"""
        (up-reset-search 1 1 1 1)
        (up-find-local c: {unit_class} c: 1)
        (up-filter-hp c: {operator} c: {hp_threshold})
        (up-drop-resources {safe_target} c: 5)
        """

    def duc_dynamic_hunt(unit_class, target_class):
        if not all(is_valid_ident(x) for x in [unit_class, target_class]):
            return "(do-nothing)"
        return f"""
        (up-reset-search 1 1 1 1)
        (up-find-local c: {unit_class} c: 10)
        (up-find-remote c: {target_class} c: 1)
        (up-target-objects 0 action-attack -1 -1)
        """

    pset.addPrimitive(duc_dynamic_retreat, [Action, Action, int, Action], Action, name="a_duc_dyn_retreat")
    pset.addPrimitive(duc_blind_flee, [Action, Action, int, Action], Action, name="a_duc_blind_flee")
    pset.addPrimitive(duc_dynamic_hunt, [Action, Action], Action, name="a_duc_dyn_hunt")

    return pset