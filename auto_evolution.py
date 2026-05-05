import os
import random
import time
import pyautogui
import re
import pytesseract
import csv
import statistics
from PIL import Image

# ==========================================
# 1. KONFIGURACJA ŚRODOWISKA
# ==========================================
pyautogui.FAILSAFE = True
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TEMPLATE_FILE = "template.per"
AOE2_AI_FOLDER = "D:\\Steam\\steamapps\\common\\AoE2DE\\resources\\_common\\ai"
CSV_FILENAME = "historia_ewolucji.csv"

POPULATION_SIZE = 7
GENERATIONS = 5  # Odpalamy potężną symulację!
MATCH_DURATION = 600  # 15 minut (potrzeba czasu, by boty zdążyły wybudować Feudal/Castle)


# ==========================================
# 2. MECHANIKA GENETYCZNA (Wielkie DNA)
# ==========================================
def create_random_genome():
    return {
        # --- EKONOMIA PODSTAWOWA ---
        'town_size': random.randint(30, 60),
        'wood_percent': random.randint(20, 50),
        'gold_percent': random.randint(0, 20),
        'stone_percent': random.randint(0, 10),  # Kamień na wieże
        'feudal_vills': random.randint(18, 30),  # Chłopi do Feudala
        'castle_vills': random.randint(32, 50),  # Chłopi do Castle
        'boar_hunting': random.choice([0, 1]),
        'boar_hunters': random.randint(4, 8),
        'max_lumber_camps': random.randint(1, 3),
        'max_mining_camps': random.randint(1, 3),

        # --- BUDYNKI (0=Nie buduj, 1=Buduj) ---
        'build_market': random.choice([0, 1]),
        'build_blacksmith': random.choice([0, 1]),
        'build_archery': random.choice([0, 1]),
        'build_stable': random.choice([0, 1]),
        'build_tower': random.choice([0, 1]),

        # --- JEDNOSTKI (Limity ilościowe) ---
        'militia_count': random.randint(0, 8),
        'archer_count': random.randint(0, 15),
        'skirm_count': random.randint(0, 10),
        'scout_count': random.randint(0, 8),
        'attack_percent': random.randint(50, 100),

        # --- TECHNOLOGIE (0=Nie badaj, 1=Badaj) ---
        'tech_loom': random.choice([0, 1]),
        'tech_wheelbarrow': random.choice([0, 1]),
        'tech_double_axe': random.choice([0, 1]),
        'tech_horse_collar': random.choice([0, 1]),
        'tech_gold_mining': random.choice([0, 1]),
        'tech_fletching': random.choice([0, 1]),  # Atak łuczników/wież
        'tech_padded_archer': random.choice([0, 1]),  # Pancerz łuczników
        'tech_forging': random.choice([0, 1]),  # Atak wręcz
        'tech_scale_mail': random.choice([0, 1]),  # Pancerz piechoty
        'tech_bloodlines': random.choice([0, 1])  # Punkty życia kawalerii
    }


def crossover(parent1, parent2):
    child = {}
    for key in parent1.keys():
        child[key] = parent1[key] if random.random() > 0.5 else parent2[key]
    return child


def mutate(genome):
    mutated = genome.copy()
    rate = 0.05  # Zmniejszamy z 10% na 5% (rzadsze mutacje)

    for key, val in mutated.items():
        if random.random() < rate:
            if 'percent' in key and key != 'attack_percent':
                # Zmniejszamy skok z +/- 10 na +/- 5 (delikatne szlifowanie proporcji)
                mutated[key] = max(0, min(60, val + random.randint(-5, 5)))
            elif 'count' in key or 'size' in key or 'vills' in key or 'hunters' in key:
                # Zmniejszamy skok jednostek/chłopów z +/- 3 na +/- 2
                mutated[key] = max(0, val + random.randint(-2, 2))
            elif 'tech_' in key or 'build_' in key or key == 'boar_hunting':
                mutated[key] = 1 - val  # Włącz/Wyłącz pozostaje bez zmian
            elif key == 'attack_percent':
                mutated[key] = max(20, min(100, val + random.randint(-10, 10)))

    return mutated


