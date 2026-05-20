import random
from deap import base, creator, tools, gp
from economy_primitives import get_economy_pset

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
# 3. GŁÓWNA PĘTLA EWOLUCYJNA (Twój autorski system)
# ==========================================
def build_next_generation(scored_population, elite_count=6, crossover_count=48, mutant_count=30, random_count=12):
    """
    scored_population: lista krotek (punkty, genom_AST, ID) posortowana malejąco!
    Wszystkie operacje genetyczne wykonujemy bezpośrednio na kodzie Lisp.
    """
    next_gen = []

    # Wyciągamy same drzewa (osobniki), odrzucając punkty i ID
    individuals = [ind for (score, ind, worker_id) in scored_population]

    # --- GRUPA 1: ELITA (Kopiowanie 1:1) ---
    for i in range(elite_count):
        elite_clone = toolbox.clone(individuals[i])
        next_gen.append(elite_clone)

    # --- GRUPA 2: LEKKIE MUTACJE (Krzyżowanie/Transplantacja) ---
    # Dzielimy przez 2, bo skrzyżowanie 2 rodziców daje 2 dzieci
    for _ in range(crossover_count // 2):
        # Losujemy 2 dobrych rodziców metodą turniejową
        parent1 = toolbox.clone(toolbox.select(individuals, 1)[0])
        parent2 = toolbox.clone(toolbox.select(individuals, 1)[0])

        child1, child2 = toolbox.mate(parent1, parent2)
        next_gen.append(child1)
        next_gen.append(child2)

    # --- GRUPA 3: CIĘŻKIE MUTACJE (Mutacje Strukturalne) ---
    for _ in range(mutant_count):
        mutant = toolbox.clone(toolbox.select(individuals, 1)[0])

        # Rzut kostką - jak uderzy mutacja?
        choice = random.random()
        if choice < 0.4:
            # 40% szans na wklejenie zupełnie nowej logiki (Uniform)
            mutant, = toolbox.mutUniform(mutant)
        elif choice < 0.7:
            # 30% szans na usunięcie losowej gałęzi (Odchudzanie/Shrink)
            mutant, = toolbox.mutShrink(mutant)
        else:
            # 30% szans na odcięcie głowy i zrobienie korzenia z głębokiej reguły (Hoist)
            mutant, = toolbox.mutNodeReplacement(mutant)

        next_gen.append(mutant)

    # --- GRUPA 4: ŚWIEŻA KREW (Kompletnie od zera) ---
    for _ in range(random_count):
        fresh_bot = toolbox.individual()
        next_gen.append(fresh_bot)

    # Bezpiecznik (gdyby pojawiły się różnice parzyste)
    while len(next_gen) < (elite_count + crossover_count + mutant_count + random_count):
        next_gen.append(toolbox.individual())

    return next_gen


# ==========================================
# 4. FUNKCJE WSPOMAGAJĄCE DLA main.py
# ==========================================
def create_initial_population(size=96):
    """Tworzy pierwszą generację botów (Drzewa AST)"""
    return toolbox.population(n=size)


def generate_per_file_content(individual):
    """Kompiluje matematyczne drzewo AST do czystego tekstu w formacie Lisp (.per)"""
    # Rozwiązujemy drzewo AST bezpośrednio do stringa za pomocą kontekstu klocków
    lisp_code = eval(str(individual), pset.context)
    return lisp_code