import pytesseract
import pyautogui
from PIL import Image
import re
import time

# Ścieżka do Tesseracta
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("[*] Skrypt uruchomiony! Masz 4 sekundy na zrobienie Alt-Tab do gry...")
time.sleep(4)

print("[*] Pobieram zrzut ekranu i wycinam zbędne elementy...")
img = pyautogui.screenshot()
width, height = img.size

# 1. ZACIEŚNIONY KADR (Ucinamy czarny brzeg pergaminu z prawej strony)
img = img.crop((width * 0.35, height * 0.25, width * 0.78, height * 0.75))

# 2. POWIĘKSZENIE OBRAZU 3x (Algorytm Lanczos zachowuje ostrość krawędzi)
# To jest kluczowe, żeby system nie mylił 1, 4 i 7!
img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)

# 3. Konwersja i Binarizacja (Zostawiamy jak było)
img = img.convert('L')
img = img.point(lambda p: 255 if p > 140 else 0)

# Możesz znów podejrzeć ten plik, tekst będzie teraz ogromny i krystalicznie czysty
img.save("wizja_tesseracta_czysta.png")

# 4. ŻELAZNA KONFIGURACJA OCR
# tessedit_char_whitelist wymusza szukanie TYLKO cyfr i spacji!
custom_config = r'--oem 3 --psm 6'
odczytany_tekst = pytesseract.image_to_string(img, config=custom_config)

print("\n--- WYDOBYTE PUNKTY BOTÓW (OD GÓRY DO DOŁU) ---")
scores = []

for linia in odczytany_tekst.split('\n'):
    # Szukamy ciągów minimum 3 cyfr
    liczby = re.findall(r'\d{3,}', linia)

    if liczby:
        # Zawsze bierzemy ostatnią liczbę z wiersza
        wynik_calkowity = int(liczby[-1])
        scores.append(wynik_calkowity)

# Przypisujemy wyniki
for i, score in enumerate(scores[:8]):
    print(f"[+] Milibot_Evo_{i + 1} -> Punktów: {score}")