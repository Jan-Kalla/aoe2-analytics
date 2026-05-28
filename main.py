import os
import time
import csv
import random
import shutil
import re

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


def sanitize_bot_code(bot_code):
    """
    Ostateczny Auto-Balancer składni Lisp.
    Liczy otwarte i zamknięte nawiasy w całym pliku.
    Jeśli brakuje prawych nawiasów (częste przy ogromnych drzewach AST),
    dokleja je na końcu pliku, by zaspokoić parser AoE2.
    """
    code = str(bot_code)

    open_brackets = code.count('(')
    close_brackets = code.count(')')

    # Jeśli brakuje prawych nawiasów, doklejamy je na końcu pliku
    if open_brackets > close_brackets:
        missing = open_brackets - close_brackets
        code += "\n" + ")" * missing

    # Zabezpieczenie przed "gołymi" operatorami, które mogły przetrwać
    code = code.replace("=>\n    <\n", "=>\n    (do-nothing)\n")
    code = code.replace("=>\n    >\n", "=>\n    (do-nothing)\n")
    code = code.replace("=>\n    <=\n", "=>\n    (do-nothing)\n")
    code = code.replace("=>\n    >=\n", "=>\n    (do-nothing)\n")

    return code

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

            # [NOWE] Telemetria: Odporna na centralne logowanie (Zawiera SLOT ID)
            # [NOWE] Telemetria: Desynchronizacja I/O (Eliminacja zatorów na dysku)
            # [NOWE] Telemetria: Eksploracja i Klauzula Przetrwania
            # [NOWE] Wracamy do odpornej na SPAM telemetrii (Jednorazowe strzały za konkretne budynki z poprawnym tagiem %d)
            # [NOWE] Telemetria: Kuloodporne rejestry (400+) połączone z natywną, poprawną składnią Lisp
            # [NOWE] Telemetria: Poprawiona składnia %d (używamy g: zamiast c:) + Logika target-player!
            # [NOWE] Telemetria: Poprawiona składnia Lisp (g: zamiast c:), Akumulator Relikwii i Klasztor
            # [NOWE] Telemetria: Dodano chirurgiczny RESET wysokich rejestrów RAM (Eliminacja śmieci startowych!)
            # [NOWE] Telemetria: Kuloodporny RESET RAM-u przy użyciu komendy (disable-self) odpornej na lagi silnika!
            # [NOWE] Telemetria: Czysta architektura + Proste zliczanie sztuk relikwii (odporne na lagi)
            # [NOWE] Telemetria: Rozszerzony, odporny na lagi licznik dla dużych map (1 do 15 relikwii)
            # [NOWE] Telemetria: Czysta architektura (Tylko bezpieczne flagi, reset RAM za pomocą disable-self)
            telemetry_rule = f"""
                        ; --- MODUL TELEMETRII (100% KULOODPORNY) ---

                        ; BEZWZGLĘDNY RESET PAMIĘCI (Odporny na lagi startowe)
                        (defrule (true) => (set-goal 411 0) (set-goal 412 0) (set-goal 413 0) (set-goal 414 0) (set-goal 415 0) (set-goal 416 0) (disable-self))
                        (defrule (true) => (set-goal 417 0) (set-goal 450 0) (set-goal 451 0) (set-goal 452 0) (set-goal 454 0) (set-goal 455 0) (disable-self))
                        (defrule (true) => (set-goal 456 0) (set-goal 457 0) (set-goal 458 0) (disable-self))

                        ; Pobieranie faktów do wysokich rejestrów
                        (defrule (true) => (up-get-fact 31 0 401) (up-get-fact 19 0 402) (up-get-fact 17 0 403))

                        ; 1. PING STARTOWY
                        (defrule (game-time > {5 + slot}) (goal 450 0) => (set-goal 450 1) (up-log-data 0 "SLOT:{slot}|START:%d" g: 450))

                        ; 2. ZAPIS PROGRESU I EKSPLORACJI 
                        (defrule (up-compare-goal 401 g:> 411) => (up-modify-goal 411 g:= 401) (up-log-data 0 "SLOT:{slot}|MIL:%d" g: 411))
                        (defrule (up-compare-goal 402 g:> 412) => (up-modify-goal 412 g:= 402) (up-log-data 0 "SLOT:{slot}|AGE:%d" g: 412))
                        (defrule (up-compare-goal 403 g:> 413) => (up-modify-goal 413 g:= 403) (up-log-data 0 "SLOT:{slot}|EXP:%d" g: 413))

                        ; 3. INFRASTRUKTURA TECHNOLOGICZNA
                        (defrule (building-type-count blacksmith > 0) (goal 454 0) => (set-goal 454 1) (up-log-data 0 "SLOT:{slot}|TEC_BLK:%d" g: 454))
                        (defrule (building-type-count university > 0) (goal 455 0) => (set-goal 455 1) (up-log-data 0 "SLOT:{slot}|TEC_UNI:%d" g: 455))
                        (defrule (building-type-count castle > 0) (goal 456 0) => (set-goal 456 1) (up-log-data 0 "SLOT:{slot}|TEC_CST:%d" g: 456))
                        (defrule (building-type-count market > 0) (goal 457 0) => (set-goal 457 1) (up-log-data 0 "SLOT:{slot}|TEC_MAR:%d" g: 457))
                        (defrule (building-type-count monastery > 0) (goal 458 0) => (set-goal 458 1) (up-log-data 0 "SLOT:{slot}|TEC_MON:%d" g: 458))

                        ; 4. KLAUZULA PRZETRWANIA i WIN
                        (defrule (building-type-count town-center == 0) (game-time > 60) (goal 451 0) => (set-goal 451 1) (up-log-data 0 "SLOT:{slot}|LOSE_TC:%d" g: 451))
                        (defrule (stance-toward target-player enemy) (players-building-type-count target-player town-center == 0) (game-time > 60) (goal 452 0) => (set-goal 452 1) (up-log-data 0 "SLOT:{slot}|WIN:%d" g: 452))
                        """

            # [NAPRAWIONE] Zlepiamy wszystkie elementy
            bot_content = f"; Genetyczny Barbarian GP | Global ID: {global_idx}\n" + up_constants + telemetry_rule + lisp_code + dummy_rule

            for fld in folders_to_seed:
                # Ścieżka do kodu Lisp (.per)
                per_path = os.path.join(fld, f"Milibot_Evo_{slot}.per")
                # [NOWE] Ścieżka do pliku metadanych (.ai) - wymagane przez silnik dla I/O!
                ai_path = os.path.join(fld, f"Milibot_Evo_{slot}.ai")

                # [ZMIANA]: Przepuszczamy kod przez nasz filtr, aby usunąć "sieroty" po =>
                bezpieczny_bot_content = sanitize_bot_code(bot_content)

                # Zapisujemy oczyszczony mózg bota
                with open(per_path, "w") as f:
                    f.write(bezpieczny_bot_content)

                # Zapisujemy pusty plik .ai, aby wylegitymować bota przed silnikiem
                with open(ai_path, "w") as f:
                    f.write("")


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
                    # Flaga sprawdzająca czy każde drzewo dało się poprawnie sparsować
                    udana_konwersja = True

                    for w in ostatnia_populacja:
                        try:
                            bot_id = int(w[1])
                            punkty = float(w[2])
                            drzewo_str = w[3]

                            drzewo_obj = gp.PrimitiveTree.from_string(drzewo_str, pset)
                            osobnik = creator.Individual(drzewo_obj)
                            osobnik.fitness.values = (punkty,)
                            odtworzona_oceniona_populacja.append((punkty, osobnik, bot_id))
                        except Exception as parse_err:
                            print(f"  [!] Drzewo bota {w[1]} jest niekompatybilne z obecnym pset: {parse_err}")
                            udana_konwersja = False
                            break

                    if udana_konwersja and odtworzona_oceniona_populacja:
                        print("[*] Generowanie nowych krzyżówek na bazie wskrzeszonej populacji...")
                        population = build_next_generation(odtworzona_oceniona_populacja)
                        current_gen += 1
                    else:
                        raise ValueError("Wykryto niezgodność struktury drzew w pliku CSV.")
                else:
                    raise ValueError("Plik CSV jest pusty.")
        except Exception as e:
            print(f"[!] Błąd odczytu CSV, tworzę nową populację od zera. Błąd: {e}")
            population = create_initial_population(POPULATION_SIZE)
            current_gen = 1
    else:
        population = create_initial_population(POPULATION_SIZE)
        current_gen = 1

        # ==========================================
        # GŁÓWNA PĘTLA SYMULACJI (Zwróć uwagę na wcięcie!)
        # ==========================================
    while True:
        print(f"\n=================== ROZPOCZYNAM GENERACJĘ {current_gen} ===================")

        print("[*] Generowanie kodu źródłowego Lisp i dystrybucja do workerów...")
        deploy_population_to_workers(population)

        print(f"[*] Uruchamiam równoległe symulacje dla pokolenia {current_gen}...")
        # Odbieramy pakiety słowników z wynikami
        match_results = run_match_and_evaluate_parallel(NUM_WORKERS)

        scored_population = []
        for global_id in range(POPULATION_SIZE):
            bot_data = match_results[global_id]
            base_score = bot_data['base']
            bonus_score = bot_data['bonus']
            penalty_score = bot_data['penalty']
            max_mil = bot_data['mil']
            max_age = bot_data['age']
            max_exp = bot_data['exp']
            tech_count = bot_data.get('tech', 0)  # Wyciągamy punkty z infrastruktury!

            raw_score = float(base_score + bonus_score - penalty_score)
            individual = population[global_id]

            # ==========================================
            # KARY GENETYCZNE
            # ==========================================
            wysokosc_drzewa = individual.height
            max_wysokosc = 300.0

            ratio = max(0.0, min(wysokosc_drzewa / max_wysokosc, 1.0))

            if ratio <= 0.25:
                procent_kary = (ratio / 0.25) * 0.00
            elif ratio <= 0.75:
                procent_kary = 0.00 + ((ratio - 0.50) / 0.50) * 0.01
            elif ratio <= 0.90:
                procent_kary = 0.01 + ((ratio - 0.75) / 0.15) * 0.04
            else:
                procent_kary = 0.05 + ((ratio - 0.90) / 0.10) * 0.75

            kara_wysokosci = raw_score * procent_kary

            ilosc_wezlow = len(individual)
            mnoznik_podatku = 1
            koszt_metaboliczny = ilosc_wezlow * mnoznik_podatku

            final_score = max(0.0, raw_score - kara_wysokosci - koszt_metaboliczny)
            individual.fitness.values = (final_score,)

            # [NOWE] Zapisujemy aż 12 elementów, żeby wszystko było prawilnie logowane
            scored_population.append(
                (final_score, individual, global_id, base_score, bonus_score, kara_wysokosci, koszt_metaboliczny,
                 max_mil, max_age, max_exp, penalty_score, tech_count))

        scored_population.sort(key=lambda x: x[0], reverse=True)

        # Zapis do CSV
        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for row_data in scored_population:
                writer.writerow([current_gen, row_data[2], row_data[0], str(row_data[1])])
            file.flush()
            os.fsync(file.fileno())

        # SZCZEGÓŁOWE WYŚWIETLANIE TOP 4
        print(f"\n--- TOP WYNIKI GENERACJI {current_gen} ---")
        for rank, row_data in enumerate(scored_population[:16]):
            # Rozpakowujemy krotkę do zmiennych
            score, ind, g_id, base, bonus, k_wys, k_met, mil, age, exp, pen, tech = row_data[:12]

            tree_preview = str(ind)[:80] + "..." if len(str(ind)) > 80 else str(ind)
            szerokosc = len(ind)
            glebokosc = ind.height

            print(f" #{rank + 1}: Bot {g_id} (TOTAL: {score:.1f} pkt) -> {tree_preview}")
            print(
                f"     [Detale: Baza: {base} | Bonus: {bonus} (MIL:{mil}, AGE:{age}, EXP:{exp}%, BLD_TECH:{tech}) | Kara w grze: -{pen} | Kary AST: Wys={k_wys:.1f}, Rozmiar={k_met:.1f} | Głęb: {glebokosc}, Szer: {szerokosc}]")

        print("[*] Przetwarzanie operatorów genetycznych dla nowego pokolenia...")

        # Formatyzujemy krotkę z powrotem do 3 elementów, zanim wyślemy ją do engine'u genetycznego!
        engine_ready_population = [(row[0], row[1], row[2]) for row in scored_population]
        population = build_next_generation(engine_ready_population)
        current_gen += 1

if __name__ == "__main__":
    main()