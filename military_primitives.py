def add_military_nodes(pset, Condition, Action):
    # ==========================================
    # MODUŁ WOJSKOWY (Military & Siege)
    # ==========================================

    # --- 1. Szkolenie Jednostek (Wszystkie kluczowe linie wojskowe) ---
    military_lines = [
        ("militiaman-line", "infantry"),  # Piechota (Militia -> Champion)
        ("spearman-line", "pike"),  # Antykawaleria (Spearman -> Halberdier)
        ("archer-line", "archer"),  # Łucznicy (Archer -> Arbalest)
        ("skirmisher-line", "skirm"),  # Anty-łucznicy (Skirmisher -> Elite)
        ("scout-cavalry-line", "scout"),  # Zwiad / Lekka jazda
        ("knight-line", "knight"),  # Ciężka jazda (Knight -> Paladin)
        ("battering-ram-line", "ram"),  # Tarany
        ("mangonel-line", "mangonel"),  # Katapulty (Mangonel -> Siege Onager)
        ("trebuchet", "treb")  # Trebusze
    ]

    for unit, name in military_lines:
        # Warunki: Kontrolowanie wielkości poszczególnych oddziałów
        pset.addTerminal(f"(unit-type-count {unit} < 5)", Condition, name=f"c_few_{name}")
        pset.addTerminal(f"(unit-type-count {unit} < 15)", Condition, name=f"c_some_{name}")
        pset.addTerminal(f"(unit-type-count {unit} < 30)", Condition, name=f"c_many_{name}")

        # Akcje: Produkcja jednostek
        pset.addTerminal(f"(train {unit})", Action, name=f"a_train_{name}")

    # --- 2. Zwiad i Wywiad (Reagowanie na armię wroga) ---
    enemy_threats = [
        ("knight-line", "knight"),
        ("archer-line", "archer"),
        ("militiaman-line", "infantry"),
        ("spearman-line", "pike")
    ]
    for threat, name in enemy_threats:
        # Bot potrafi teraz zauważyć kompozycję armii wroga!
        pset.addTerminal(f"(players-unit-type-count any-enemy {threat} > 5)", Condition, name=f"c_enemy_has_few_{name}")
        pset.addTerminal(f"(players-unit-type-count any-enemy {threat} > 15)", Condition,
                         name=f"c_enemy_has_many_{name}")

    # --- 3. Badania Wojskowe (Kuźnia, Uniwersytet) ---
    military_techs = [
        ("ri-fletching", "fletching"), ("ri-bodkin-arrow", "bodkin"), ("ri-bracer", "bracer"),  # Atak łuczników
        ("ri-forging", "forging"), ("ri-iron-casting", "iron_cast"), ("ri-blast-furnace", "blast"),  # Atak wręcz
        ("ri-scale-mail", "scale_mail"), ("ri-chain-mail", "chain_mail"),  # Pancerz piechoty
        ("ri-ballistics", "ballistics"), ("ri-chemistry", "chemistry")  # Uniwersytet
    ]
    for tech, name in military_techs:
        pset.addTerminal(f"(can-research {tech})", Condition, name=f"c_can_res_{name}")
        pset.addTerminal(f"(research {tech})", Action, name=f"a_res_{name}")

    # --- 4. Podstawowe komendy ataku (Makrozarządzanie) ---
    pset.addTerminal("(military-population > 10)", Condition, name="c_mil_pop_10")
    pset.addTerminal("(military-population > 30)", Condition, name="c_mil_pop_30")
    pset.addTerminal("(military-population > 50)", Condition, name="c_mil_pop_50")

    pset.addTerminal("(attack-now)", Action, name="a_attack_now")

    return pset