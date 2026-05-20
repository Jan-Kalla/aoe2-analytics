import os
import time
import csv
import random

import shutil

from config import *
from genetic_engine import (
    create_initial_population,
    build_next_generation,
    generate_per_file_content
)
from simulation_runner import run_match_and_evaluate_parallel


def deploy_population_to_workers(population):
    """
    Automatycznie rozdziela 96 osobników (drzewa AST) pomiędzy 12 niezależnych workerów.
    Każdy worker otrzymuje paczkę 8 botów skompilowanych do formatu gry (.per/.ai).
    """

    for w in range(1, NUM_WORKERS + 1):
        worker_dir = os.path.join(WORKERS_DIR, f"Worker_{w}")


        # Lokalizacje docelowe wymagane przez architekturę UserPatch 1.5 dla każdego workera
        folders_to_seed = [
            os.path.join(worker_dir, "AI"),
            os.path.join(worker_dir, "Age2_x1", "Script.AI"),
            os.path.join(worker_dir, "Games", "WololoKingdoms", "Script.AI")
        ]

        # Upewniamy się, że struktura folderów na skrypty istnieje
        for fld in folders_to_seed:
            os.makedirs(fld, exist_ok=True)

        for local_id in range(1, BOTS_PER_MATCH + 1):
            # Obliczamy globalny indeks na podstawie zmiennych z configu
            global_idx = (w - 1) * BOTS_PER_MATCH + (local_id - 1)
            individual = population[global_idx]

            # Kompilacja drzewa AST bezpośrednio do czystego kodu tekstowego Lisp
            lisp_code = generate_per_file_content(individual)

            # Zabezpieczenie przed "pustym plikiem" z samymi komentarzami
            dummy_rule = "\n\n; Zabezpieczenie AST (Gwarancja 1 reguły)\n(defrule\n    (true)\n=>\n    (do-nothing)\n)\n"

            # [NOWE] Samowystarczalny blok stałych UserPatch 1.5 (Brak zależności od plików zewnętrznych!)
            up_constants = (
                "; --- Wbudowane stale UP 1.5 (zastepuje brakujacy plik UserPatchConst.per) ---\n"
                "(defconst sn-placement-zone 288)\n"
                "(defconst sn-allow-adjacent-dropsites 290)\n"
                "(defconst place-forward 1)\n"
                "(defconst action-default 0)\n"
                "(defconst archery-class 900)\n"
                "(defconst infantry-class 906)\n"
                "(defconst siege-weapon-class 927)\n"
            )

            # [NOWE] Ładowanie oficjalnego słownika stałych UserPatch na samej górze pliku bota
            bot_content = f"; Genetyczny Barbarian GP | Global ID: {global_idx}\n(load \"UserPatchConst\")\n" + lisp_code + dummy_rule

            # Zrzucamy wygenerowany kod na twardy dysk do struktur odpowiedniego workera
            for fld in folders_to_seed:
                per_path = os.path.join(fld, f"Milibot_Evo_{local_id}.per")
                ai_path = os.path.join(fld, f"Milibot_Evo_{local_id}.ai")

                with open(per_path, "w", encoding="utf-8") as f:
                    f.write(bot_content)
                with open(ai_path, "w", encoding="utf-8") as f:
                    f.write(f'(load "Milibot_Evo_{local_id}")\n')


def main():
    # Liczymy wielkość populacji dynamicznie, by zawsze pasowała do klastra!
    POPULATION_SIZE = NUM_WORKERS * BOTS_PER_MATCH

    print("[*] Inicjalizacja zaawansowanego klastra Programowania Genetycznego (DEAP)...")

    # =====================================================
    # ZARZĄDZANIE PLIKIEM CSV (Backup / Nadpisywanie / Kontynuacja)
    # =====================================================
    if os.path.exists(CSV_FILENAME):
        print(f"\n[!] Wykryto istniejący plik ewolucji: {CSV_FILENAME}")
        wybor = input("    Wybierz akcję: [B]ackup i nowy plik | [N]adpisz | [K]ontynuuj stary: ").strip().upper()

        if wybor == 'B':
            backup_name = f"backup_{int(time.time())}_{CSV_FILENAME}"
            os.rename(CSV_FILENAME, backup_name)
            print(f"    [*] Stary plik zabezpieczony jako: {backup_name}")

            # Tworzymy nowy z nagłówkami
            with open(CSV_FILENAME, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Generacja", "Bot_ID", "Punkty", "AST_Tree"])

        elif wybor == 'N':
            print("    [*] UWAGA: Stary plik zostanie wyczyszczony i nadpisany!")
            with open(CSV_FILENAME, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Generacja", "Bot_ID", "Punkty", "AST_Tree"])

        else:
            print("    [*] Kontynuacja zapisu do istniejącego pliku.")
    else:
        # Plik nie istnieje, tworzymy od zera
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Generacja", "Bot_ID", "Punkty", "AST_Tree"])

    # Generowanie początkowej, losowej populacji drzew logicznych ze słownika klocków
    population = create_initial_population(POPULATION_SIZE)
    current_gen = 1

    while True:
        print(f"\n=================== ROZPOCZYNAM GENERACJĘ {current_gen} ===================")

        # 1. Kompilacja i fizyczne wstrzyknięcie kodu do folderów gry
        print("[*] Generowanie kodu źródłowego Lisp i dystrybucja do workerów...")
        deploy_population_to_workers(population)

        # 2. Uruchomienie 12 instancji w trybie przyspieszonym headless i zebranie surowych wyników z RAM
        print(f"[*] Uruchamiam 12 równoległych symulacji dla pokolenia {current_gen}...")
        raw_scores = run_match_and_evaluate_parallel(NUM_WORKERS)

        # 3. Ewaluacja i przypisywanie ocen (Fitness) osobnikom w strukturach DEAP
        scored_population = []
        for global_id in range(POPULATION_SIZE):
            score = raw_scores[global_id]
            individual = population[global_id]

            # DEAP wymaga, aby fitness był przypisany jako krotka (tuple)
            individual.fitness.values = (float(score),)
            scored_population.append((score, individual, global_id))

        # Sortowanie populacji od najlepszego do najgorszego bota
        scored_population.sort(key=lambda x: x[0], reverse=True)

        # 4. Archiwizacja wyników generacji do bazy danych CSV
        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for score, individual, global_id in scored_population:
                # Zapisujemy epokę, ID bota, punkty oraz pełny zrzut struktury drzewa jako tekst
                writer.writerow([current_gen, global_id, score, str(individual)])

        # 5. Wyświetlenie aktualnej czołówki ewolucyjnej w konsoli
        print(f"\n--- TOP WYNIKI GENERACJI {current_gen} ---")
        for rank, (score, individual, global_id) in enumerate(scored_population[:4]):
            # Pokazujemy tylko wycinek drzewa w konsoli, by nie zasypać ekranu tysiącem klocków
            tree_preview = str(individual)[:80] + "..." if len(str(individual)) > 80 else str(individual)
            print(f" #{rank + 1}: Bot {global_id} (Wynik: {score}) -> Układ AST: {tree_preview}")

        # 6. Przejście do procedury tworzenia nowego pokolenia (Elita, Crossover, Mutacje, Krew)
        print("[*] Przetwarzanie operatorów genetycznych dla nowego pokolenia...")
        population = build_next_generation(scored_population)
        current_gen += 1


if __name__ == "__main__":
    main()