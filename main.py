import os
import time
import csv
import random
import shutil

from deap import creator, gp
from config import *
from genetic_engine import (
    create_initial_population,
    build_next_generation,
    generate_per_file_content,
    pset  # Wymagane do tłumaczenia tekstu CSV z powrotem na drzewa
)
from simulation_runner import run_match_and_evaluate_parallel

# ==========================================
# DYNAMICZNE WYLICZENIE POPULACJI
# ==========================================
POPULATION_SIZE = NUM_WORKERS * BOTS_PER_MATCH


def deploy_population_to_workers(population):
    for w in range(1, NUM_WORKERS + 1):
        worker_dir = os.path.join(WORKERS_DIR, f"Worker_{w}")

        folders_to_seed = [
            os.path.join(worker_dir, "AI"),
            os.path.join(worker_dir, "Age2_x1", "Script.AI"),
            os.path.join(worker_dir, "Games", "WololoKingdoms", "Script.AI")
        ]

        for fld in folders_to_seed:
            os.makedirs(fld, exist_ok=True)

        for slot in range(1, BOTS_PER_MATCH + 1):
            global_idx = (w - 1) * BOTS_PER_MATCH + (slot - 1)
            individual = population[global_idx]

            # Skompilowane drzewo AST bota
            lisp_code = generate_per_file_content(individual)

            # [NAPRAWIONE] Zabezpieczenie AST - jedyna rzecz, która zepsuła dzisiejszą symulację
            dummy_rule = "\n\n; Zabezpieczenie AST (Gwarancja 1 reguły)\n(defrule\n    (true)\n=>\n    (do-nothing)\n)\n"

            # [ZOSTAWIONE] Stabilny blok stałych z wczoraj (Skoro działał i dawał 2400 pkt, to go nie tykamy!)
            up_constants = (
                "; --- Wbudowane stale UP 1.5 ---\n"
                "(defconst sn-placement-zone 288)\n"
                "(defconst sn-allow-adjacent-dropsites 290)\n"
                "(defconst place-forward 1)\n"
                "(defconst action-default 0)\n"
                "(defconst archery-class 900)\n"
                "(defconst infantry-class 906)\n"
                "(defconst siege-weapon-class 927)\n"
            )

            bot_content = f"; Genetyczny Barbarian GP | Global ID: {global_idx}\n" + up_constants + lisp_code + dummy_rule

            for fld in folders_to_seed:
                per_path = os.path.join(fld, f"Milibot_Evo_{slot}.per")
                with open(per_path, "w") as f:
                    f.write(bot_content)


