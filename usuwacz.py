import csv
import sys
import os

# KRYTYCZNA POPRAWKA: Bezpieczny limit wielkości pola dla Windowsa (2^31 - 1)
maxInt = 2147483647
csv.field_size_limit(maxInt)

input_file = 'historia_ewolucji.csv'  # Upewnij się, że nazwa się zgadza
temp_file = 'historia_ewolucji_temp.csv'

print(f"[*] Skanowanie pliku {input_file} w poszukiwaniu najnowszej generacji (to potrwa chwilę)...")

max_gen = 0

# KROK 1: Skanujemy plik tylko po to, żeby znaleźć najwyższy numer generacji
if not os.path.exists(input_file):
    print(f"[!] Nie znaleziono pliku {input_file}!")
    sys.exit()

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)  # Pomijamy nagłówek
    except StopIteration:
        print("[!] Plik jest pusty!")
        sys.exit()

    for row in reader:
        if row:
            try:
                gen = int(row[0])
                if gen > max_gen:
                    max_gen = gen
            except ValueError:
                continue  # Ignorujemy uszkodzone wiersze

print(f"[*] Znaleziono! Najnowsza generacja do usunięcia to: {max_gen}")
print(f"[*] Przepisywanie danych (z pominięciem generacji {max_gen}) do pliku tymczasowego...")

# KROK 2: Przechodzimy przez plik jeszcze raz i zapisujemy wszystko OPRÓCZ max_gen
zapisano_wierszy = 0
usunieto_wierszy = 0

with open(input_file, 'r', encoding='utf-8') as fin, open(temp_file, 'w', encoding='utf-8', newline='') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)

    # Kopiujemy nagłówek
    fin.seek(0)
    writer.writerow(next(reader))

    for row in reader:
        if row:
            try:
                if int(row[0]) != max_gen:
                    writer.writerow(row)
                    zapisano_wierszy += 1
                else:
                    usunieto_wierszy += 1
            except ValueError:
                continue # Ignorujemy uszkodzone wiersze

# KROK 3: Bezpieczna podmiana pliku oryginalnego plikiem tymczasowym
os.replace(temp_file, input_file)

print(f"[*] Gotowe! Usunięto {usunieto_wierszy} botów z generacji {max_gen}.")
print(f"[*] Plik '{input_file}' zawiera teraz dane do generacji {max_gen - 1} włącznie (łącznie {zapisano_wierszy} wierszy).")