import pandas as pd
import matplotlib.pyplot as plt
import csv

# Bezpieczne ładowanie omijające uszkodzone linie (np. linię 57)
rows = []
with open('historia_ewolucji.csv', 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) == len(header): # Odrzucamy uszkodzone wiersze
            rows.append(row)

df = pd.DataFrame(rows, columns=header)
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()

# Obliczanie średnich dla każdej generacji
gen_stats = df.groupby('Generacja').agg(
    avg_score=('Punkty', 'mean'),
    max_score=('Punkty', 'max'),
    avg_siege=('build_siege', 'mean')
).reset_index()

# Rysowanie wykresu
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(gen_stats['Generacja'], gen_stats['avg_score'], color='blue', label='Średnie Punkty', linewidth=2)
ax1.plot(gen_stats['Generacja'], gen_stats['max_score'], color='red', label='Mistrz (Max)', linewidth=2, linestyle='--')
ax1.set_xlabel('Generacja', fontsize=12)
ax1.set_ylabel('Punkty KDA', color='black', fontsize=12)
ax1.tick_params(axis='y', labelcolor='black')
ax1.legend(loc='upper left')

# Druga oś Y dla Warsztatów
ax2 = ax1.twinx()
ax2.plot(gen_stats['Generacja'], gen_stats['avg_siege'] * 100, color='purple', label='% Botów z Warsztatem', linewidth=3)
ax2.set_ylabel('% Posiadania Warsztatu', color='purple', fontsize=12)
ax2.tick_params(axis='y', labelcolor='purple')
ax2.set_ylim(0, 100)
ax2.legend(loc='upper right')

plt.title('Zanikanie Warsztatów Oblężniczych w Ewolucji', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()