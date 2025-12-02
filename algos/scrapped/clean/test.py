import os
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "datas", "scrapped")

INPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_fusion_brut.csv")

print("Dossier CSV :", BASE_DIR)
print("Fichier fusion :", INPUT_PATH)

if not os.path.isfile(INPUT_PATH):
    print(" Fichier introuvable :", INPUT_PATH)
    raise SystemExit(1)

print("\nChargement du fichier...")
df = pd.read_csv(INPUT_PATH, sep=";", dtype=str)
print("✓ Fichier chargé.")
print(f"→ {len(df)} lignes, {len(df.columns)} colonnes.\n")

print(" Liste des colonnes :")
for col in df.columns:
    print(" -", col)
print()

# ================================
# Valeurs manquantes détaillées
# ================================
print(" Valeurs manquantes / problématiques par colonne :")
for col in df.columns:
    serie = df[col]

    nb_nan = serie.isna().sum()  # NaN 
    nb_empty = (serie == "").sum()  # chaînes vides
    lower = serie.str.lower().fillna("")

    nb_non_dispo = lower.str.contains("non disponible").sum()
    nb_null_text = lower.isin(["null", "none"]).sum()

    print(
        f" - {col:15s} : "
        f"{nb_nan:6d} NaN  | "
        f"{nb_empty:6d} vides  | "
        f"{nb_non_dispo:6d} 'non dispo' | "
        f"{nb_null_text:6d} 'null/none'"
    )
print()

print("Aperçu des 5 premières lignes :")
print(df.head(5))
print()

if "type" in df.columns:
    print(" Répartition par type de bien :")
    print(df["type"].value_counts().head(30))
    print()
else:
    print(" Colonne 'type' absente.\n")

if "source" in df.columns:
    print(" Répartition par source :")
    print(df["source"].value_counts())
    print()
else:
    print(" Colonne 'source' absente.\n")

if "details" in df.columns:
    nb_null_details = df["details"].isna().sum()
    nb_vide_details = (df["details"] == "").sum()
    print(" Colonne 'details' :")
    print(f" - NaN   : {nb_null_details}")
    print(f" - Vides : {nb_vide_details}")
    print("\nExemples de 'details' non vides :")
    exemples = df["details"].dropna()
    exemples = exemples[exemples != ""].head(5)
    for i, texte in enumerate(exemples, start=1):
        print(f"  {i}. {texte}")
    print()
else:
    print(" Colonne 'details' absente.\n")

print(" Fin des tests simples sur la table de fusion.")
