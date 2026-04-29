import pandas as pd
import numpy as np

# Konfiguracja wejścia / wyjścia
INPUT_FILE = "aoe2_dataset.csv"
OUTPUT_FILE = "aoe2_dataset_ml_ready.csv"


def clean_dataset():
    print(f"[*] Rozpoczynam inżynierię cech i czyszczenie danych na pliku: {INPUT_FILE}")

    try:
        # 1. WCZYTANIE DANYCH
        df = pd.read_csv(INPUT_FILE)
        print(f"-> Kształt wejściowy: {df.shape}")

        # Usuwamy mecze bez wyraźnego zwycięzcy (jeśli takie się pojawiły)
        if 'Winner_Name' in df.columns:
            df = df[df['Winner_Name'] != 'Unknown']

        # 2. PRZETWARZANIE CZASU
        # Szukamy kolumn, które zawierają w nazwie 'Time'
        time_columns = [col for col in df.columns if 'Time' in col]

        for col in time_columns:
            # Rzutujemy teksty na obiekt Timedelta, a potem wyciągamy same sekundy
            df[col] = pd.to_timedelta(df[col]).dt.total_seconds()

        print(f"-> Przekonwertowano {len(time_columns)} kolumn czasowych na twarde sekundy.")

        # 3. OBSŁUGA BRAKÓW DANYCH (NaN)
        # Dla czasów: -1 oznacza "nie wystąpiło"
        df[time_columns] = df[time_columns].fillna(-1)

        # Dla pozostałych cech numerycznych (np. liczba jednostek): 0 oznacza "brak jednostek"
        num_cols = df.select_dtypes(include=[np.number]).columns
        df[num_cols] = df[num_cols].fillna(0)

        print("-> Wypełniono puste wartości (NaN).")

        # 4. KODOWANIE ZMIENNYCH KATEGORYCZNYCH (One-Hot Encoding)
        # Szukamy kolumn tekstowych, ale omijamy te, których nie chcemy zakodować jako zera i jedynki
        text_cols = df.select_dtypes(include=['object']).columns
        cols_to_encode = [c for c in text_cols if c not in ['Replay_Filename', 'Winner_Name']]

        # Magiczna funkcja get_dummies zamienia wartości tekstowe na macierz 0/1
        df = pd.get_dummies(df, columns=cols_to_encode)

        # get_dummies domyślnie rzuca typ boolean (True/False). Rzutujemy go na int (1/0)
        bool_cols = df.select_dtypes(include=['bool']).columns
        df[bool_cols] = df[bool_cols].astype(int)

        print(f"-> Wykonano transformację One-Hot Encoding dla {len(cols_to_encode)} zmiennych.")

        # 5. OSTATECZNY ZAPIS
        df.to_csv(OUTPUT_FILE, index=False)

        print("\n[SUKCES CZYSZCZENIA DANYCH]")
        print("=========================================================")
        print(f"-> Zapisano docelowy plik: {OUTPUT_FILE}")
        print(f"-> Nowy kształt macierzy ML: {df.shape}")
        print("=========================================================\n")

    except FileNotFoundError:
        print(f"[BŁĄD] Nie znaleziono pliku {INPUT_FILE}. Upewnij się, że uruchomiłeś najpierw main.py!")
    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Coś poszło nie tak podczas transformacji: {e}")


if __name__ == "__main__":
    clean_dataset()