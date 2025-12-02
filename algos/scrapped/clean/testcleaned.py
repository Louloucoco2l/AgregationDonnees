import os
import pandas as pd



CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "datas", "scrapped")

INPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_clean_final.csv")

print("Dossier CSV :", BASE_DIR)
print("Fichier nettoyé :", INPUT_PATH)


if not os.path.isfile(INPUT_PATH):
    print(" Fichier introuvable :", INPUT_PATH)
    raise SystemExit(1)

df = pd.read_csv(INPUT_PATH, sep=";", dtype=str)
print("\nFichier chargé.")
print(f"→ {len(df)} lignes, {len(df.columns)} colonnes.\n")

# ================================
# 3) Colonnes
# ================================

print("Colonnes présentes :")
for col in df.columns:
    print(" -", col)
print()

# ================================
# 4) Valeurs manquantes / spéciales
# ================================

print("Valeurs manquantes / spéciales :")

for col in df.columns:

    serie = df[col]

    # NaN pandas
    nan_count = serie.isna().sum()

    # Valeurs vides ""
    empty_count = (serie == "").sum()

    
    low = serie.str.lower().fillna("")

    # "non disponible"
    non_dispo = low.str.contains("non disponible").sum()

    # "null" / "none"
    null_txt = low.isin(["null", "none"]).sum()

    print(
        f" - {col:15s} : "
        f"{nan_count:5d} NaN | "
        f"{empty_count:5d} vides | "
        f"{non_dispo:5d} 'non dispo' | "
        f"{null_txt:5d} null/none"
    )
print()


print("Aperçu des 5 premières lignes :")
print(df.head(5))
print()

# Convertir colonnes numériques pour les stats
for col in ["prix", "surface", "prix_m2"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ================================
# 6) Statistiques numériques
# ================================

print("Statistiques (prix / surface / prix_m2) :")
colonnes_num = [c for c in ["prix", "surface", "prix_m2"] if c in df.columns]
print(df[colonnes_num].describe())
print()

# ================================
# 7) Répartition type
# ================================

if "type" in df.columns:
    print("Répartition par type (top 20) :")
    print(df["type"].value_counts().head(20))
    print()

# ================================
# 8) Répartition source
# ================================

if "source" in df.columns:
    print("Répartition par source :")
    print(df["source"].value_counts())
    print()

# ================================
# 9) Répartition localisation
# ================================

if "localisation" in df.columns:
    print("Répartition par localisation  :")
    pd.set_option("display.max_rows", None)  
    print(df["localisation"].value_counts())
    print()
else:
    print("Colonne 'localisation' absente.\n")
# ================================
# 10) Exemples de details
# ================================

if "details" in df.columns:
    print("Exemples de descriptions (details) :")
    details = df["details"].dropna()
    details = details[details != ""].head(5)
    for i, txt in enumerate(details, 1):
        print(f"{i}. {txt}")
    print()

print("Analyse terminée.")
