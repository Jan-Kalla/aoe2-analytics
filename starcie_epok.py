import os
import csv
import pandas as pd

# Ścieżki (upewnij się, że są takie same jak w głównym skrypcie)
TEMPLATE_FILE = "template.per"
AOE2_AI_FOLDER = "D:\\Steam\\steamapps\\common\\AoE2DE\\resources\\_common\\ai"
CSV_FILENAME = "historia_ewolucji.csv"


def generate_clash_of_eras():
    print("[*] Przygotowuję Turniej: STARCIE EPOK (Przodkowie vs Drapieżniki)")

    # Wczytanie bazy danych
    df = pd.read_csv(CSV_FILENAME)

    # Czyszczenie błędu OCR (ósemki) dla pewności
    df.loc[df['Punkty'] > 7000, 'Punkty'] = df.loc[df['Punkty'] > 7000, 'Punkty'] % 10000 + 3000

    # Ekstrakcja 4 najlepszych z Generacji 2 (Przodkowie) i 60 (Drapieżniki)
    gen_early = df[df['Generacja'] == 2].sort_values(by='Punkty', ascending=False).head(4)
    gen_late = df[df['Generacja'] == 60].sort_values(by='Punkty', ascending=False).head(4)

    # Konwersja na słowniki genów
    early_genomes = gen_early.drop(columns=['Generacja', 'Bot_ID', 'Punkty']).to_dict(orient='records')
    late_genomes = gen_late.drop(columns=['Generacja', 'Bot_ID', 'Punkty']).to_dict(orient='records')

    # Łączymy w jedną listę 8 uczestników
    tournament_roster = early_genomes + late_genomes

    with open(TEMPLATE_FILE, "r") as f:
        template_content = f.read()

    print("\n--- TWORZENIE PLIKÓW AI ---")
    for idx, genome in enumerate(tournament_roster):
        bot_id = idx + 1
        name = f"Milibot_Evo_{bot_id}"

        # Oznaczanie dla konsoli
        drużyna = "PRZODKOWIE (Gen 2)" if bot_id <= 4 else "DRAPIEŻNIKI (Gen 60)"
        print(
            f"[+] Generowanie: {name} -> Frakcja: {drużyna} | Drewno: {genome['wood_percent']}%, Złoto: {genome['gold_percent']}%, Kawaleria: {genome['scout_count']}")

        # Zabezpieczenie żywności
        food_p = max(0, 100 - genome['wood_percent'] - genome['gold_percent'] - genome['stone_percent'])

        # Wstrzykiwanie genów
        bot_content = template_content.replace("{{BOT_ID}}", str(bot_id))
        for key, value in genome.items():
            bot_content = bot_content.replace(f"{{{{{key.upper()}}}}}", str(value))

        bot_content = bot_content.replace("{{FOOD_PERCENT}}", str(food_p))

        # Zapis do folderu gry
        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.per"), "w") as f:
            f.write(bot_content)
        with open(os.path.join(AOE2_AI_FOLDER, f"{name}.ai"), "w") as f:
            f.write(f'(load "{name}")\n')

    print("\n[!!!] GOTOWE! Możesz odpalić Age of Empires 2 [!!!]")
    print("Sugerowane ustawienie gry: 4v4 (Boty 1-4 w Drużynie 1, Boty 5-8 w Drużynie 2)")


if __name__ == "__main__":
    generate_clash_of_eras()