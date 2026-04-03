"""
seed_v2.py — Seeds Phase 2.5 and Phase 3B AlloyDB tables.
Run once: python3 seed_v2.py
Tables created:
  - fssai_additives
  - fssai_fruit_content_rules
  - ingredient_health_map
"""

import os, sys
import sqlalchemy
from dotenv import load_dotenv
load_dotenv()

from tools.fssai_rag_tool import get_db_connection

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

FSSAI_ADDITIVES = [
    ("INS 211", "Sodium Benzoate",           "carbonated drinks, jams, squashes",       "infant food, fresh juice",          "Linked to hyperactivity in children at high doses; possible carcinogen at chronic exposure", 250),
    ("INS 102", "Tartrazine",                "confectionery, beverages, snacks",         "infant food",                       "Allergic reactions, hyperactivity in children; banned in several countries",               100),
    ("INS 110", "Sunset Yellow FCF",         "beverages, snacks, dairy",                 "infant food",                       "Hyperactivity in children; allergic reactions in aspirin-sensitive individuals",            100),
    ("INS 122", "Carmoisine",                "jams, jellies, confectionery",             "infant food",                       "Possible allergic reactions; part of the Southampton Six colours",                         100),
    ("INS 124", "Ponceau 4R",                "jelly, tinned fruit, desserts",            "infant food",                       "Hyperactivity in children; banned in USA and Norway",                                      100),
    ("INS 129", "Allura Red AC",             "beverages, snacks",                        "infant food",                       "Hyperactivity in children; one of the Southampton Six",                                    100),
    ("INS 415", "Xanthan Gum",               "sauces, dressings, dairy alternatives",    "none",                              "Generally safe at normal consumption levels; low concern",                                 None),
    ("INS 412", "Guar Gum",                  "ice cream, sauces, baked goods",           "none",                              "Generally safe; may cause bloating at very high doses",                                    None),
    ("INS 471", "Mono and Diglycerides",     "bread, margarine, confectionery",          "none",                              "Derived from animal or plant fats; generally recognised as safe",                         None),
    ("INS 322", "Lecithin",                  "chocolate, baked goods, margarine",        "none",                              "Generally safe; often soy-derived — concern for soy-allergic individuals",                 None),
    ("INS 500", "Sodium Bicarbonate",        "baked goods, confectionery",               "none",                              "Generally safe at food levels",                                                            None),
    ("INS 330", "Citric Acid",               "beverages, confectionery, preserves",      "none",                              "Generally safe; may erode tooth enamel at high frequency consumption",                    None),
    ("INS 621", "Monosodium Glutamate",      "snacks, instant noodles, sauces",          "none",                              "MSG sensitivity in susceptible individuals; no proven harm at normal doses",               None),
    ("INS 951", "Aspartame",                 "diet beverages, sugar-free products",      "phenylketonuria patients",          "Contains phenylalanine — dangerous for PKU patients; general safety debated",             None),
    ("INS 420", "Sorbitol",                  "sugar-free confectionery, baked goods",    "none",                              "Laxative effect at high doses (>20g/day); generally safe in moderation",                  None),
    ("INS 202", "Potassium Sorbate",         "cheese, wine, dried fruit",                "none",                              "Generally safe; mild antimicrobial; rare allergic reactions",                             1000),
    ("INS 220", "Sulphur Dioxide",           "wine, dried fruit, fruit juices",          "asthma patients",                   "Triggers asthma and allergic reactions in sensitive individuals",                          350),
    ("INS 250", "Sodium Nitrite",            "cured meats, processed meats",             "infant food",                       "Forms nitrosamines under high heat — possible carcinogen; WHO Group 2A",                  125),
    ("INS 407", "Carrageenan",               "dairy, infant formula, processed meats",   "inflammatory bowel disease",        "Possible gut inflammation at high doses; degraded form is carcinogenic in animal studies", None),
    ("INS 1422","Acetylated Distarch Adipate","instant noodles, sauces, frozen foods",   "none",                              "Modified starch; generally safe; high glycaemic index concern",                           None),
]