def deploy_tournament_bots(population):
    with open(TEMPLATE_FILE, "r") as f:
        template_content = f.read()

    for idx, genome in enumerate(population):
        name = f"Milibot_Evo_{idx + 1}"
        # Zabezpieczenie, by jedzenie wypełniło resztę do 100% z 3 innych surowców
        food_p = max(0, 100 - genome['wood_percent'] - genome['gold_percent'] - genome['stone_percent'])

        bot_content = template_content.replace("{{BOT_ID}}", str(idx + 1))
        for key, value in genome.items():
            bot_content = bot_content.replace(f"{{{{{key.upper()}}}}}", str(value))

        bot_content = bot_content.replace("{{FOOD_PERCENT}}", str(food_p))

        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.per"), "w") as f:
            f.write(bot_content)
        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.ai"), "w") as f:
            f.write(f'(load "{name}")\n')


# ==========================================
# 3. WIZJA KOMPUTEROWA (BEZ ZMIAN)
# ==========================================
def extract_scores_via_ocr():
    print("[*] Wykonuję skan OCR tabeli wyników...")
    img = pyautogui.screenshot()
    width, height = img.size

    img = img.crop((width * 0.35, height * 0.25, width * 0.78, height * 0.75))
    img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
    img = img.convert('L')
    img = img.point(lambda p: 255 if p > 140 else 0)

    custom_config = r'--oem 3 --psm 6'
    odczytany_tekst = pytesseract.image_to_string(img, config=custom_config)

    raw_scores = []
    for linia in odczytany_tekst.split('\n'):
        liczby = re.findall(r'\d{3,}', linia)
        if liczby:
            raw_scores.append(int(liczby[-1]))

    if not raw_scores: return []

    sensible_scores = [s for s in raw_scores if 999 < s < 10000]
    median_score = statistics.median(sensible_scores) if sensible_scores else 1000

    clean_scores = []
    for s in raw_scores:
        s_str = str(s)

        # Naprawa błędu OCR (8 zamiast 3)
        if s > 7000 and s_str.startswith('8'):
            s = int('3' + s_str[1:])
            s_str = str(s)

        if s > median_score * 4 and len(s_str) > 3:
            s = int(s_str[1:])
        elif s < median_score * 0.3:
            s = int(s_str + '0')

        clean_scores.append(s)

    # ZWRACAMY TYLKO WYNIKI DLA NASZEJ POPULACJI (Ignorujemy Bossa w 8. slocie)
    return clean_scores[:POPULATION_SIZE]


# ==========================================
# 4. NAWIGACJA (BEZ ZMIAN)
# ==========================================
def run_match_and_evaluate(population):
    print("[*] Rozpoczynam nawigację w menu...")
    pyautogui.click(x=900, y=400)
    time.sleep(0.4)
    pyautogui.click(x=1400, y=700)
    time.sleep(1)
    pyautogui.click(x=1200, y=520)
    time.sleep(0.5)
    pyautogui.click(x=1000, y=670)
    time.sleep(0.5)

    print("[*] Rozpoczynam mecz...")
    pyautogui.click(x=1700, y=1230)
    time.sleep(1)
    pyautogui.click(x=1700, y=1230)

    for i in range(MATCH_DURATION):
        print(f"  Mecz w toku... [{i}/{MATCH_DURATION}s]", end='\r')
        time.sleep(1)

    print("\n[*] Czas minął. Wymuszam zakończenie meczu...")
    # NOWA SEKWENCJA WYCHODZENIA Z GRY NA BAZIE TWOICH WSPÓŁRZĘDNYCH
    pyautogui.click(x=3383, y=44)  # Menu
    time.sleep(0.8)
    pyautogui.click(x=1700, y=550)  # Opuść bieżącą rozgrywkę
    time.sleep(0.8)
    pyautogui.click(x=1500, y=800)  # Tak

    print("[*] Oczekiwanie na załadowanie ekranu statystyk...")
    time.sleep(3)  # Wydłużony czas na pewne załadowanie pergaminu statystyk

    raw_scores = extract_scores_via_ocr()
    if len(raw_scores) < POPULATION_SIZE:
        print(f"[!] Ostrzeżenie: OCR odczytał braki. Uzupełniam.")
        raw_scores.extend([500] * (POPULATION_SIZE - len(raw_scores)))

    scored_population = []
    print("--- ODCZYTANE WYNIKI ---")
    for idx, genome in enumerate(population):
        bot_id = idx + 1
        score = raw_scores[idx]
        scored_population.append((score, genome, bot_id))
        print(f"    [+] Bot {bot_id}: {score} pkt.")

    print("[*] Powrót do menu...")
    pyautogui.click(x=1000, y=1230)
    time.sleep(2)

    scored_population.sort(key=lambda x: x[0], reverse=True)
    return scored_population


