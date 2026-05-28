def add_military_nodes(pset, Condition, Action):
    # ==========================================
    # MODUŁ WOJSKOWY (Military & Siege)
    # ==========================================

    military_lines = [
        ("militiaman-line", "infantry"),
        ("spearman-line", "pike"),
        ("archer-line", "archer"),
        ("skirmisher-line", "skirm"),
        ("scout-cavalry-line", "scout"),
        ("knight-line", "knight"),
        ("battering-ram-line", "ram"),
        ("mangonel-line", "mangonel"),
        ("trebuchet", "treb"),
        ("cavalry-archer-line", "cav_archer"), ("camel-line", "camel"),
        ("eagle-warrior-line", "eagle"), ("monk", "monk"),
        ("hand-cannoneer", "hc"), ("bombard-cannon", "bbc"),
        ("scorpion-line", "scorpion"), ("petard", "petard")
    ]

    for unit, name in military_lines:
        pset.addTerminal(f"(unit-type-count {unit} < 5)", Condition, name=f"c_few_mil_{name}")
        pset.addTerminal(f"(unit-type-count {unit} < 15)", Condition, name=f"c_some_mil_{name}")
        pset.addTerminal(f"(unit-type-count {unit} < 30)", Condition, name=f"c_many_mil_{name}")
        pset.addTerminal(f"(unit-type-count {unit} > 0)", Condition, name=f"c_has_mil_{name}")

        pset.addTerminal(f"(can-train {unit})", Condition, name=f"c_can_train_mil_{name}")

        pset.addTerminal(f"(train {unit})", Action, name=f"a_train_mil_{name}")

    enemy_threats = [
        ("knight-line", "knight"),
        ("archer-line", "archer"),
        ("militiaman-line", "infantry"),
        ("spearman-line", "pike")
    ]
    for threat, name in enemy_threats:
        pset.addTerminal(f"(players-unit-type-count any-enemy {threat} > 5)", Condition, name=f"c_enemy_has_few_{name}")
        pset.addTerminal(f"(players-unit-type-count any-enemy {threat} > 15)", Condition,
                         name=f"c_enemy_has_many_{name}")

    military_techs = [
        ("ri-fletching", "fletching"), ("ri-bodkin-arrow", "bodkin"), ("ri-bracer", "bracer"),
        ("ri-forging", "forging"), ("ri-iron-casting", "iron_cast"), ("ri-blast-furnace", "blast"),
        ("ri-scale-mail", "scale_mail"), ("ri-chain-mail", "chain_mail"), ("ri-plate-mail", "plate_mail"),
        ("ri-man-at-arms", "man_at_arms"),  # <-- DODANE TUTAJ
        ("ri-long-swordsman", "long_sword"),
        ("ri-two-handed-swordsman", "two_hand_swordsman"),
        ("ri-champion", "champion"),
        ("ri-pikeman", "pikeman"),
        ("ri-halberdier", "halberdier"),
        ("ri-squires", "squires"),
        ("ri-padded-archer-armor", "pad_archer"), ("ri-leather-archer-armor", "lea_archer"),
        ("ri-ring-archer-armor", "ring_archer"),
        ("ri-scale-barding", "scale_cav"), ("ri-chain-barding", "chain_cav"), ("ri-plate-barding", "plate_cav"),
        ("ri-crossbow", "crossbow"),
        ("ri-arbalest", "arbalest"),
        ("ri-elite-skirmisher", "elite_skirm"),
        ("ri-bloodlines", "bloodlines"), ("ri-husbandry", "husbandry"),
        ("ri-thumb-ring", "thumb_ring"), ("ri-parthian-tactics", "parthian"),
        ("ri-light-cavalry", "light_cav"),
        ("ri-hussar", "hussar"),
        ("ri-cavalier", "cavalier"),
        ("ri-paladin", "paladin"),
        ("ri-capped-ram", "capped_ram"),
        ("ri-siege-ram", "siege_ram"),
        ("ri-onager", "onager"),
        ("ri-siege-onager", "siege_onager"),
        ("ri-heavy-scorpion", "heavy_scorpion"),
        ("ri-bombard-cannon", "bombard_cannon"),
        ("ri-ballistics", "ballistics"), ("ri-chemistry", "chemistry"), ("ri-siege-engineers", "siege_eng"),
        ("ri-masonry", "masonry"), ("ri-architecture", "architecture"), ("ri-hoardings", "hoardings"),
        ("ri-conscription", "conscription"),
        ("ri-sappers", "sappers"),
        ("ri-faith", "faith"),
        ("ri-guilds", "guilds")
    ]

    unique_techs = list(dict.fromkeys(military_techs))
    for tech, name in unique_techs:
        term_name = f"c_can_res_mil_{name}"
        act_name = f"a_res_mil_{name}"
        if term_name not in pset.context:
            pset.addTerminal(f"(can-research {tech})", Condition, name=term_name)
        if act_name not in pset.context:
            pset.addTerminal(f"(research {tech})", Action, name=act_name)

    pset.addTerminal("(military-population > 10)", Condition, name="c_mil_pop_10")
    pset.addTerminal("(military-population > 30)", Condition, name="c_mil_pop_30")
    pset.addTerminal("(military-population > 50)", Condition, name="c_mil_pop_50")
    pset.addTerminal("(attack-now)", Action, name="a_attack_now")

    if "c_few_mil_archery_range" not in pset.context:
        pset.addTerminal("(building-type-count archery-range < 5)", Condition, name="c_few_mil_archery_range")
        pset.addTerminal("(building-type-count archery-range < 15)", Condition, name="c_some_mil_archery_range")
        pset.addTerminal("(building-type-count archery-range < 30)", Condition, name="c_many_mil_archery_range")
        pset.addTerminal("(building-type-count archery-range > 0)", Condition, name="c_has_mil_archery_range")
        pset.addTerminal("(can-build archery-range)", Condition, name="c_can_train_mil_archery_range")
        pset.addTerminal("(build archery-range)", Action, name="a_train_mil_archery_range")

    if "c_can_res_mil_crossbowman" not in pset.context:
        pset.addTerminal("(can-research ri-crossbow)", Condition, name="c_can_res_mil_crossbowman")
        pset.addTerminal("(research ri-crossbow)", Action, name="a_res_mil_crossbowman")

    if "c_can_res_mil_arson" not in pset.context:
        pset.addTerminal("(false)", Condition, name="c_can_res_mil_arson")
        pset.addTerminal("(do-nothing)", Action, name="a_res_mil_arson")

    if "c_can_res_mil_herbal_med" not in pset.context:
        pset.addTerminal("(false)", Condition, name="c_can_res_mil_herbal_med")
        pset.addTerminal("(do-nothing)", Action, name="a_res_mil_herbal_med")

    return pset