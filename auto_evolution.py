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

POPULATION_SIZE = 8  # Wracamy do pełnych 8 Milibotów
GENERATIONS = 10
MATCH_DURATION = 60


# ==========================================
# 2. MECHANIKA GENETYCZNA (Wielkie DNA)
# ==========================================
def create_random_genome():
    return {
        'town_size': random.randint(30, 60),
        'wood_percent': random.randint(20, 50),
        'gold_percent': random.randint(0, 20),
        'stone_percent': random.randint(0, 10),
        'feudal_vills': random.randint(18, 30),
        'castle_vills': random.randint(32, 50),
        'boar_hunting': random.choice([0, 1]),
        'boar_hunters': random.randint(4, 8),
        'max_lumber_camps': random.randint(1, 3),
        'max_mining_camps': random.randint(1, 3),
        'build_market': random.choice([0, 1]),
        'build_blacksmith': random.choice([0, 1]),
        'build_archery': random.choice([0, 1]),
        'build_stable': random.choice([0, 1]),
        'build_tower': random.choice([0, 1]),
        'militia_count': random.randint(0, 8),
        'archer_count': random.randint(0, 15),
        'skirm_count': random.randint(0, 10),
        'scout_count': random.randint(0, 8),
        'attack_percent': random.randint(50, 100),
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
    rate = 0.10  # 15% mutacji

    for key, val in mutated.items():
        if random.random() < rate:
            if 'percent' in key and key != 'attack_percent':
                mutated[key] = max(0, min(60, val + random.randint(-5, 5)))
            elif 'count' in key or 'size' in key or 'vills' in key or 'hunters' in key:
                mutated[key] = max(0, val + random.randint(-2, 2))
            elif 'tech_' in key or 'build_' in key or key == 'boar_hunting':
                mutated[key] = 1 - val
            elif key == 'attack_percent':
                mutated[key] = max(20, min(100, val + random.randint(-10, 10)))
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


# ==========================================
# 3. WIZJA KOMPUTEROWA (WYNIKI WOJSKOWE)
# ==========================================
def extract_scores_via_ocr():
    print("[*] Wykonuję skan OCR statystyk wojskowych...")
    try:
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
            liczby = [int(x) for x in re.findall(r'\d+', linia)]

            # Weryfikacja: Szukamy rzędów, gdzie OCR odczytał minimum 5 lub 6 liczb (statystyki gracza)
            if len(liczby) >= 5:
                # Bierzemy ostatnie 6 liczb z rzędu (jeśli jest ich 6) lub paddujemy zerami
                dane = liczby[-6:] if len(liczby) >= 6 else [0] + liczby[-5:]

                zabite = dane[0]
                # stracone = dane[1] (IGNORUJEMY)
                zburzone = dane[2]
                # stracone_bud = dane[3] (IGNORUJEMY)
                # przejete = dane[4] (Ignorujemy dla uproszczenia, rzadkie we wczesnych erach)
                armia = dane[5]

                # WAŻONA FUNKCJA NAGRODY:
                aktywnosc_militarna = (zabite * 10) + (zburzone * 50) + (armia * 2)
                raw_scores.append(aktywnosc_militarna)

        if not raw_scores or len(raw_scores) < (POPULATION_SIZE - 2):  # Zapas błędu, np. ktoś wcześnie odpadł
            return None

        while len(raw_scores) < POPULATION_SIZE:
            raw_scores.append(0)

        return raw_scores[:POPULATION_SIZE]

    except Exception as e:
        print(f"  [!] Błąd wewnętrzny OCR: {e}")
        return None


def sprawdz_wzorzec(nazwa_pliku):
    try:
        return pyautogui.locateOnScreen(nazwa_pliku, confidence=0.8) is not None
    except:
        return False


# ==========================================
# 4. NAWIGACJA (Z WIZUALNĄ PĘTLĄ RATUNKOWĄ)
# ==========================================
def run_match_and_evaluate(population):
    while True:
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

        print("\n[*] Czas minął. Przechodzenie do statystyk...")
        pyautogui.click(x=3383, y=44)  # Menu
        time.sleep(0.8)
        pyautogui.click(x=1700, y=550)  # Opuść
        time.sleep(0.8)
        pyautogui.click(x=1500, y=800)  # Tak
        time.sleep(1.5)

        pyautogui.click(x=1200, y=50)  # Wojskowy
        time.sleep(1)

        # ---------------------------------------------------
        # BLOK ANALIZY I RATUNKU (Max 3 próby)
        # ---------------------------------------------------
        ocr_sukces = False
        raw_scores = []

        for proba in range(3):
            raw_scores = extract_scores_via_ocr()

            if raw_scores is not None:
                ocr_sukces = True
                break
            else:
                print(f"  [!] Brak wyników (Próba {proba + 1}/3). Uruchamiam analizę ekranu...")

                if sprawdz_wzorzec('wzorzec_menu.png'):
                    print("  -> Wykryto: Menu Główne. Ponawiam: Opuść -> Tak -> Wojskowy")
                    pyautogui.click(x=1700, y=550)
                    time.sleep(1)
                    pyautogui.click(x=1500, y=800)
                    time.sleep(1.5)
                    pyautogui.click(x=1200, y=50)
                    time.sleep(1)

                elif sprawdz_wzorzec('wzorzec_wyjscie.png'):
                    print("  -> Wykryto: Potwierdzenie Wyjścia. Ponawiam: Tak -> Wojskowy")
                    pyautogui.click(x=1500, y=800)
                    time.sleep(1.5)
                    pyautogui.click(x=1200, y=50)
                    time.sleep(1)

                elif sprawdz_wzorzec('wzorzec_wynik.png'):
                    print("  -> Wykryto: Tabela Wyników Ogólnych. Klikam zakładkę Wojskowy.")
                    pyautogui.click(x=1200, y=50)
                    time.sleep(1)

                else:
                    print("  -> Ekran nie pasuje do wzorców. Czekam 3 sekundy...")
                    time.sleep(1)

        # ---------------------------------------------------
        # DECYZJA PO PRÓBACH RATUNKOWYCH
        # ---------------------------------------------------
        if ocr_sukces:
            break
        else:
            print("[!!!] BŁĄD KRYTYCZNY OCR/NAWIGACJI NIE ZOSTAŁ ROZWIĄZANY [!!!]")
            print("[!!!] Program nie zalicza tej generacji. Rozpoczynam mecz całkowicie od nowa.")
            pyautogui.click(x=1000, y=1230)
            time.sleep(1.5)
            continue

    scored_population = []
    print("--- ODCZYTANE WYNIKI (MNOŻNIK WOJSKOWY) ---")
    for idx, genome in enumerate(population):
        bot_id = idx + 1
        score = raw_scores[idx]
        scored_population.append((score, genome, bot_id))
        print(f"    [+] Bot {bot_id}: {score} pkt.")

    print("[*] Powrót do menu...")
    pyautogui.click(x=1000, y=1230)
    time.sleep(1)

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
    print("MILI-BOT EVOLUTION v11.0 (MILITARY FITNESS 8-BOTS) ONLINE")

    start_gen = 0
    population = []

    if os.path.isfile(CSV_FILENAME) and os.path.getsize(CSV_FILENAME) > 0:
        odpowiedz = input(f"[*] Znaleziono stary zapis. Kontynuować? (T/N): ").strip().upper()
        if odpowiedz == 'T':
            evaluated_pop, last_gen = load_population_from_csv()
            if evaluated_pop:
                top_4 = [g for s, g, b in evaluated_pop[:4]]
                next_gen = []

                # 6 Krzyżówek z Top 4
                pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
                for p1, p2 in pairs:
                    next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))

                # 7. Bot: Zmutowany potomek Lidera
                next_gen.append(mutate(top_4[0]))

                # 8. Bot: Mutant Zero (Całkowicie losowa świeża krew)
                next_gen.append(create_random_genome())

                population = next_gen
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
        evaluated_pop = run_match_and_evaluate(population)

        with open(CSV_FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            for score, genome, bot_id in evaluated_pop:
                row_data = [current_gen, bot_id, score] + list(genome.values())
                writer.writerow(row_data)

        print("\n--- TOP 4 WYNIKI GENERACJI ---")
        for rank, (score, genome, bot_id) in enumerate(evaluated_pop[:4]):
            print(
                f" #{rank + 1}: Bot {bot_id} (Wynik bojowy: {score}) | Las: {genome['wood_percent']}%, Złoto: {genome['gold_percent']}%, Kawaleria: {genome['scout_count']}")

        # Reprodukcja na kolejne pokolenie
        top_4 = [g for s, g, b in evaluated_pop[:4]]
        next_gen = []
        pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        for p1, p2 in pairs:
            next_gen.append(mutate(crossover(top_4[p1], top_4[p2])))

        next_gen.append(mutate(top_4[0]))  # Bot 7
        next_gen.append(create_random_genome())  # Bot 8 (Mutant Zero)

        population = next_gen

    print(f"\n[!!!] PROCES ZAKOŃCZONY [!!!]")