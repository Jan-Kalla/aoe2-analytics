import csv
import sys
import os
from collections import defaultdict
import matplotlib.pyplot as plt

# Zabezpieczenie limitu Windowsa
maxInt = 2147483647
csv.field_size_limit(maxInt)

INPUT_FILE = 'historia_ewolucji.csv'

# ROZSZERZONA LISTA SŁÓW KLUCZOWYCH
TRACKED_ACTIONS = [
    'a_train_vill', 'a_build_house', 'a_build_mill', 'a_build_farm',  # Gospodarka
    'a_train_infantry', 'a_train_ram', 'a_attack_now',  # Wojsko
    'a_dyn_town_size', 'a_dynamic_civ_scout_cap',  # Dynamiczne parametry
    'a_go_feudal_age', 'a_go_castle_age',  # Epoki
    'a_res_loom', 'a_res_axe_1', 'a_res_farm_1'  # Kluczowe Technologie (Troska, Siekiera, Chomąto)
]

print(f"[*] Rozpoczynam strumieniowe przetwarzanie pliku {INPUT_FILE}...")

stats = defaultdict(lambda: {
    'scores': [],
    'rules_count': [],
    'actions': defaultdict(list)
})

wierszy_przetworzono = 0

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        next(reader)
    except StopIteration:
        print("[!] Plik jest pusty!")
        sys.exit()

    for row in reader:
        if not row or len(row) < 4:
            continue
        try:
            gen = int(row[0])
            score = float(row[2])
            ast_tree = row[3]
        except ValueError:
            continue

        wierszy_przetworzono += 1
        if wierszy_przetworzono % 50000 == 0:
            print(f"  ... przetworzono już {wierszy_przetworzono} botów ...")

        stats[gen]['scores'].append(score)
        rules = ast_tree.count("DEFRULE")
        stats[gen]['rules_count'].append(rules)

        for action in TRACKED_ACTIONS:
            count = ast_tree.count(action)
            stats[gen]['actions'][action].append(count)

print("[*] Plik wczytany! Przygotowuję dane do wykresów...")

generations = sorted(list(stats.keys()))

max_scores, mean_scores, min_scores, mean_rules = [], [], [], []
action_means = defaultdict(list)

for gen in generations:
    gen_scores = stats[gen]['scores']
    max_scores.append(max(gen_scores))
    mean_scores.append(sum(gen_scores) / len(gen_scores))
    min_scores.append(min(gen_scores))

    rules = stats[gen]['rules_count']
    mean_rules.append(sum(rules) / len(rules))

    for action in TRACKED_ACTIONS:
        acts = stats[gen]['actions'][action]
        action_means[action].append(sum(acts) / len(acts))

# --- GENEROWANIE WYKRESÓW ---
print("[*] Rysowanie wykresów...")
plt.style.use('seaborn-v0_8-darkgrid')

# 1. WYKRES PUNKTÓW
plt.figure(figsize=(12, 6))
plt.plot(generations, max_scores, label='Max Wynik (Liderzy)', color='gold', linewidth=2)
plt.plot(generations, mean_scores, label='Średni Wynik (Populacja)', color='blue', linewidth=2)
plt.fill_between(generations, min_scores, max_scores, color='blue', alpha=0.1)
plt.title(f'Ewolucja Punktowa ({generations[-1]} Generacji)')
plt.xlabel('Generacja')
plt.ylabel('Punkty (Score)')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_1_punkty.png', dpi=300)
plt.close()

# 2. WYKRES PUCHNIĘCIA KODU
plt.figure(figsize=(12, 6))
plt.plot(generations, mean_rules, label='Średnia liczba reguł na bota (AST)', color='green', linewidth=2)
plt.title('Rozwój Mózgu (Złożoność Drzewa AST)')
plt.xlabel('Generacja')
plt.ylabel('Ilość reguł (DEFRULE)')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_2_puchniecie.png', dpi=300)
plt.close()

# 3. WYKRES GOSPODARKI I ZABUDOWY
plt.figure(figsize=(12, 6))
plt.plot(generations, action_means['a_train_vill'], label='Chłopi (a_train_vill)')
plt.plot(generations, action_means['a_build_house'], label='Domy (a_build_house)')
plt.plot(generations, action_means['a_build_mill'], label='Młyny (a_build_mill)')
plt.plot(generations, action_means['a_build_farm'], label='Farmy (a_build_farm)')
plt.title('Ewolucja Makroekonomii (Częstotliwość genów)')
plt.xlabel('Generacja')
plt.ylabel('Średnie wystąpienia w kodzie')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_3_gospodarka.png', dpi=300)
plt.close()

# 4. WYKRES MILITARNY / AGRESJI
plt.figure(figsize=(12, 6))
plt.plot(generations, action_means['a_train_infantry'], label='Piechota (a_train_infantry)')
plt.plot(generations, action_means['a_train_ram'], label='Tarany (a_train_ram)')
plt.plot(generations, action_means['a_attack_now'], label='Rozkazy Ataku (a_attack_now)', color='red', linewidth=2)
plt.title('Rozwój Agresji Militarnych')
plt.xlabel('Generacja')
plt.ylabel('Średnie wystąpienia w kodzie')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_4_wojsko.png', dpi=300)
plt.close()

# 5. WYKRES ZMIENNYCH DYNAMICZNYCH
plt.figure(figsize=(12, 6))
plt.plot(generations, action_means['a_dyn_town_size'], label='Dyn. Wielkość Miasta (a_dyn_town_size)')
plt.plot(generations, action_means['a_dynamic_civ_scout_cap'], label='Dyn. Limit Zwiadowców')
plt.title('Wykorzystanie Dynamicznych Stałych (ERC)')
plt.xlabel('Generacja')
plt.ylabel('Średnie wystąpienia w kodzie')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_5_parametry_dynamiczne.png', dpi=300)
plt.close()

# 6. WYKRES EPOK I TECHNOLOGII [NOWY]
plt.figure(figsize=(12, 6))
plt.plot(generations, action_means['a_go_feudal_age'], label='Feudal Age (a_go_feudal_age)', color='purple',
         linewidth=2)
plt.plot(generations, action_means['a_res_loom'], label='Troska / Loom (a_res_loom)', linestyle='--')
plt.plot(generations, action_means['a_res_axe_1'], label='Siekiera / Double-Bit Axe (a_res_axe_1)')
plt.plot(generations, action_means['a_res_farm_1'], label='Chomąto / Horse Collar (a_res_farm_1)')
plt.title('Rozwój Technologiczny i Awans Epok')
plt.xlabel('Generacja')
plt.ylabel('Średnie wystąpienia w kodzie')
plt.legend()
plt.tight_layout()
plt.savefig('wykres_6_technologie.png', dpi=300)
plt.close()

print("[*] SUKCES! 6 Wykresów zostało zapisanych.")