import time
import pyautogui
import pytesseract
import re
from PIL import Image, ImageOps
from config import *

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def awaryjne_rozpoznanie_ekranu():
    """Robi zrzut centralnej części ekranu, podbija kontrast i czyta słowa kluczowe OCR."""
    try:
        img = pyautogui.screenshot()
        W, H = img.size

        # Tniemy szeroki środek ekranu (złapie każde menu na ultrawide)
        x_start = W * 0.30
        x_end = W * 0.70
        y_start = H * 0.20
        y_end = H * 0.80

        center_img = img.crop((x_start, y_start, x_end, y_end))

        # POWIĘKSZENIE I KONTRAST
        center_img = center_img.resize((center_img.width * 2, center_img.height * 2), Image.Resampling.LANCZOS)
        center_img = center_img.convert('L')
        center_img = center_img.point(lambda p: 0 if p < 130 else 255)

        center_img.save("DEBUG_awaryjny_ekran.png")

        tekst = pytesseract.image_to_string(center_img, config='--oem 3 --psm 3').lower()

        with open("DEBUG_awaryjny_tekst.txt", "w", encoding="utf-8") as f:
            f.write("--- ODCZYT AWARYJNY ---\n")
            f.write(tekst)

        if "rezygnuj" in tekst or "opcje" in tekst or "zrestartuj" in tekst or "opu" in tekst:
            return "MENU_PAUZY"
        elif "chcesz" in tekst or "tak" in tekst or "nie" in tekst:
            return "POTWIERDZENIE_WYJSCIA"
        elif "statystyki" in tekst or "wynik" in tekst or "gospodarczy" in tekst or "wojskowy" in tekst:
            return "WYNIKI_OGOLNE"
        else:
            return "NIEZNANY"

    except Exception as e:
        print(f"  [!] Błąd w awaryjnym OCR: {e}")
        return "NIEZNANY"


def sprawdz_wzorzec(nazwa_pliku):
    try:
        return pyautogui.locateOnScreen(nazwa_pliku, confidence=0.8) is not None
    except:
        return False


def extract_military_scores():
    print("[*] Wykonuję skan OCR (Naprawione, NAPRAWDĘ szerokie paski)...")
    try:
        img = pyautogui.screenshot()
        W, H = img.size

        # KADROWANIE ULTRAWIDE-PROOF (Tniemy od 41% szerokości i do 68% wysokości)
        x_start = W * 0.41
        x_end = W * 0.82
        y_start = H * 0.28
        y_end = H * 0.68

        table_img = img.crop((x_start, y_start, x_end, y_end))
        table_img = table_img.resize((table_img.width * 2, table_img.height * 2), Image.Resampling.LANCZOS)
        table_img = table_img.convert('L')
        table_img = table_img.point(lambda p: 0 if p < 130 else 255)

        table_img.save("DEBUG_tabela_ocr.png")
        debug_file = open("DEBUG_log_tekstowy.txt", "w", encoding="utf-8")
        debug_file.write("--- ODCZYT BARDZO SZEROKICH KOLUMN --- \n\n")

        # PSM 6 bez whitelisty, by korony czytało jako litery i omijało dzięki digits[-1]
        custom_config = r'--oem 3 --psm 6'

        tw = table_img.width

        def read_precise_column(ratio_start, ratio_end, nazwa):
            # Tniemy pasek z całej wysokości
            col_img = table_img.crop((int(tw * ratio_start), 0, int(tw * ratio_end), table_img.height))
            # Ramka (padding)
            col_img = ImageOps.expand(col_img, border=20, fill=255)
            col_img.save(f"DEBUG_kolumna_{nazwa}.png")

            txt = pytesseract.image_to_string(col_img, config=custom_config).strip().upper()

            # Słownik podstawowych korekt
            txt_korekta = txt.replace('O', '0').replace('Q', '0').replace('D', '0')
            txt_korekta = txt_korekta.replace('I', '1').replace('L', '1').replace('|', '1').replace(']', '1').replace(
                '[', '1').replace('}', '1').replace('{', '1')

            lines = txt_korekta.split('\n')
            values = []

            for line in lines:
                digits = re.findall(r'\d+', line)
                if digits:
                    # KRYTYCZNA POPRAWKA: Zawsze bierzemy ostatnią liczbę z prawej. Omija to korony!
                    values.append(int(digits[-1]))

            debug_file.write(f"KOLUMNA [{nazwa}] surowy odczyt OCR:\n{txt}\n")
            debug_file.write(f"-> Zinterpretowane: {values}\n\n")

            if not values:
                raise ValueError(f"Kolumna {nazwa} jest całkowicie pusta! Prawdopodobnie jesteś w menu pauzy.")

            while len(values) < 8:
                values.append(0)

            return values[:8]

        # KRYTYCZNA POPRAWKA: Przesunięto PRAWE krawędzie cięcia, żeby nie ucinać długich liczb
        zabojstwa_lista = read_precise_column(0.100, 0.220, "Zabojstwa")
        budynki_lista = read_precise_column(0.300, 0.420, "Budynki")
        armia_lista = read_precise_column(0.665, 0.730, "Armia")

        raw_scores = []
        for r_idx in range(8):
            zabite = zabojstwa_lista[r_idx]
            budynki = budynki_lista[r_idx]
            armia = armia_lista[r_idx]

            wynik = (zabite * 10) + (budynki * 100) + (armia * 2)
            debug_file.write(
                f"BOT {r_idx + 1} => Zabite: {zabite}, Budynki: {budynki}, Armia: {armia} | WYNIK BOJOWY: {wynik}\n")
            raw_scores.append(wynik)

        debug_file.close()

        # Alarm przeciwko awariom menu
        if sum(raw_scores) == 0:
            print("  [!] Ostrzeżenie: Wszystkie wartości równe 0. Wzbudzam ratownika.")
            return None

        if len(raw_scores) < POPULATION_SIZE:
            return None

        return raw_scores

    except Exception as e:
        print(f"  [!] Błąd wewnętrzny OCR: {e}")
        return None


