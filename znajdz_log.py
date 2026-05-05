import os
import time

# Skanujemy cały główny folder AoE2 DE
SEARCH_DIR = r"C:\Users\kalla\Games\Age of Empires 2 DE"

print(f"[*] Skanowanie całego folderu: {SEARCH_DIR}")
print("[*] Szukam plików zmodyfikowanych w ciągu ostatnich 15 minut...")

found = False
now = time.time()

for root, dirs, files in os.walk(SEARCH_DIR):
    for file in files:
        if file.endswith(".txt") or file.endswith(".log"):
            filepath = os.path.join(root, file)

            try:
                # Sprawdzamy tylko "świeże" pliki
                if now - os.path.getmtime(filepath) < 900:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Szukamy naszego testowego stringa ATAK LUB samego bota
                        if "TEST: System logowania" in content or "Milibot" in content:
                            print(f"\n[!!!] ZNALAZŁEM UKRYTY PLIK LOGÓW!")
                            print(f" -> Ścieżka: {filepath}")
                            found = True

                    # Czasem pliki są w utf-16, więc sprawdzamy jeszcze raz
                    if not found:
                        with open(filepath, 'r', encoding='utf-16', errors='ignore') as f:
                            content = f.read()
                            if "TEST: System logowania" in content or "Milibot" in content:
                                print(f"\n[!!!] ZNALAZŁEM UKRYTY PLIK LOGÓW (UTF-16)!")
                                print(f" -> Ścieżka: {filepath}")
                                found = True
            except Exception as e:
                pass

if not found:
    print("\n[-] Przeskanowałem wszystko. Silnik gry całkowicie zablokował zapis do pliku.")