import random
import os
import csv
from config import *


def create_random_genome():
    return {
        'town_size': random.randint(15, 30),
        'wood_percent': random.randint(20, 50),
        'gold_percent': random.randint(0, 20),
        'stone_percent': random.randint(0, 10),

        # Poprawka 1: Szersze widełki awansu, żeby uciec z "więzienia genetycznego"
        'feudal_vills': random.randint(18, 28),
        'castle_vills': random.randint(28, 40),

        'boar_hunting': random.choice([0, 1]),
        'boar_hunters': random.randint(4, 8),

        # Geny Budynków
        'build_market': random.choice([0, 1]),
        'build_blacksmith': random.choice([0, 1]),
        'build_archery': random.choice([0, 1]),
        'build_stable': random.choice([0, 1]),
        'build_tower': random.choice([0, 1]),
        'build_palisade': random.choice([0, 1]),
        'build_castle': random.choice([0, 1]),
        'build_siege': 1,  # Zablokowane na stałe

        # Geny Wojskowe
        'militia_count': random.randint(0, 10),
        'archer_count': random.randint(10, 40),
        'skirm_count': random.randint(0, 15),
        'scout_count': random.randint(0, 10),
        'spearman_count': random.randint(0, 25),
        'knight_count': random.randint(10, 30),
        'ram_count': random.randint(2, 5),

        # Geny Taktyczne
        'attack_group_size': random.randint(12, 35),
        'target_eco': random.choice([0, 1]),
        'attack_percent': random.randint(50, 100),
        'min_attack_group': random.randint(8, 20),
        'army_size_with_siege': random.randint(15, 25),
        'army_size_no_siege': random.randint(35, 50),

        # Geny Technologii
        'tech_loom': random.choice([0, 1]),
        'tech_wheelbarrow': random.choice([0, 1]),
        'tech_double_axe': random.choice([0, 1]),
        'tech_horse_collar': random.choice([0, 1]),
        'tech_gold_mining': random.choice([0, 1]),
        'tech_fletching': random.choice([0, 1]),
        'tech_padded_archer': random.choice([0, 1]),
        'tech_forging': random.choice([0, 1]),
        'tech_scale_mail': random.choice([0, 1]),
        'tech_bloodlines': random.choice([0, 1])
    }


def crossover(parent1, parent2):
    child = {}
    for key in parent1.keys():
        child[key] = parent1[key] if random.random() > 0.5 else parent2[key]
    return child


def mutate(genome):
    mutated = genome.copy()
    for key, val in mutated.items():
        if key == 'build_siege':
            continue

        if random.random() < MUTATION_RATE:
            if key in ['build_market', 'build_blacksmith', 'build_archery', 'build_stable',
                       'build_tower', 'build_palisade', 'build_castle', 'boar_hunting', 'target_eco'] or 'tech_' in key:
                mutated[key] = 1 - val
            elif 'percent' in key and key != 'attack_percent':
                mutated[key] = max(0, min(60, val + random.randint(-5, 5)))
            elif key == 'attack_percent':
                mutated[key] = max(20, min(100, val + random.randint(-10, 10)))
            else:
                mutated[key] = max(0, val + random.randint(-3, 3))
    return mutated


def deploy_tournament_bots(population):
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template_content = f.read()

    for idx, genome in enumerate(population):
        name = f"Milibot_Evo_{idx + 1}"
        food_p = max(0, 100 - genome['wood_percent'] - genome['gold_percent'] - genome['stone_percent'])
        bot_content = template_content.replace("{{BOT_ID}}", str(idx + 1))

        for key, value in genome.items():
            bot_content = bot_content.replace(f"{{{{{key.upper()}}}}}", str(value))
        bot_content = bot_content.replace("{{FOOD_PERCENT}}", str(food_p))

        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.per"), "w", encoding="utf-8") as f:
            f.write(bot_content)
        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.ai"), "w", encoding="utf-8") as f:
            f.write(f'(load "{name}")\n')


def load_population_from_csv():
    if not os.path.isfile(CSV_FILENAME) or os.path.getsize(CSV_FILENAME) == 0:
        return None, 0
    with open(CSV_FILENAME, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows: return None, 0
    last_gen = max(int(row['Generacja']) for row in rows)
    last_gen_rows = [r for r in rows if int(r['Generacja']) == last_gen]

    evaluated_pop = []
    gene_keys = reader.fieldnames[3:]
    for row in last_gen_rows:
        genome = {key: int(row[key]) for key in gene_keys}
        evaluated_pop.append((int(row['Punkty']), genome, int(row['Bot_ID'])))

    evaluated_pop.sort(key=lambda x: x[0], reverse=True)
    return evaluated_pop, last_gen