def run_match_and_evaluate():
    while True:
        print("[*] Rozpoczynam nawigację w menu...")
        pyautogui.click(*COORD_MENU_SINGLEPLAYER)
        time.sleep(0.4)
        pyautogui.click(*COORD_MENU_SKIRMISH)
        time.sleep(1.5)

        # --- NOWA NAWIGACJA KLAWIATUROWA (Zmiana Gracza na Bota) ---
        # 2 razy w dół
        pyautogui.press('down', presses=2, interval=0.1)
        time.sleep(0.2)
        # Enter by otworzyć listę
        pyautogui.press('enter')
        time.sleep(0.4)  # Czekamy ułamek sekundy, aż lista się rozwinie
        # 4 razy w dół
        pyautogui.press('down', presses=4, interval=0.1)
        time.sleep(0.2)
        # Enter by potwierdzić wybór
        pyautogui.press('enter')
        time.sleep(0.8)

        print("[*] Rozpoczynam mecz...")
        pyautogui.click(*COORD_MENU_START_GAME)
        time.sleep(1)
        pyautogui.click(*COORD_MENU_START_GAME)

        for i in range(MATCH_DURATION):
            print(f"  Mecz w toku... [{i}/{MATCH_DURATION}s]", end='\r')
            time.sleep(1)

        print("\n[*] Czas minął. Przechodzenie do statystyk...")
        pyautogui.click(*COORD_INGAME_MENU)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_MENU)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_LEAVE)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_LEAVE)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_LEAVE)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_LEAVE)
        time.sleep(0.8)
        pyautogui.click(*COORD_INGAME_YES)
        time.sleep(0.2)
        pyautogui.click(*FUCKUP_EXIT)
        time.sleep(1.5)

        pyautogui.click(*COORD_TAB_MILITARY)
        time.sleep(1)

        ocr_sukces = False
        raw_scores = []

        for proba in range(3):
            raw_scores = extract_military_scores()

            if raw_scores is not None and len(raw_scores) == POPULATION_SIZE:
                ocr_sukces = True
                break
            else:
                stan_ekranu = awaryjne_rozpoznanie_ekranu()
                print(f"  [!] Brak wyników (Próba {proba + 1}/3). Zidentyfikowano ekran jako: {stan_ekranu}")

                if stan_ekranu == "MENU_PAUZY":
                    pyautogui.click(*COORD_INGAME_LEAVE)
                    time.sleep(1)
                    pyautogui.click(*COORD_INGAME_YES)
                    time.sleep(1.5)
                    pyautogui.click(*COORD_TAB_MILITARY)
                    time.sleep(1)
                elif stan_ekranu == "POTWIERDZENIE_WYJSCIA":
                    pyautogui.click(*COORD_INGAME_YES)
                    time.sleep(1.5)
                    pyautogui.click(*COORD_TAB_MILITARY)
                    time.sleep(1)
                elif stan_ekranu == "WYNIKI_OGOLNE":
                    pyautogui.click(*COORD_TAB_MILITARY)
                    time.sleep(1)
                else:
                    print("  [!] Nie mogę rozpoznać ekranu. Czekam...")
                    time.sleep(2)

        if ocr_sukces:
            break
        else:
            print("[!!!] BŁĄD KRYTYCZNY NAWIGACJI [!!!] Wymuszam twardy powrót do Menu Głównego.")
            pyautogui.click(*COORD_BACK_TO_MENU)
            time.sleep(1.5)
            continue

    print("[*] Powrót do menu...")
    pyautogui.click(*COORD_BACK_TO_MENU)
    time.sleep(1)
    pyautogui.click(*COORD_BACK_TO_MENU)
    time.sleep(1)
    pyautogui.click(*COORD_BACK_TO_MENU)
    time.sleep(1)

    return raw_scores