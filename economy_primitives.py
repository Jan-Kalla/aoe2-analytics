from deap import gp
from military_primitives import add_military_nodes
from tactics_primitives import add_tactics_nodes


class Condition: pass


class Action: pass


class Rule: pass


class RuleList: pass


def get_economy_pset():
    pset = gp.PrimitiveSetTyped("MAIN", [], RuleList)

    def combine_rules(r1, r2):
        return f"{r1}\n\n{r2}"

    pset.addPrimitive(combine_rules, [Rule, Rule], RuleList, name="TWO_RULES")
    pset.addPrimitive(combine_rules, [Rule, RuleList], RuleList, name="MANY_RULES")

    def make_rule(cond, act):
        # [POPRAWKA] Jeśli ewolucja spróbuje wstawić "goły" identyfikator, naprawiamy go!
        if not cond.strip().startswith("("): cond = "(true)"
        if not act.strip().startswith("("): act = "(do-nothing)"
        return f"(defrule\n    {cond}\n=>\n    {act}\n)"

    pset.addPrimitive(make_rule, [Condition, Action], Rule, name="DEFRULE")

    def and_cond(c1, c2):
        # [POPRAWKA] Zabezpieczenie logiczne węzłów wewnętrznych
        if not c1.strip().startswith("("): c1 = "(true)"
        if not c2.strip().startswith("("): c2 = "(true)"

        if c1.count('(') >= 8: return c1
        if c1.count('(') + c2.count('(') > 8: return c1
        return f"{c1}\n    {c2}"

    def do_both(a1, a2):
        # [POPRAWKA] Blokujemy wstawianie "gołych" operatorów jako akcji łączonych!
        if not a1.strip().startswith("("): a1 = "(do-nothing)"
        if not a2.strip().startswith("("): a2 = "(do-nothing)"

        if a1.count('(') >= 8: return a1
        if a1.count('(') + a2.count('(') > 8: return a1
        return f"{a1}\n    {a2}"

    pset.addPrimitive(and_cond, [Condition, Condition], Condition, name="AND")
    pset.addPrimitive(do_both, [Action, Action], Action, name="DO_BOTH")

    # ==========================================
    # 2. GENEROWANIE TERMINALI (Fakty i Komendy)
    # ==========================================

    pset.addTerminal("; [Pusta Regula (Zabezpieczenie AST)]", Rule, name="t_empty_rule")
    pset.addTerminal("; [Koniec Listy Regul (Zabezpieczenie AST)]", RuleList, name="t_empty_list")

    buildings = [
        "house", "mill", "lumber-camp", "mining-camp", "town-center",
        "barracks", "archery-range", "stable", "siege-workshop", "blacksmith", "market",
        "monastery", "university", "castle", "dock", "watch-tower",
        "bombard-tower", "outpost", "palisade-wall", "stone-wall", "gate"
    ]
    for b in buildings:
        pset.addTerminal(f"(building-type-count-total {b} < 1)", Condition, name=f"c_no_{b.replace('-', '_')}")
        pset.addTerminal(f"(building-type-count-total {b} < 2)", Condition, name=f"c_few_{b.replace('-', '_')}")
        pset.addTerminal(f"(can-build {b})", Condition, name=f"c_can_build_{b.replace('-', '_')}")
        pset.addTerminal(f"(build {b})", Action, name=f"a_build_{b.replace('-', '_')}")

    town_sizes = [12, 20, 30, 40]
    for size in town_sizes:
        pset.addTerminal(f"(set-strategic-number sn-maximum-town-size {size})", Action, name=f"a_town_size_{size}")

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

    pset.addTerminal("(dropsite-min-distance wood > 5)", Condition, name="c_far_wood")
    pset.addTerminal("(dropsite-min-distance gold > 5)", Condition, name="c_far_gold")
    pset.addTerminal("(dropsite-min-distance stone > 5)", Condition, name="c_far_stone")

    pset.addTerminal("(unit-type-count villager < 30)", Condition, name="c_vills_under_30")
    pset.addTerminal("(unit-type-count villager < 60)", Condition, name="c_vills_under_60")
    pset.addTerminal("(unit-type-count villager < 100)", Condition, name="c_vills_under_100")
    pset.addTerminal("(idle-farm-count < 2)", Condition, name="c_need_farms")

    pset.addTerminal("(train villager)", Action, name="a_train_vill")
    pset.addTerminal("(build farm)", Action, name="a_build_farm")

    techs = [
        ("ri-loom", "loom"), ("ri-wheel-barrow", "wheel_barrow"), ("ri-hand-cart", "hand_cart"),
        ("ri-double-bit-axe", "axe_1"), ("ri-bow-saw", "axe_2"), ("ri-two-man-saw", "axe_3"),
        ("ri-horse-collar", "farm_1"), ("ri-heavy-plow", "farm_2"), ("ri-crop-rotation", "farm_3"),
        ("ri-gold-mining", "gold_1"), ("ri-gold-shaft-mining", "gold_2"),
        ("ri-stone-mining", "stone_1"), ("ri-stone-shaft-mining", "stone_2"),
        ("ri-sanctity", "sanctity"), ("ri-fervor", "fervor"), ("ri-atonement", "atonement"),
        ("ri-heresy", "heresy"), ("ri-block-printing", "block_print"), ("ri-theocracy", "theocracy")
    ]
    for tech, name in techs:
        pset.addTerminal(f"(can-research {tech})", Condition, name=f"c_can_res_{name}")
        pset.addTerminal(f"(research {tech})", Action, name=f"a_res_{name}")

    ages = ["dark-age", "feudal-age", "castle-age", "imperial-age"]
    for age in ages:
        pset.addTerminal(f"(current-age == {age})", Condition, name=f"c_is_{age.replace('-', '_')}")
        if age != "dark-age":
            pset.addTerminal(f"(can-research {age})", Condition, name=f"c_can_go_{age.replace('-', '_')}")
            pset.addTerminal(f"(research {age})", Action, name=f"a_go_{age.replace('-', '_')}")

    add_military_nodes(pset, Condition, Action)
    add_tactics_nodes(pset, Condition, Action)

    return pset