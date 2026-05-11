import csv
import os

input_file = 'historia_ewolucji.csv'
output_file = 'historia_ewolucji_fixed.csv'

# Nowa lista nagłówków - BEZ max_lumber_camps i max_mining_camps
new_headers = [
    'Generacja', 'Bot_ID', 'Punkty', 'town_size', 'wood_percent', 'gold_percent', 'stone_percent',
    'feudal_vills', 'castle_vills', 'boar_hunting', 'boar_hunters', 'build_market', 'build_blacksmith',
    'build_archery', 'build_stable', 'build_tower', 'build_palisade', 'build_castle', 'build_siege',
    'militia_count', 'archer_count', 'skirm_count', 'scout_count', 'spearman_count', 'knight_count',
    'ram_count', 'attack_group_size', 'target_eco', 'attack_percent', 'min_attack_group',
    'army_size_with_siege', 'army_size_no_siege', 'tech_loom', 'tech_wheelbarrow', 'tech_double_axe',
    'tech_horse_collar', 'tech_gold_mining', 'tech_fletching', 'tech_padded_archer', 'tech_forging',
    'tech_scale_mail', 'tech_bloodlines'
]

# Domyślne wartości dla genów pobocznych (na wypadek braków w starych generacjach)
defaults = {
    'build_castle': '0',
    'min_attack_group': '15',
    'army_size_with_siege': '20',
    'army_size_no_siege': '40'
}

try:
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, open(output_file, 'w', newline='',
                                                                             encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Odczytujemy stare nagłówki
        old_headers = next(reader)
        # Zapisujemy nowe nagłówki (odchudzone)
        writer.writerow(new_headers)

        for row in reader:
            # Zabezpieczenie przed uszkodzonymi wierszami (np. błędy zapisu z poprzednich dni)
            if len(old_headers) == len(row):
                # Tworzymy słownik z obecnego wiersza
                old_dict = dict(zip(old_headers, row))
            else:
                continue  # Pomijamy uszkodzony wiersz

            new_row = []
            for header in new_headers:
                # Wyciągamy wartość, o ile gen istniał (zignoruje usunięte camps, bo nie ma ich w new_headers)
                if header in old_dict:
                    new_row.append(old_dict[header])
                # Wstawienie domyślnej, jeśli w starej bazie nie było danego genu
                else:
                    new_row.append(defaults.get(header, '0'))

            writer.writerow(new_row)

    # Zabezpieczenie danych
    os.rename(input_file, 'historia_ewolucji_BACKUP.csv')
    os.rename(output_file, input_file)

    print("[+] SUKCES: Baza danych zaktualizowana. Usunięto limity obozów i wyrównano strukturę plików.")

except Exception as e:
    print(f"[-] Błąd podczas konwersji: {e}")