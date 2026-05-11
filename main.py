import os
import time
import csv
from config import *
from genetic_engine import create_random_genome, deploy_tournament_bots, load_population_from_csv, crossover, mutate
from vision_rpa import run_match_and_evaluate

import pyautogui
pyautogui.FAILSAFE = False

if __name__ == "__main__":
    print("MILI-BOT EVOLUTION v13 (MODULAR + CELLULAR OCR) ONLINE")

    start_gen = 0
    population = []

    if os.path.isfile(CSV_FILENAME) and os.path.getsize(CSV_FILENAME) > 0:
        odpowiedz = input(f"[*] Znaleziono stary zapis. Kontynuować? (T/N): ").strip().upper()
        if odpowiedz == 'T':
            evaluated_pop, last_gen = load_population_from_csv()
            if evaluated_pop:
                top_4 = [g for s, g, b in evaluated_pop[:4]]
                next_gen = []
                pairs = [(2, 3), (0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]
                for p1, p2 in pairs:
                    next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))
                next_gen.append(top_4[0].copy())

                next_gen.append(create_random_genome())
                population = next_gen
                start_gen = last_gen
        else:
            os.rename(CSV_FILENAME, f"historia_backup_{int(time.time())}.csv")
            population = [create_random_genome() for _ in range(POPULATION_SIZE)]
    else:
        population = [create_random_genome() for _ in range(POPULATION_SIZE)]

    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            headers = ['Generacja', 'Bot_ID', 'Punkty'] + list(population[0].keys())
            writer.writerow(headers)

    print("\n!!! Zaczynamy za 4 sekundy! Zrób Alt-Tab do gry !!!")
    time.sleep(4)

    for gen in range(start_gen, start_gen + GENERATIONS):
        current_gen = gen + 1
        print(f"\n====================================")
        print(f">>> GENERACJA {current_gen}/{start_gen + GENERATIONS}")
        print(f"====================================")

        deploy_tournament_bots(population)

        raw_scores = run_match_and_evaluate()

        scored_population = []
        for idx, genome in enumerate(population):
            bot_id = idx + 1
            score = raw_scores[idx]
            scored_population.append((score, genome, bot_id))

        scored_population.sort(key=lambda x: x[0], reverse=True)

        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for score, genome, bot_id in scored_population:
                row_data = [current_gen, bot_id, score] + list(genome.values())
                writer.writerow(row_data)

        print("\n--- TOP 4 WYNIKI GENERACJI ---")
        for rank, (score, genome, bot_id) in enumerate(scored_population[:4]):
            print(
                f" #{rank + 1}: Bot {bot_id} (Wynik bojowy: {score}) | Las: {genome['wood_percent']}%, Złoto: {genome['gold_percent']}%, Kawaleria: {genome['scout_count']}")

        top_4 = [g for s, g, b in scored_population[:4]]
        next_gen = []
        pairs = [(2, 3), (0, 1), (0, 2), (0, 3), (1, 2), (1, 3)]
        for p1, p2 in pairs:
            next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))

        next_gen.append(top_4[0].copy())

        next_gen.append(create_random_genome())

        population = next_gen

    print(f"\n[!!!] PROCES ZAKOŃCZONY [!!!]")