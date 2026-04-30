import random

# ==========================================
# 1. PARAMETRY GRY I SYMULATORA
# ==========================================
VILLAGER_CREATION_TIME = 25  # sekund
FOOD_GATHER_RATE = 0.33  # jedzenia na sekundę (owce)
WOOD_GATHER_RATE = 0.39  # drewna na sekundę

TARGET_VILLAGERS_TO_PRODUCE = 17  # 21 pop - 1 scout - 3 startowych
TARGET_FOOD = 500
TARGET_WOOD = 775

# Definicje Genów (Możliwe akcje do przypisania wieśniakowi)
GENE_FOOD = 0
GENE_WOOD = 1


# ==========================================
# 2. SYMULATOR DARK AGE (BARDZIEJ REALISTYCZNY)
# ==========================================
def simulate_build_order(build_order_genes):
    food = 200.0
    wood = 200.0

    vills_on_food = 3
    vills_on_wood = 0

    current_time = 0

    # KARY I OPÓŹNIENIA
    # Uznajemy, że jeśli jeszcze nikt nie poszedł na drewno, pierwszy drwal musi
    # dojść (np. 15s) i zbudować Lumber Camp (35s).
    lumber_camp_built = False
    time_until_lumber_camp_ready = 0

    for gene in build_order_genes:
        # Czas potrzebny na stworzenie bieżącego wieśniaka. Pętla tickuje co sekundę.
        vill_production_progress = 0

        # 1. Czekamy, aż zbierze się 50 food
        while food < 50:
            current_time += 1
            food += vills_on_food * FOOD_GATHER_RATE

            # Drewno zbieramy tylko, jeśli obóz jest gotowy (uproszczenie)
            if lumber_camp_built:
                wood += vills_on_wood * WOOD_GATHER_RATE
            elif time_until_lumber_camp_ready > 0:
                time_until_lumber_camp_ready -= 1
                if time_until_lumber_camp_ready == 0:
                    lumber_camp_built = True

            if vills_on_food == 0 and food < 50:
                return 99999

        food -= 50

        # 2. Cykl 25 sekund produkcji
        while vill_production_progress < VILLAGER_CREATION_TIME:
            current_time += 1
            vill_production_progress += 1

            food += vills_on_food * FOOD_GATHER_RATE
            if lumber_camp_built:
                wood += vills_on_wood * WOOD_GATHER_RATE
            elif time_until_lumber_camp_ready > 0:
                time_until_lumber_camp_ready -= 1
                if time_until_lumber_camp_ready == 0:
                    lumber_camp_built = True

        # Wieśniak wychodzi. Gdzie idzie?
        if gene == GENE_FOOD:
            vills_on_food += 1
        elif gene == GENE_WOOD:
            if not lumber_camp_built and time_until_lumber_camp_ready == 0:
                # To pierwszy drwal! Wysłany, ale najpierw idzie budować (50 sekund marszu+budowy)
                time_until_lumber_camp_ready = 50
                # UWAGA: W naszym uproszczeniu odejmujemy drewno na ten obóz (-100) na koniec jako wymaganie
                # w TARGET_WOOD (żeby nie psuć matematyki wczesnego startu z domkami).

            vills_on_wood += 1

    # Po wyprodukowaniu, liczymy resztę
    time_for_food = max(0, (TARGET_FOOD - food) / (vills_on_food * FOOD_GATHER_RATE)) if vills_on_food > 0 else (
        99999 if food < TARGET_FOOD else 0)
    time_for_wood = max(0, (TARGET_WOOD - wood) / (vills_on_wood * WOOD_GATHER_RATE)) if vills_on_wood > 0 else (
        99999 if wood < TARGET_WOOD else 0)

    additional_time = max(time_for_food, time_for_wood)
    current_time += additional_time

    final_food = food + (vills_on_food * FOOD_GATHER_RATE) * additional_time
    final_wood = wood + (vills_on_wood * WOOD_GATHER_RATE) * additional_time

    # Tu podkręcamy karę za marnotrawstwo.
    # Jeśli algorytm zebrał np. 150 drewna ZA DUŻO, mnożymy to razy dużą wagę, by go brutalnie skarcić.
    wasted_food = final_food - TARGET_FOOD
    wasted_wood = final_wood - TARGET_WOOD
    penalty = (wasted_food + wasted_wood) * 1.5

    return current_time + penalty


# ==========================================
# 4. SILNIK ALGORYTMU GENETYCZNEGO
# ==========================================

