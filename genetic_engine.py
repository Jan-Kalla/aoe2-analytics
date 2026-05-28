import random
from deap import base, creator, tools, gp
from economy_primitives import get_economy_pset
from config import MUTATION_RATE

# ==========================================
# 1. INICJALIZACJA DEAP I TYPÓW AST
# ==========================================
pset = get_economy_pset()

# Zabezpieczenie przed wielokrotnym tworzeniem klas przez DEAP
if not hasattr(creator, "FitnessMax"):
    # Maksymalizujemy fitness (będziemy do niego przekazywać wynik z gry minus kara za rozmiar)
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if not hasattr(creator, "Individual"):
    # Osobnik to teraz matematyczne drzewo!
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Ograniczamy głębokość początkowego drzewa (żeby na starcie pliki nie miały miliona linijek)
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=2, max_=5)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

# ==========================================
# 2. NARZĘDZIA CHIRURGICZNE (Mutacje AST)
# ==========================================
# Selekcja do turniejów dla Mutacji i Krzyżowania
toolbox.register("select", tools.selTournament, tournsize=3)

# Transplantacja gałęzi między dwoma botami
toolbox.register("mate", gp.cxOnePoint)

# Mutacje
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutUniform", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)
toolbox.register("mutShrink", gp.mutShrink)
toolbox.register("mutNodeReplacement", gp.mutNodeReplacement, pset=pset)


# ==========================================
# 3. GŁÓWNA PĘTLA EWOLUCYJNA
# ==========================================
# ==========================================
# [NOWE] AUTORSKA MUTACJA WIELOPUNKTOWA
# ==========================================
def mut_dynamic_coverage(individual, pset_ref, max_percent=0.05):  # <-- Tutaj prawilny snake_case (PEP 8)
    """
    Losowo mutuje od 0% do max_percent wszystkich węzłów w drzewie bota.
    Zastępuje statyczną, jednowęzłową mutację DEAP.
    """
    size = len(individual)

    # Losujemy procent pokrycia mutacją (od 0.0 do np. 0.05)
    coverage = random.uniform(0.0, max_percent)

    # Obliczamy ile to fizycznie węzłów (np. 500 * 0.04 = 20 mutacji)
    num_mutations = int(size * coverage)

    # Wykonujemy standardową mutację DEAP wielokrotnie w pętli
    for _ in range(num_mutations):
        individual, = gp.mutNodeReplacement(individual, pset=pset_ref)

    return individual,


# Rejestrujemy naszą nową funkcję w narzędziach (przekazując słownik pset)
toolbox.register("mutDynamicCoverage", mut_dynamic_coverage, pset_ref=pset)

def build_next_generation(scored_population, elite_count=12, crossover_count=52, mutant_count=32):
    """
    scored_population: lista krotek (punkty, genom_AST, ID) posortowana malejąco!
    Wszystkie operacje genetyczne wykonujemy bezpośrednio na kodzie Lisp.
    """
    next_gen = []

    # Wyciągamy same drzewa (osobniki), odrzucając punkty i ID
    individuals = [ind for (score, ind, worker_id) in scored_population]

    # ==========================================
    # [NOWE] TWARDA SELEKCJA ODCIĘCIA (Truncation)
    # ==========================================
    # Odcinamy 1/3 najsłabszych botów. Do reprodukcji dopuszczamy tylko top 66%.
    rozmiar_puli = int(len(individuals) * (2 / 3))
    mating_pool = individuals[:rozmiar_puli]

    # --- GRUPA 1: ELITA (Kopiowanie 1:1) ---
    # Elita musi zostać, to absolutni mistrzowie obecnej generacji
    for i in range(elite_count):
        elite_clone = toolbox.clone(individuals[i])
        next_gen.append(elite_clone)

    # --- GRUPA 2: LEKKIE MUTACJE (Krzyżowanie + Dynamiczna Mutacja Wielopunktowa) ---
    for _ in range(crossover_count // 2):
        # Losujemy rodziców metodą turniejową z bezpiecznej puli
        parent1 = toolbox.clone(toolbox.select(mating_pool, 1)[0])
        parent2 = toolbox.clone(toolbox.select(mating_pool, 1)[0])

        # 1. KRZYŻOWANIE (Wymiana głównych gałęzi)
        child1, child2 = toolbox.mate(parent1, parent2)

        # 2. DYNAMICZNA MUTACJA (Od 0% do 5% węzłów całego drzewa)
        # Każde dziecko losuje swój własny stopień mutacji z zachowaniem górnego limitu (max 5%)
        child1, = toolbox.mutDynamicCoverage(child1, max_percent=0.05)
        child2, = toolbox.mutDynamicCoverage(child2, max_percent=0.05)

        next_gen.append(child1)
        next_gen.append(child2)

    # --- GRUPA 3: CIĘŻKIE MUTACJE (Mutacje Strukturalne) ---
    for _ in range(mutant_count):
        # [ZMIANA] Bazy do mutacji szukamy tylko w bezpiecznej puli mating_pool
        mutant = toolbox.clone(toolbox.select(mating_pool, 1)[0])

        # Rzut kostką - jak uderzy mutacja?
        choice = random.random()
        if choice < 0.4:
            # 40% szans na wklejenie zupełnie nowej logiki (Uniform)
            mutant, = toolbox.mutUniform(mutant)
        elif choice < 0.7:
            # 30% szans na usunięcie losowej gałęzi (Odchudzanie/Shrink)
            mutant, = toolbox.mutShrink(mutant)
        else:
            # 30% szans na podmianę konkretnego węzła (NodeReplacement)
            mutant, = toolbox.mutNodeReplacement(mutant)

        next_gen.append(mutant)

    # GRUPA 4 (Świeża Krew) została usunięta, aby nie psuć DNA wysoce rozwiniętych botów.

    # Bezpiecznik (gdyby pojawiły się luki w liście przez błędy zaokrągleń)
    while len(next_gen) < (elite_count + crossover_count + mutant_count):
        # Jeśli brakuje bota, zapychamy lukę bezpiecznym klonem wylosowanym z dobrej puli
        next_gen.append(toolbox.clone(random.choice(mating_pool)))

    return next_gen


# ==========================================
# 4. FUNKCJE WSPOMAGAJĄCE DLA main.py
# ==========================================
def create_initial_population(size=96):
    """Tworzy pierwszą generację botów (Drzewa AST)"""
    return toolbox.population(n=size)


def generate_per_file_content(individual):
    """
    Kompiluje drzewo AST do tekstu Lisp omijając limit zagnieżdżeń Pythona.
    Używa oficjalnego słownika DEAP (pset.context), wiernie symulując eval().
    """
    stack = []

    for node in reversed(individual):
        if node.arity == 0:
            # KRYTYCZNA POPRAWKA: Pytamy oficjalny słownik, tak jak robi to eval().
            # Gwarantuje to poprawne tłumaczenie (np. c_few_watch_tower -> (unit-type-count...))
            if node.name in pset.context:
                stack.append(str(pset.context[node.name]))
            else:
                # Jeśli węzła nie ma w słowniku, jest to wylosowana liczba (ERC)
                stack.append(str(node.value))
        else:
            # Dla funkcji logicznych (DEFRULE, MANY_RULES, itp.) pobieramy zmontowane argumenty ze stosu
            args = [stack.pop() for _ in range(node.arity)]
            func = pset.context[node.name]
            stack.append(str(func(*args)))

    return stack[0]