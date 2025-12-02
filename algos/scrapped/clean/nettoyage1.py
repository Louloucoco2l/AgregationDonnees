import os
import glob
import pandas as pd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# Puis on va dans datas/old_dataset/scrapped
BASE_DIR = os.path.join(PROJECT_ROOT, "datas", "scrapped")

print("Dossier CSV :", BASE_DIR)

pattern = os.path.join(BASE_DIR, "annonces_*_paris*.csv")
files = glob.glob(pattern)

if not files:
    print("Aucun fichier trouvé dans :", pattern)
else:
    print(" Fichiers trouvés :")
    for f in files:
        print(" -", os.path.basename(f))


COLUMNS = ["type", "prix", "prix_m2", "surface", "nb_pieces", "localisation", "details"]

all_dfs = []

for path in files:
    print("\n=== Traitement :", os.path.basename(path), "===")
    df = pd.read_csv(path)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Forcer ordre + colonnes
    df = df[COLUMNS]

    # Trouver la source
    name = os.path.basename(path).lower()
    if "orpi" in name:
        source = "orpi"
    elif "laforet" in name:
        source = "laforet"
    elif "century21" in name:
        source = "century21"
    elif "plaza" in name:
        source = "stephane_plaza"
    elif "lefigaro" in name:
        source = "lefigaro"
    else:
        source = "autre"

    df["source"] = source

    print(" →", len(df), "lignes")
    all_dfs.append(df)


if all_dfs:
    df_final = pd.concat(all_dfs, ignore_index=True)

    output_path = os.path.join(BASE_DIR, "annonces_paris_fusion_brut.csv")
    df_final.to_csv(output_path, sep=";", index=False, encoding="utf-8")

    print("\n======================================")
    print(" Fusion terminée !")
    print("Total lignes :", len(df_final))
    print("Fichier créé :", output_path)
    print("======================================")
else:
    print(" Aucun dataframe à fusionner.")
