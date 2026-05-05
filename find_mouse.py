import pyautogui
import time

print("Radar myszki włączony! Aby wyłączyć, kliknij CZERWONY KWADRAT w PyCharmie.")
print("Najedź na przycisk w grze i spisz liczby!")

try:
    while True:
        x, y = pyautogui.position()
        print(f"X: {x:>4} | Y: {y:>4}")
        time.sleep(1.5)  # Wyświetla nową pozycję co 1.5 sekundy
except KeyboardInterrupt:
    print("Koniec.")