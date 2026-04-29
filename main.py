import os
import pandas as pd
from agealyser import AgeGame
import mgz.summary

REPLAYS_DIR = "replays"
OUTPUT_FILE = "aoe2_dataset.csv"


def build_dataset():
    print(f"[*] Rozpoczynam budowę potoku danych z ekstrakcją Zwycięzcy...")

    if not os.path.exists(REPLAYS_DIR):
        os.makedirs(REPLAYS_DIR)
        return

    all_replays_data = []
    files_processed = 0
    files_failed = 0

    for filename in os.listdir(REPLAYS_DIR):
        if not filename.endswith(".aoe2record"):
            continue

        file_path = os.path.join(REPLAYS_DIR, filename)
        print(f"-> Analizuję mecz: {filename}...")

        try:
            # 1. NAPRAWIONA WYCIĄGANIE ZWYCIĘZCY
            winner_name = "Unknown"
            with open(file_path, 'rb') as f:
                match_summary = mgz.summary.Summary(f)

                # Przeszukujemy listę graczy i szukamy flagi 'winner'
                for player in match_summary.get_players():
                    if player.get('winner'):
                        winner_name = player.get('name')
                        break

            # 2. WYCIĄGANIE STATYSTYK (age-alyser)
            game = AgeGame(file_path)
            raw_data = game.advanced_parser()

            # 3. STANDARYZACJA DO DATAFRAME
            if isinstance(raw_data, pd.Series):
                row_df = raw_data.to_frame().T
            elif isinstance(raw_data, dict):
                row_df = pd.DataFrame([raw_data])
            elif isinstance(raw_data, pd.DataFrame):
                row_df = raw_data.head(1)
            else:
                raise ValueError("Nieznany format wyjściowy z parsera.")

            # 4. DODAWANIE KLUCZOWYCH KOLUMN
            row_df.insert(0, 'Replay_Filename', filename)
            row_df.insert(1, 'Winner_Name', winner_name)  # NASZ TARGET DO ML!

            all_replays_data.append(row_df)
            files_processed += 1

        except Exception as e:
            print(f"   [BŁĄD] Plik {filename} odrzucony: {e}")
            files_failed += 1

    # 5. ZAPIS DO PLIKU
    if all_replays_data:
        print("\n[*] Łączenie danych w główny zbiór (Dataset)...")
        final_dataset = pd.concat(all_replays_data, ignore_index=True)
        final_dataset.to_csv(OUTPUT_FILE, index=False)

        print("\n[SUKCES POTOKU DANYCH]")
        print("=========================================================")
        print(f"-> Pomyślnie przetworzono: {files_processed} plików.")
        print(f"-> Odrzucono z błędami: {files_failed} plików.")
        print(f"-> Zapisano jako: {OUTPUT_FILE}")
        print(f"-> Nowy kształt macierzy ML: {final_dataset.shape} (Dodano Target!)")
        print("=========================================================\n")


if __name__ == "__main__":
    build_dataset()