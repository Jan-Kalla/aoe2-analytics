import random
from deap import base, creator, tools, gp


# ==========================================
# 1. DEFINICJA TYPÓW (Kształty klocków Lego)
# ==========================================
# Zabezpieczają nas przed błędem składni Lisp.
class Condition: pass


class Action: pass


class Rule: pass


# ==========================================
# 2. BAZA KLOCKÓW (Primitive Set)
# ==========================================
# Inicjujemy drzewo, którego "korzeniem" musi być gotowa reguła (Rule)
pset = gp.PrimitiveSetTyped("MAIN", [], Rule)


# --- A. Klocki łączące warunki (Operatory Logiczne) ---
def and_cond(cond1, cond2):
    # W silniku Lisp zapisanie dwóch warunków pod sobą to domyślne AND
    return f"{cond1}\n    {cond2}"


def or_cond(cond1, cond2):
    return f"(or {cond1}\n        {cond2})"


pset.addPrimitive(and_cond, [Condition, Condition], Condition, name="AND")
pset.addPrimitive(or_cond, [Condition, Condition], Condition, name="OR")


# --- B. Klocki łączące akcje ---
def double_action(act1, act2):
    return f"{act1}\n    {act2}"


pset.addPrimitive(double_action, [Action, Action], Action, name="DO_BOTH")


# --- C. Główny łącznik (Sklejanie reguły) ---
def make_rule(condition, action):
    return f"(defrule\n    {condition}\n=>\n    {action}\n)"


pset.addPrimitive(make_rule, [Condition, Action], Rule, name="DEFRULE")

# ==========================================
# 3. TERMINALE (Liście drzewa - konkretne instrukcje gry)
# ==========================================
# Możemy ich w przyszłości dodać setki!

# -- Warunki (Fakty z gry) --
pset.addTerminal("(wood-amount > 100)", Condition, name="c_wood100")
pset.addTerminal("(food-amount > 50)", Condition, name="c_food50")
pset.addTerminal("(current-age == dark-age)", Condition, name="c_darkage")
pset.addTerminal("(unit-type-count villager < 10)", Condition, name="c_vill_under_10")
pset.addTerminal("(building-type-count-total house < 3)", Condition, name="c_need_house")

# -- Akcje (Co ma zrobić bot) --
pset.addTerminal("(build house)", Action, name="a_build_house")
pset.addTerminal("(build mill)", Action, name="a_build_mill")
pset.addTerminal("(research ri-loom)", Action, name="a_loom")
pset.addTerminal("(train villager)", Action, name="a_train_vill")

# ==========================================
# 4. KONFIGURACJA SILNIKA DEAP
# ==========================================
# Tworzymy typ osobnika (drzewo genetyczne) i jego fitness
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
# Losujemy drzewo o głębokości od 1 do 3 poziomów logiki
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("compile", gp.compile, pset=pset)

# ==========================================
# 5. GENEROWANIE I ODCZYT
# ==========================================
if __name__ == "__main__":
    print("--- LOSOWANIE 3 UNIKALNYCH REGUŁ ZMUTOWANEGO BOTA ---")

    for i in range(3):
        # 1. Losujemy genom osobnika (drzewo AST)
        ind = toolbox.individual()

        # Rozwiązujemy drzewo AST bezpośrednio do stringa za pomocą słownika DEAP
        lisp_code = eval(str(ind), pset.context)

        print(f"\n[Mutacja {i + 1}]: Reprezentacja matematyczna (AST):")
        print(ind)
        print("\nGotowy kod .per wstrzykiwany do gry:")
        print(lisp_code)
        print("-" * 40)