# ==========================================
# 5. DYNAMICZNY SYSTEM PAMIĘCI
# ==========================================
def load_population_from_csv():
    with open(CSV_FILENAME, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows: return None, 0

    last_gen = max(int(row['Generacja']) for row in rows)
    last_gen_rows = [r for r in rows if int(r['Generacja']) == last_gen]

    evaluated_pop = []
    # Dynamicznie ładujemy wszystkie klucze od 4 kolumny w górę (pomijając Gen, ID i Punkty)
    gene_keys = reader.fieldnames[3:]
    for row in last_gen_rows:
        genome = {key: int(row[key]) for key in gene_keys}
        evaluated_pop.append((int(row['Punkty']), genome, int(row['Bot_ID'])))

    evaluated_pop.sort(key=lambda x: x[0], reverse=True)
    return evaluated_pop, last_gen


# ==========================================
# 6. PĘTLA GŁÓWNA EVOLUCJI
# ==========================================
if __name__ == "__main__":
    print("MILI-BOT EVOLUTION v9.0 (DYNAMIC DNA) ONLINE")

    start_gen = 0
    population = []

    if os.path.isfile(CSV_FILENAME) and os.path.getsize(CSV_FILENAME) > 0:
        odpowiedz = input(f"[*] Znaleziono stary zapis. Kontynuować? (T/N): ").strip().upper()
        if odpowiedz == 'T':
            evaluated_pop, last_gen = load_population_from_csv()
            if evaluated_pop:
                # Inżynieria genetyczna dla następnej iteracji (Populacja 7)
                top_4 = [g for s, g, b in evaluated_pop[:4]]
                next_gen = []

                # 6 potomków z krzyżowania
                pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
                for p1, p2 in pairs:
                    next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))

                # 1 bezpośredni, zmutowany potomek zwycięzcy (lidera)
                next_gen.append(mutate(top_4[0]))

                population = next_gen
        else:
            os.rename(CSV_FILENAME, f"historia_backup_{int(time.time())}.csv")
            population = [create_random_genome() for _ in range(POPULATION_SIZE)]
    else:
        population = [create_random_genome() for _ in range(POPULATION_SIZE)]

    # Dynamiczne tworzenie nagłówków CSV na podstawie wygenerowanego genomu
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
        evaluated_pop = run_match_and_evaluate(population)

        # Dynamiczny zapis wartości do CSV
        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for score, genome, bot_id in evaluated_pop:
                row_data = [current_gen, bot_id, score] + list(genome.values())
                writer.writerow(row_data)

        print("\n--- TOP 4 WYNIKI GENERACJI ---")
        for rank, (score, genome, bot_id) in enumerate(evaluated_pop[:4]):
            print(
                f" #{rank + 1}: Bot {bot_id} (Punkty: {score}) | Las: {genome['wood_percent']}%, Złoto: {genome['gold_percent']}%, Kawaleria: {genome['scout_count']}")

        # Inżynieria genetyczna dla następnej iteracji (Populacja 7)
        top_4 = [g for s, g, b in evaluated_pop[:4]]
        next_gen = []

        # 6 potomków z krzyżowania
        pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        for p1, p2 in pairs:
            next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))

        # 1 bezpośredni, zmutowany potomek zwycięzcy (lidera)
        next_gen.append(mutate(top_4[0]))

        population = next_gen

    print(f"\n[!!!] PROCES ZAKOŃCZONY [!!!]")