def main():
    print("==================================================")
    print("   GENETYCZNY ENGINE AI - AGE OF EMPIRES II       ")
    print("==================================================")

    akcja = input("Wybierz akcję: [B]ackup i nowy plik | [N]adpisz | [K]ontynuuj stary: ").strip().upper()

    population = []
    current_gen = 1

    # ==========================================
    # WSKRZESZANIE DANYCH Z PLIKU CSV
    # ==========================================
    if akcja == 'K':
        print("[*] Próba odzyskania drzew genetycznych z pliku CSV...")
        try:
            with open(CSV_FILENAME, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                wiersze = list(reader)

                if wiersze:
                    current_gen = max([int(w[0]) for w in wiersze])
                    ostatnia_populacja = [w for w in wiersze if int(w[0]) == current_gen]

                    print(f"[*] Odtwarzanie Generacji {current_gen} z pliku CSV ({len(ostatnia_populacja)} botów)...")

                    odtworzona_oceniona_populacja = []
                    for w in ostatnia_populacja:
                        bot_id = int(w[1])
                        punkty = float(w[2])
                        drzewo_str = w[3]

                        drzewo_obj = gp.PrimitiveTree.from_string(drzewo_str, pset)
                        osobnik = creator.Individual(drzewo_obj)
                        osobnik.fitness.values = (punkty,)

                        odtworzona_oceniona_populacja.append((punkty, osobnik, bot_id))

                    print("[*] Generowanie nowych krzyżówek na bazie wskrzeszonej populacji...")
                    population = build_next_generation(odtworzona_oceniona_populacja)
                    current_gen += 1
        except Exception as e:
            print(f"[!] Błąd odczytu CSV, tworzę nową populację od zera. Błąd: {e}")
            population = create_initial_population(POPULATION_SIZE)
    else:
        population = create_initial_population(POPULATION_SIZE)

    # ==========================================
    # GŁÓWNA PĘTLA SYMULACJI
    # ==========================================
    while True:
        print(f"\n=================== ROZPOCZYNAM GENERACJĘ {current_gen} ===================")

        print("[*] Generowanie kodu źródłowego Lisp i dystrybucja do workerów...")
        deploy_population_to_workers(population)

        print(f"[*] Uruchamiam równoległe symulacje dla pokolenia {current_gen}...")
        raw_scores = run_match_and_evaluate_parallel(NUM_WORKERS)

        scored_population = []
        for global_id in range(POPULATION_SIZE):
            # Rozpakowujemy krotkę z Twojej zmiennej
            wynik_ogolny, wynik_wojskowy = raw_scores[global_id]
            individual = population[global_id]

            wzrost_za_agresje = float(wynik_wojskowy) * 2.0
            total_raw_score = float(wynik_ogolny) + wzrost_za_agresje

            # ==========================================
            # ZAAWANSOWANA PRESJA PARSYMONII (Kara Wykładnicza)
            # ==========================================
            wysokosc_drzewa = individual.height
            max_wysokosc = 300.0  # Limit nałożony w genetic_engine.py

            # Ustalamy, w jakiej ćwiartce limitu znajduje się bot
            ratio = max(0.0, min(wysokosc_drzewa / max_wysokosc, 1.0))

            # Płynne skalowanie kary wewnątrz zmodyfikowanych przedziałów
            if ratio <= 0.25:
                # 0% do 25% głębokości (Rozpiętość: 0.25) -> Kara 0%
                procent_kary = (ratio / 0.25) * 0.00
            elif ratio <= 0.75:
                # 25% do 75% głębokości (Rozpiętość: 0.5) -> Kara od 0% do 1%
                procent_kary = 0.00 + ((ratio - 0.50) / 0.50) * 0.01
            elif ratio <= 0.90:
                # 75% do 90% głębokości (Rozpiętość: 0.15) -> Kara od 1% do 5%
                procent_kary = 0.01 + ((ratio - 0.75) / 0.15) * 0.04
            else:
                # Powyżej 90% głębokości (Rozpiętość: 0.10) -> Brutalna kara od 5% do 80%
                procent_kary = 0.05 + ((ratio - 0.90) / 0.10) * 0.75

            kara_wysokosci = raw_score * procent_kary

            # ==========================================
            # PRESJA PARSYMONII: 2. NOWA KARA ZA SZEROKOŚĆ (Podatek od genów)
            # ==========================================
            ilosc_wezlow = len(individual)

            # Parametr do tuningu: 0.5 punktu kary za KAŻDY element w kodzie bota
            mnoznik_podatku = 0.5
            koszt_metaboliczny = ilosc_wezlow * mnoznik_podatku

            final_score = max(0.0, raw_score - kara_wysokosci - koszt_metaboliczny)

            individual.fitness.values = (final_score,)
            scored_population.append((final_score, individual, global_id))

        scored_population.sort(key=lambda x: x[0], reverse=True)

        # Zapis do CSV
        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for score, individual, global_id in scored_population:
                writer.writerow([current_gen, global_id, score, str(individual)])

            # Zrzut bufora na dysk poza pętlą dla wydajności
            file.flush()
            os.fsync(file.fileno())

        print(f"\n--- TOP WYNIKI GENERACJI {current_gen} ---")
        for rank, (score, individual, global_id) in enumerate(scored_population[:4]):
            tree_preview = str(individual)[:80] + "..." if len(str(individual)) > 80 else str(individual)
            print(
                f" #{rank + 1}: Bot {global_id} (Wynik zredukowany: {score:.1f} pkt | Głębokość: {individual.height}) -> {tree_preview}")

        print("[*] Przetwarzanie operatorów genetycznych dla nowego pokolenia...")
        population = build_next_generation(scored_population)
        current_gen += 1


if __name__ == "__main__":
    main()