FRUIT_CONTENT_RULES = [
    ("jam",              45, "FSS (Food Products Standards) Regulation 2.4.7",  "ingredient_position"),
    ("jelly",            30, "FSS (Food Products Standards) Regulation 2.4.8",  "ingredient_position"),
    ("fruit juice",      85, "FSS (Food Products Standards) Regulation 2.3.2",  "nutrient_label"),
    ("fruit drink",      10, "FSS (Food Products Standards) Regulation 2.3.4",  "ingredient_position"),
    ("squash",           25, "FSS (Food Products Standards) Regulation 2.3.5",  "ingredient_position"),
    ("nectar",           25, "FSS (Food Products Standards) Regulation 2.3.3",  "ingredient_position"),
    ("fruit bar",        20, "FSS (Food Products Standards) Regulation 2.4.15", "ingredient_position"),
    ("marmalade",        35, "FSS (Food Products Standards) Regulation 2.4.9",  "ingredient_position"),
    ("fruit preserve",   40, "FSS (Food Products Standards) Regulation 2.4.11", "ingredient_position"),
    ("fruit chutney",    30, "FSS (Food Products Standards) Regulation 2.4.14", "ingredient_position"),
]

INGREDIENT_HEALTH_MAP = [
    ("Refined Sugar",               "Inflammation, insulin spike, rapid blood glucose rise, weight gain with excess consumption",   "Stevia, raw honey, dates paste, jaggery",           "High"),
    ("Sugar",                       "Same as refined sugar — often the primary source of empty calories in packaged foods",         "Jaggery, coconut sugar, stevia",                    "High"),
    ("Palm Oil",                    "High in saturated fat; environmental concern (deforestation); raises LDL cholesterol",         "Cold-pressed coconut oil, olive oil, mustard oil",  "Medium"),
    ("Hydrogenated Vegetable Oil",  "Trans fat source — raises LDL, lowers HDL; strongly linked to heart disease and stroke",      "Ghee, unrefined mustard oil, cold-pressed oils",    "High"),
    ("Partially Hydrogenated Oil",  "Contains trans fats even when listed as 0g — FSSAI limit is 0.2g/100g, not zero",             "Ghee, unrefined coconut oil",                       "High"),
    ("HFCS",                        "High fructose corn syrup — liver stress, obesity, metabolic syndrome, insulin resistance",     "Jaggery, coconut sugar, raw honey",                 "High"),
    ("High Fructose Corn Syrup",    "Same as HFCS",                                                                                "Jaggery, coconut sugar, raw honey",                 "High"),
    ("Maida",                       "Refined wheat flour — stripped of fibre and nutrients; high glycaemic index",                  "Whole wheat flour (atta), jowar, ragi",             "Medium"),
    ("Refined Wheat Flour",         "Same as Maida — low fibre, high GI, nutrient-poor",                                           "Whole wheat flour, multigrain flour",               "Medium"),
    ("Artificial Flavours",         "Synthetic chemicals mimicking natural flavours — long-term effects not fully studied",         "Natural extracts, real fruit/spice",                "Medium"),
    ("Artificial Colours",          "Synthetic dyes — several linked to hyperactivity in children and allergic reactions",          "Turmeric, beetroot extract, saffron",               "Medium"),
    ("INS 211",                     "Sodium Benzoate — possible carcinogen at high exposure, hyperactivity in children",            "Citric acid, salt, fermentation, vinegar",          "High"),
    ("Sodium Benzoate",             "Same as INS 211",                                                                             "Citric acid, salt, fermentation",                   "High"),
    ("INS 102",                     "Tartrazine — allergic reactions, hyperactivity in children, banned in several countries",      "Turmeric, beetroot extract",                        "Medium"),
    ("Tartrazine",                  "Same as INS 102",                                                                             "Turmeric, saffron",                                 "Medium"),
    ("INS 110",                     "Sunset Yellow — hyperactivity risk in children; Southampton Six colour",                       "Paprika extract, annatto",                          "Medium"),
    ("INS 250",                     "Sodium Nitrite — forms carcinogenic nitrosamines under heat; WHO Group 2A carcinogen",         "Sea salt, celery powder, fermentation",             "High"),
    ("Sodium Nitrite",              "Same as INS 250",                                                                             "Sea salt, celery powder",                           "High"),
    ("INS 951",                     "Aspartame — dangerous for PKU patients; controversial in broader safety debate",               "Stevia, monk fruit extract",                        "Medium"),
    ("Aspartame",                   "Same as INS 951",                                                                             "Stevia, monk fruit",                                "Medium"),
    ("Carrageenan",                 "INS 407 — possible gut inflammation; degraded form carcinogenic in animal studies",            "Agar-agar, tapioca starch",                         "Medium"),
    ("INS 407",                     "Carrageenan — gut inflammation concern at high doses",                                         "Agar-agar, tapioca starch",                         "Medium"),
    ("INS 621",                     "MSG — sensitivity in some individuals; no proven harm at normal doses",                        "Natural spices, yeast extract",                     "Low"),
    ("Monosodium Glutamate",        "Same as INS 621",                                                                             "Natural spices, herbs",                             "Low"),
    ("INS 415",                     "Xanthan Gum — generally safe at food levels; low concern",                                     "Chia seeds (in home cooking), psyllium husk",       "Low"),
    ("Xanthan Gum",                 "Same as INS 415 — generally safe",                                                            "Chia seeds, psyllium husk",                         "Low"),
    ("Acidity Regulator",           "Catch-all — specific concern depends on which acid (citric safe; phosphoric raises concern)",  "Natural acids (lemon, tamarind)",                   "Low"),
    ("Anticaking Agent",            "Prevents clumping — most are mineral salts, generally safe at food levels",                   "Arrowroot powder (in home cooking)",                "Low"),
    ("Emulsifier",                  "Keeps fat and water mixed — safety depends on specific type (lecithin safe, carrageenan not)", "Natural emulsifiers: egg yolk, mustard",            "Low"),
    ("Preservative",                "Generic label — specific risk depends on which preservative is used",                          "Fermentation, salt, vinegar, drying",               "Medium"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA + SEED
# ─────────────────────────────────────────────────────────────────────────────

def seed_v2():
    print("\n--- NutriGuard 2.0 DB Seeding ---")

    try:
        engine = get_db_connection()
        with engine.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        print("✅ AlloyDB connected.")
    except Exception as e:
        print(f"❌ AlloyDB connection failed: {e}")
        sys.exit(1)

    with engine.connect() as conn:

        # ── fssai_additives ───────────────────────────────────────────────────
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS fssai_additives (
                id                    SERIAL PRIMARY KEY,
                ins_code              VARCHAR(20)  NOT NULL UNIQUE,
                common_name           VARCHAR(100) NOT NULL,
                permitted_categories  TEXT,
                prohibited_categories TEXT,
                health_concern        TEXT,
                max_limit_ppm         FLOAT
            );
        """))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE fssai_additives RESTART IDENTITY;"))

        for row in FSSAI_ADDITIVES:
            conn.execute(sqlalchemy.text("""
                INSERT INTO fssai_additives
                    (ins_code, common_name, permitted_categories,
                     prohibited_categories, health_concern, max_limit_ppm)
                VALUES (:ins_code, :common_name, :permitted,
                        :prohibited, :concern, :limit)
            """), {
                "ins_code":   row[0],
                "common_name": row[1],
                "permitted":  row[2],
                "prohibited": row[3],
                "concern":    row[4],
                "limit":      row[5],
            })

        print(f"✅ fssai_additives — {len(FSSAI_ADDITIVES)} rows inserted.")

        # ── fssai_fruit_content_rules ─────────────────────────────────────────
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS fssai_fruit_content_rules (
                id                SERIAL PRIMARY KEY,
                product_category  VARCHAR(100) NOT NULL UNIQUE,
                min_fruit_pct     FLOAT        NOT NULL,
                regulation_ref    TEXT,
                detection_method  VARCHAR(50)
            );
        """))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE fssai_fruit_content_rules RESTART IDENTITY;"))

        for row in FRUIT_CONTENT_RULES:
            conn.execute(sqlalchemy.text("""
                INSERT INTO fssai_fruit_content_rules
                    (product_category, min_fruit_pct, regulation_ref, detection_method)
                VALUES (:cat, :pct, :ref, :method)
            """), {
                "cat":    row[0],
                "pct":    row[1],
                "ref":    row[2],
                "method": row[3],
            })

        print(f"✅ fssai_fruit_content_rules — {len(FRUIT_CONTENT_RULES)} rows inserted.")

        # ── ingredient_health_map ─────────────────────────────────────────────
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS ingredient_health_map (
                id                  SERIAL PRIMARY KEY,
                ingredient_name     VARCHAR(100) NOT NULL UNIQUE,
                health_concern      TEXT,
                natural_alternative TEXT,
                risk_level          VARCHAR(10)  NOT NULL
            );
        """))
        conn.execute(sqlalchemy.text("TRUNCATE TABLE ingredient_health_map RESTART IDENTITY;"))

        for row in INGREDIENT_HEALTH_MAP:
            conn.execute(sqlalchemy.text("""
                INSERT INTO ingredient_health_map
                    (ingredient_name, health_concern, natural_alternative, risk_level)
                VALUES (:name, :concern, :alt, :risk)
            """), {
                "name":    row[0],
                "concern": row[1],
                "alt":     row[2],
                "risk":    row[3],
            })

        print(f"✅ ingredient_health_map — {len(INGREDIENT_HEALTH_MAP)} rows inserted.")

        conn.commit()

    print("\n🎉 seed_v2.py complete. Run your pipeline — new tables are ready.")
    print("   Next: python3 app.py data/test_label.jpg")


if __name__ == "__main__":
    seed_v2()