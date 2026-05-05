import os
import random

# ==========================================
# 1. KONFIGURACJA ŚRODOWISKA
# ==========================================
# Ścieżka do folderu z AI w Twojej grze (zmień ukośniki na podwójne backslashe w Windowsie)
AOE2_AI_FOLDER = "D:\\Steam\\steamapps\\common\\AoE2DE\\resources\\_common\\ai"

POPULATION_SIZE = 5
GENERATION = 1


# ==========================================
# 2. DEFINICJA SZABLONU PLIKU .PER (TEMPLATE)
# ==========================================
# Używamy formatowania f-string, aby Python mógł wstrzykiwać geny prosto w kod bota!
def generate_per_content(genes):
    food_percent = 100 - genes['wood_percent']

    return f"""; ========================================================
; MILI-BOT (Evolved Generation)
; Genom: {genes}
; ========================================================

(defrule
    (true)
=>
    (set-strategic-number sn-number-explore-groups 1)
    (set-strategic-number sn-total-number-explorers 1)
    (set-strategic-number sn-cap-civilian-explorers 0)

    ; WSTRZYKNIĘTE GENY PRZESTRZENNE:
    (set-strategic-number sn-maximum-town-size {genes['town_size']})
    (set-strategic-number sn-maximum-food-drop-distance {genes['food_drop_distance']})
    (set-strategic-number sn-mill-max-distance {genes['mill_distance']})

    ; WSTRZYKNIĘTE GENY GOSPODARCZE:
    (set-strategic-number sn-wood-gatherer-percentage {genes['wood_percent']})
    (set-strategic-number sn-food-gatherer-percentage {food_percent})
    (set-strategic-number sn-gold-gatherer-percentage 0)
    (set-strategic-number sn-stone-gatherer-percentage 0)

    (disable-self)
)

(defrule
    (can-train villager)
    (unit-type-count-total villager < 30)
=>
    (train villager)
)

(defrule
    (can-build house)
    (housing-headroom < 4)
    (up-pending-objects c: house == 0)
=>
    (build house)
)

(defrule
    (current-age == dark-age)
    (building-type-count-total lumber-camp == 0)
    (can-build lumber-camp)
=>
    (build lumber-camp)
    (disable-self)
)

(defrule
    (current-age == dark-age)
    (building-type-count-total lumber-camp >= 1)
    (building-type-count-total mill == 0)
    (can-build mill)
=>
    (build mill)
    (disable-self)
)
"""


def generate_ai_file_content(bot_name):
    """Tworzy prosty plik deklaracyjny .ai ładujący mózg .per"""
    return f'(load "{bot_name}")\n'


# ==========================================
# 3. SILNIK GENERUJĄCY POPULACJĘ (DNA)
# ==========================================
def create_random_genome():
    """Generuje w pełni losowy zestaw genów dla nowego bota."""
    return {
        'town_size': random.randint(20, 50),
        'wood_percent': random.randint(10, 40),
        'food_drop_distance': random.randint(5, 25),
        'mill_distance': random.randint(10, 30)
    }


def deploy_bots_to_game(population_genomes, gen_number):
    """Tworzy pliki .per i .ai we właściwym folderze gry."""
    print(f"[*] Wdrażanie Generacji {gen_number} do Age of Empires 2...")

    for idx, genome in enumerate(population_genomes):
        bot_name = f"Milibot_G{gen_number}_V{idx + 1}"
        per_path = os.path.join(AOE2_AI_FOLDER, f"{bot_name}.per")
        ai_path = os.path.join(AOE2_AI_FOLDER, f"{bot_name}.ai")

        # 1. Zapis pliku Mózgu (.per)
        with open(per_path, "w") as f:
            f.write(generate_per_content(genome))

        # 2. Zapis pliku Deklaracyjnego (.ai)
        with open(ai_path, "w") as f:
            f.write(generate_ai_file_content(bot_name))

        print(f"  -> Zbudowano: {bot_name} | Geny: {genome}")


# ==========================================
# 4. GŁÓWNA PĘTLA PROGRAMU
# ==========================================
if __name__ == "__main__":
    print("===========================================")
    print(" MILI-BOT EVOLUTION MANAGER v1.0")
    print("===========================================")

    # Krok 1: Inicjalizacja pierwszej, losowej populacji
    population = [create_random_genome() for _ in range(POPULATION_SIZE)]

    # Krok 2: Kompilacja i wysłanie do folderu Steama
    try:
        deploy_bots_to_game(population, GENERATION)
        print("\n[SUKCES] Boty czekają w grze na przetestowanie!")
        print(
            "Kolejny krok (w pełnej automatyzacji): Uruchomienie gry z wiersza poleceń i parsowanie logów .aoe2record")
    except Exception as e:
        print(
            f"\n[BŁĄD] Nie udało się zapisać plików w folderze gry. Czy ścieżka AOE2_AI_FOLDER jest poprawna? Błąd: {e}")