POPULATION_SIZE = 200  # Ilu "wirtualnych graczy" trenuje jednocześnie w jednym pokoleniu
GENERATIONS = 100  # Ile pokoleń (generacji) przeprowadzimy
MUTATION_RATE = 0.05  # Szansa (5%) na to, że pojedynczy rozkaz zmutuje (błąd przy klikaniu, odkrycie nowej drogi)


def create_initial_population(size):
    """Tworzy pierwszą, całkowicie losową populację Build Orderów."""
    population = []
    for _ in range(size):
        chromosome = [random.choice([GENE_FOOD, GENE_WOOD]) for _ in range(TARGET_VILLAGERS_TO_PRODUCE)]
        population.append(chromosome)
    return population


def crossover(parent1, parent2):
    """Krzyżowanie dwóch strategii (wymiana genów). Przecinamy Build Ordery w losowym miejscu."""
    crossover_point = random.randint(1, TARGET_VILLAGERS_TO_PRODUCE - 1)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    return child1, child2



def mutate(chromosome):
    """Mutacja: losowa zmiana rozkazu (np. z FOOD na WOOD), by zapobiec stagnacji genetycznej."""
    for i in range(len(chromosome)):
        if random.random() < MUTATION_RATE:
            # Zamień gen na przeciwny
            chromosome[i] = GENE_WOOD if chromosome[i] == GENE_FOOD else GENE_FOOD
    return chromosome


def translate_build_order(genes):
    """Pomocnicza funkcja do ładnego wypisywania genów."""
    return ["FOOD" if g == GENE_FOOD else "WOOD" for g in genes]


# ==========================================
# 5. GŁÓWNA PĘTLA EWOLUCYJNA (TRENING)
# ==========================================
if __name__ == "__main__":
    print("[*] Inicjalizacja Algorytmu Genetycznego dla AoE2 (21-Pop Scout Rush)...")

    # 1. Stworzenie pierwszej, głupiej populacji (Pokolenie 0)
    population = create_initial_population(POPULATION_SIZE)

    best_time_overall = float('inf')
    best_bo_overall = []

    # 2. Start ewolucji przez 'N' pokoleń
    for generation in range(GENERATIONS):
        # Oceniamy każdego osobnika w populacji (uruchamiamy go w symulatorze)
        scored_population = []
        for build_order in population:
            time_score = simulate_build_order(build_order)
            scored_population.append((time_score, build_order))

        # Sortujemy po czasie (od najkrótszego - czyli najlepszego)
        scored_population.sort(key=lambda x: x[0])

        # Wyciągamy lidera aktualnego pokolenia
        best_time, best_bo = scored_population[0]

        if best_time < best_time_overall:
            best_time_overall = best_time
            best_bo_overall = best_bo.copy()

        # Logujemy postęp co 10 generacji (lub pierwszą i ostatnią)
        if generation % 10 == 0 or generation == GENERATIONS - 1:
            print(f"-> Generacja {generation:02d} | Najlepszy czas: {best_time} sek.")

        # ================= SELEKCJA I ROZMNAŻANIE =================
        next_generation = []

        # Elitaryzm (Elitism): Zachowujemy absolutną topkę (najlepsze 10%), bez zmian
        elite_count = int(POPULATION_SIZE * 0.1)
        elites = [ind[1] for ind in scored_population[:elite_count]]
        next_generation.extend(elites)

        # Wypełniamy resztę populacji "dziećmi" najlepszych osobników
        while len(next_generation) < POPULATION_SIZE:
            # Selekcja Turniejowa (Wybieramy losowo 2 pary i krzyżujemy ze sobą tych, co mieli lepsze czasy)
            parent1 = random.choice(scored_population[:int(POPULATION_SIZE / 2)])[1]
            parent2 = random.choice(scored_population[:int(POPULATION_SIZE / 2)])[1]

            child1, child2 = crossover(parent1, parent2)

            # Mutujemy dzieci
            child1 = mutate(child1)
            child2 = mutate(child2)

            next_generation.append(child1)
            if len(next_generation) < POPULATION_SIZE:
                next_generation.append(child2)

        # Zastępujemy starą populację nową, ulepszoną
        population = next_generation

    # Koniec ewolucji, pokazujemy wyniki mistrza!
    print("\n=========================================================")
    print("[SUKCES] Ewolucja Zakończona!")
    print(f"Najszybszy wyewoluowany czas: {best_time_overall} sekund")
    print(f"Czas w minutach gry: {best_time_overall / 60:.2f} min")
    print("Wyewoluowany optymalny Build Order (od 4-tego wieśniaka):")
    print(translate_build_order(best_bo_overall))
    print("=========================================================")