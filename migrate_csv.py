import csv

OLD_CSV = 'historia_ewolucji.csv'
NEW_CSV = 'historia_ewolucji.csv'

# 1. GENEROWANIE MAPOWANIA (Automatyczne na podstawie Twoich list)
# Tworzymy mapowania dla linii jednostek i technologii
mappings = {}

# Mapowanie dla linii (tłumaczenie starych nazw na mil_...)
military_lines = [
    ("militiaman-line", "infantry"), ("spearman-line", "pike"), ("archer-line", "archer"),
    ("skirmisher-line", "skirm"), ("scout-cavalry-line", "scout"), ("knight-line", "knight"),
    ("battering-ram-line", "ram"), ("mangonel-line", "mangonel"), ("trebuchet", "treb"),
    ("cavalry-archer-line", "cav_archer"), ("camel-line", "camel"), ("eagle-warrior-line", "eagle"),
    ("monk", "monk"), ("hand-cannoneer", "hc"), ("bombard-cannon", "bbc"),
    ("scorpion-line", "scorpion"), ("petard", "petard")
]

for _, name in military_lines:
    # Stare nazwy: c_few_... -> nowe: c_few_mil_...
    for prefix in ["c_few_", "c_some_", "c_many_", "c_can_train_", "a_train_"]:
        mappings[f"{prefix}{name}"] = f"{prefix}mil_{name}"

# Mapowanie dla technologii (military_techs)
military_techs = [
    ("ri-fletching", "fletching"), ("ri-bodkin-arrow", "bodkin"), ("ri-bracer", "bracer"),
    ("ri-forging", "forging"), ("ri-iron-casting", "iron_cast"), ("ri-blast-furnace", "blast"),
    ("ri-scale-mail", "scale_mail"), ("ri-chain-mail", "chain_mail"), ("ri-plate-mail", "plate_mail"),
    ("ri-long-swordsman", "long_sword"), ("ri-two-handed-swordsman", "two_hand_swordsman"),
    ("ri-champion", "champion"), ("ri-pikeman", "pikeman"), ("ri-halberdier", "halberdier"),
    ("ri-squires", "squires"), ("ri-arson", "arson"), ("ri-padded-archer-armor", "pad_archer"),
    ("ri-leather-archer-armor", "lea_archer"), ("ri-ring-archer-armor", "ring_archer"),
    ("ri-scale-barding", "scale_cav"), ("ri-chain-barding", "chain_cav"), ("ri-plate-barding", "plate_cav"),
    ("ri-crossbowman", "crossbowman"), ("ri-arbalest", "arbalest"), ("ri-elite-skirmisher", "elite_skirm"),
    ("ri-bloodlines", "bloodlines"), ("ri-husbandry", "husbandry"), ("ri-thumb-ring", "thumb_ring"),
    ("ri-parthian-tactics", "parthian"), ("ri-light-cavalry", "light_cav"), ("ri-hussar", "hussar"),
    ("ri-cavalier", "cavalier"), ("ri-paladin", "paladin"), ("ri-capped-ram", "capped_ram"),
    ("ri-siege-ram", "siege_ram"), ("ri-onager", "onager"), ("ri-siege-onager", "siege_onager"),
    ("ri-heavy-scorpion", "heavy_scorpion"), ("ri-bombard-cannon", "bombard_cannon"),
    ("ri-ballistics", "ballistics"), ("ri-chemistry", "chemistry"), ("ri-siege-engineers", "siege_eng"),
    ("ri-masonry", "masonry"), ("ri-architecture", "architecture"), ("ri-hoardings", "hoardings"),
    ("ri-conscription", "conscription"), ("ri-sappers", "sappers"), ("ri-faith", "faith"),
    ("ri-herbal-medicine", "herbal_med"), ("ri-guilds", "guilds")
]

for _, name in military_techs:
    mappings[f"c_can_res_{name}"] = f"c_can_res_mil_{name}"
    mappings[f"a_res_{name}"] = f"a_res_mil_{name}"

# 2. PROCESOWANIE TYLKO NAJNOWSZEJ GENERACJI
with open(OLD_CSV, 'r') as f_in:
    reader = list(csv.reader(f_in))
    header = reader[0]
    data = reader[1:]

if not data:
    print("[!] Plik jest pusty!")
    exit()

# Znajdź max generację
max_gen = max(int(row[0]) for row in data)
latest_generation = [row for row in data if int(row[0]) == max_gen]

# 3. ZAPIS DO NOWEGO PLIKU
with open(NEW_CSV, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(header)

    for row in latest_generation:
        gen, bot_id, score, tree_str = row
        new_tree_str = tree_str

        # Podmiana nazw
        for old_name, new_name in mappings.items():
            new_tree_str = new_tree_str.replace(old_name, new_name)

        writer.writerow([gen, bot_id, score, new_tree_str])

print(f"[*] Migracja zakończona. Przeniesiono {len(latest_generation)} botów z generacji {max_gen} do {NEW_CSV}")