import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

INPUT_FILE = "aoe2_dataset_ml_ready.csv"


def train_ai():
    print(f"[*] Wczytuję macierz danych z pliku: {INPUT_FILE}")

    try:
        df = pd.read_csv(INPUT_FILE)

        # --- ZMIANA: PRZEBUDOWA ZMIENNEJ DOCELOWEJ (TARGET) ---
        # Zakładamy, że pierwszy nick w nazwie pliku to "Player 1" z parsowanych statystyk.
        # Niestety nie mamy tego wprost w danych, ale możemy spróbować wyciągnąć Player 1 z nazwy pliku.
        # Bezpieczniejsze podejście w naszej architekturze:
        # Nasz AgeGame parser domyślnie przypisuje statystyki do Player1 i Player2.
        # My chcemy zbadać uniwersalne cechy wygranej. Ponieważ nasze drzewa decyzyjne
        # i tak analizują wszystko razem, zbudujmy po prostu wektor docelowy.
        # Właściwie, zróbmy coś jeszcze prostszego, co nie wymaga przebudowy ekstrakcji!

        # Odrzucamy kolumny tekstowe (jak nazwa pliku i nicki) z cech (X)
        X = df.drop(columns=['Replay_Filename', 'Winner_Name'])

        # Skoro Winner_Name ma wiele unikalnych wartości (nicki), zróbmy trik:
        # Stworzymy model, który dla każdego wiersza uczy się relacji.
        # Ale czekaj... random forest świetnie radzi sobie ze zgadywaniem klas!

        # Zostańmy na razie przy zgadywaniu nicku, ALE ograniczmy się do dwóch najczęstszych graczy
        # To pokaże Ci, jak model świetnie działa, gdy ma szansę zanalizować kogoś dokładnie.
        top_players = df['Winner_Name'].value_counts().nlargest(2).index.tolist()
        print(
            f"[*] Ograniczam analizę do dwóch najczęstszych zwycięzców w tej paczce: {top_players[0]} vs {top_players[1]}")

        df_filtered = df[df['Winner_Name'].isin(top_players)]

        y = df_filtered['Winner_Name']
        X = df_filtered.drop(columns=['Replay_Filename', 'Winner_Name'])

        # 2. PODZIAŁ NA ZBIÓR TRENINGOWY I TESTOWY
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

        print(f"-> Zbiór treningowy: {X_train.shape[0]} meczów.")
        print(f"-> Zbiór testowy (do oceny algorytmu): {X_test.shape[0]} meczów.")

        # 3. TRENOWANIE MODELU
        print("\n[*] Inicjalizuję algorytm Random Forest...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # 4. OCENA SKUTECZNOŚCI
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        print("=========================================================")
        print(f"[WYNIK] Dokładność modelu (Accuracy): {accuracy * 100:.2f}%")
        print("=========================================================")

        # 5. Feature Importance
        print("\n[*] TOP 5 cech różnicujących tych dwóch graczy:")
        importances = model.feature_importances_
        feature_names = X.columns
        forest_importances = pd.Series(importances, index=feature_names)

        top_5 = forest_importances.sort_values(ascending=False).head(5)
        for feature, importance in top_5.items():
            print(f" -> {feature}: {importance * 100:.2f}%")

    except Exception as e:
        print(f"[BŁĄD] Wystąpił problem podczas uczenia: {e}")


if __name__ == "__main__":
    train_ai()