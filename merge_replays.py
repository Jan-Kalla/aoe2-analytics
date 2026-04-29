import os
import zipfile
import shutil

# 1. Ścieżka, gdzie pobrałeś paczki .zip z Discorda
DOWNLOAD_DIR = r"C:\Users\kalla\Downloads\Turniej"  # Zmień na właściwą ścieżkę z Twojego komputera

# 2. Docelowy folder w naszym projekcie
TARGET_DIR = "replays"


def merge_replays():
    print(f"[*] Rozpoczynam konsolidację powtórek z folderu: {DOWNLOAD_DIR}")

    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    extracted_count = 0

    # Przeszukujemy folder pobranych plików
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".zip"):
            zip_path = os.path.join(DOWNLOAD_DIR, filename)
            print(f"-> Znaleziono paczkę: {filename}. Rozpakowywanie...")

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Sprawdzamy zawartość ZIPa
                    for file_in_zip in zip_ref.namelist():
                        if file_in_zip.endswith(".aoe2record"):
                            # Wyciągamy plik bezpośrednio do docelowego folderu (pomijając ewentualne podfoldery w ZIPie)
                            extracted_path = zip_ref.extract(file_in_zip, TARGET_DIR)

                            # Opcjonalnie: przenosimy z podfolderu na sam wierzch, jeśli ZIP był tak zbudowany
                            base_name = os.path.basename(extracted_path)
                            final_path = os.path.join(TARGET_DIR, base_name)
                            if extracted_path != final_path:
                                shutil.move(extracted_path, final_path)

                            extracted_count += 1
            except Exception as e:
                print(f"   [BŁĄD] Nie udało się przetworzyć paczki {filename}: {e}")

    # Czyścimy ewentualne puste podfoldery wygenerowane podczas ekstrakcji
    for root, dirs, files in os.walk(TARGET_DIR, topdown=False):
        for name in dirs:
            dir_path = os.path.join(root, name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

    print("\n[SUKCES KONSOLIDACJI]")
    print(f"-> Łącznie przeniesiono plików .aoe2record: {extracted_count}")


if __name__ == "__main__":
    merge_replays()