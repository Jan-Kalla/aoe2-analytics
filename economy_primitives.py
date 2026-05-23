from deap import gp
from military_primitives import add_military_nodes
from tactics_primitives import add_tactics_nodes


class Condition: pass


class Action: pass


class Rule: pass


class RuleList: pass


def get_economy_pset():
    pset = gp.PrimitiveSetTyped("MAIN", [], RuleList)

    # --- A. Klocki łączące reguły ---
    def combine_rules(r1, r2):
        return f"{r1}\n\n{r2}"

    pset.addPrimitive(combine_rules, [Rule, Rule], RuleList, name="TWO_RULES")
    pset.addPrimitive(combine_rules, [Rule, RuleList], RuleList, name="MANY_RULES")

    # --- B. Klocek tworzący pojedynczą regułę ---
    def make_rule(cond, act):
        return f"(defrule\n    {cond}\n=>\n    {act}\n)"

    pset.addPrimitive(make_rule, [Condition, Action], Rule, name="DEFRULE")

    # --- C. Klocki logiczne wewnątrz reguł (Agresywny bezpiecznik silnika) ---
    def and_cond(c1, c2):
        if c1.count('(') >= 8: return c1
        if c1.count('(') + c2.count('(') > 8: return c1
        return f"{c1}\n    {c2}"

    def do_both(a1, a2):
        if a1.count('(') >= 8: return a1
        if a1.count('(') + a2.count('(') > 8: return a1
        return f"{a1}\n    {a2}"

    pset.addPrimitive(and_cond, [Condition, Condition], Condition, name="AND")
    pset.addPrimitive(do_both, [Action, Action], Action, name="DO_BOTH")

    # ==========================================
    # 2. GENEROWANIE TERMINALI (Fakty i Komendy)
    # ==========================================

    # --- 0. Zabezpieczenia strukturalne drzewa (Genetyczne Introny) ---
    pset.addTerminal("; [Pusta Regula (Zabezpieczenie AST)]", Rule, name="t_empty_rule")
    pset.addTerminal("; [Koniec Listy Regul (Zabezpieczenie AST)]", RuleList, name="t_empty_list")

    # --- 1. Rozszerzone Budynki (Gospodarka i Wojsko) ---
    buildings = [
        "house", "mill", "lumber-camp", "mining-camp", "town-center",
        "barracks", "archery-range", "stable", "siege-workshop", "blacksmith", "market",
        "monastery", "university", "castle", "dock", "watch-tower"
    ]
    for b in buildings:
        pset.addTerminal(f"(building-type-count-total {b} < 1)", Condition, name=f"c_no_{b.replace('-', '_')}")
        pset.addTerminal(f"(building-type-count-total {b} < 2)", Condition, name=f"c_few_{b.replace('-', '_')}")
        pset.addTerminal(f"(can-build {b})", Condition, name=f"c_can_build_{b.replace('-', '_')}")
        pset.addTerminal(f"(build {b})", Action, name=f"a_build_{b.replace('-', '_')}")


    # --- 2. Numery Strategiczne Gospodarki (Ekspansja i Odległości) ---
    # 1. Zostawiamy "sztywne" wartości (dla kompatybilności z poprzednimi generacjami)
    town_sizes = [12, 20, 30, 40]
    for size in town_sizes:
        pset.addTerminal(f"(set-strategic-number sn-maximum-town-size {size})", Action, name=f"a_town_size_{size}")

    # 2. DODAJEMY NOWY: dynamiczny klocek (pozwala na mutację dowolnej wartości)
    # Używamy innej nazwy (np. a_dyn_town_size), żeby nie było konfliktu
    def set_town_size(size):
        return f"(set-strategic-number sn-maximum-town-size {size})"

    pset.addPrimitive(set_town_size, [int], Action, name="a_dyn_town_size")

    vill_dropsites = [
        ("wood", "lumber-camp"), ("food", "mill"),
        ("gold", "mining-camp"), ("stone", "mining-camp")
    ]
    for res, camp in vill_dropsites:
        pset.addTerminal(f"({res}-amount < 50)", Condition, name=f"c_low_{res}")
        pset.addTerminal(f"({res}-amount > 200)", Condition, name=f"c_has_{res}")
        pset.addTerminal(f"(set-strategic-number sn-{res}-gatherer-percentage 40)", Action, name=f"a_focus_{res}")

    # [NOWE] Sensory inteligencji przestrzennej (odległość drwali i górników) - umieszczone bezpiecznie poza pętlą!
    pset.addTerminal("(dropsite-min-distance wood > 5)", Condition, name="c_far_wood")
    pset.addTerminal("(dropsite-min-distance gold > 5)", Condition, name="c_far_gold")
    pset.addTerminal("(dropsite-min-distance stone > 5)", Condition, name="c_far_stone")

    # --- 3. Trening, Farmy i Utrzymanie ---
    pset.addTerminal("(unit-type-count villager < 30)", Condition, name="c_vills_under_30")
    pset.addTerminal("(unit-type-count villager < 60)", Condition, name="c_vills_under_60")
    pset.addTerminal("(unit-type-count villager < 100)", Condition, name="c_vills_under_100")
    pset.addTerminal("(idle-farm-count < 2)", Condition, name="c_need_farms")

    pset.addTerminal("(train villager)", Action, name="a_train_vill")
    pset.addTerminal("(build farm)", Action, name="a_build_farm")

    # --- 4. Pełne Drzewo Badań Gospodarczych ---
    techs = [
        ("ri-loom", "loom"), ("ri-wheel-barrow", "wheel_barrow"), ("ri-hand-cart", "hand_cart"),
        ("ri-double-bit-axe", "axe_1"), ("ri-bow-saw", "axe_2"), ("ri-two-man-saw", "axe_3"),
        ("ri-horse-collar", "farm_1"), ("ri-heavy-plow", "farm_2"), ("ri-crop-rotation", "farm_3"),
        ("ri-gold-mining", "gold_1"), ("ri-gold-shaft-mining", "gold_2"),
        ("ri-stone-mining", "stone_1"), ("ri-stone-shaft-mining", "stone_2")
    ]
    for tech, name in techs:
        pset.addTerminal(f"(can-research {tech})", Condition, name=f"c_can_res_{name}")
        pset.addTerminal(f"(research {tech})", Action, name=f"a_res_{name}")

    # --- 5. Awans Epok ---
    ages = ["dark-age", "feudal-age", "castle-age", "imperial-age"]
    for age in ages:
        pset.addTerminal(f"(current-age == {age})", Condition, name=f"c_is_{age.replace('-', '_')}")
        if age != "dark-age":
            pset.addTerminal(f"(can-research {age})", Condition, name=f"c_can_go_{age.replace('-', '_')}")
            pset.addTerminal(f"(research {age})", Action, name=f"a_go_{age.replace('-', '_')}")

    # ==========================================
    # WPIĘCIE MODUŁÓW
    # ==========================================
    add_military_nodes(pset, Condition, Action)
    add_tactics_nodes(pset, Condition, Action)

    return pset