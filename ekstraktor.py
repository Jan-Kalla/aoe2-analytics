import csv
import sys
import os

# KRYTYCZNA POPRAWKA: Bezpieczny limit wielkości pola dla Windowsa (2^31 - 1)
maxInt = 2147483647
csv.field_size_limit(maxInt)

input_file = 'historia_ewolucji.csv'  # Upewnij się, że nazwa się zgadza
output_file = 'historia_ewolucji.csv'

print(f"[*] Skanowanie pliku {input_file} w poszukiwaniu najnowszej generacji (to potrwa chwilę)...")

max_gen = 0

# KROK 1: Skanujemy plik tylko po to, żeby znaleźć najwyższy numer generacji
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

print(f"[*] Znaleziono! Ostatnia generacja to: {max_gen}")
print(f"[*] Kopiowanie danych generacji {max_gen} do nowego pliku...")

# KROK 2: Przechodzimy przez plik jeszcze raz i wyłapujemy tylko wiersze z max_gen
zapisano_wierszy = 0
with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8', newline='') as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)

    # Kopiujemy nagłówek
    fin.seek(0)
    writer.writerow(next(reader))

    for row in reader:
        if row:
            try:
                if int(row[0]) == max_gen:
                    writer.writerow(row)
                    zapisano_wierszy += 1
            except ValueError:
                continue

print(f"[*] Gotowe! Zapisano {zapisano_wierszy} botów z generacji {max_gen} do pliku '{output_file}'.")