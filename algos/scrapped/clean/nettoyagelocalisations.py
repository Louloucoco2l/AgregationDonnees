import os
import re
import pandas as pd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "datas", "scrapped")

INPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_clean.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_clean_fina-l.csv")

print("Dossier CSV :", BASE_DIR)
print("Fichier nettoyé d'entrée :", INPUT_PATH)



if not os.path.isfile(INPUT_PATH):
    print("Fichier introuvable :", INPUT_PATH)
    raise SystemExit(1)

df = pd.read_csv(INPUT_PATH, sep=";", dtype=str)
print("Fichier chargé.")
print(f"Lignes : {len(df)}")
print()

if "localisation" not in df.columns:
    print("Colonne 'localisation' absente du fichier.")
    raise SystemExit(1)

# ================================
# 3) Fonction de normalisation
# ================================

def extraire_code_paris(val):
    """
    Retourne un code postal parisien sous la forme 75xxx.
    Exemples acceptés :
      - "75015"
      - "16ème (75)"
      - "11- philippe-auguste"
      - "3ème (75)"
      - "19- flandre - aubervilliers"
    Sinon -> None.
    """
    if pd.isna(val):
        return None

    s = str(val).strip().lower()
    if s == "":
        return None

    # 1) Si un code postal 75xxx est déjà présent
    m_code = re.search(r"\b75\d{3}\b", s)
    if m_code:
        return m_code.group().upper()

    #    ex: "16ème (75)", "5eme (75)", "11- philippe-auguste", "9- aligre"
    m_arr = re.match(r"^\s*(\d{1,2})(er|ème|eme|e)?\b", s)
    if m_arr:
        arr = int(m_arr.group(1))
        if 1 <= arr <= 20:
            return f"75{arr:03d}"

    # Rien trouvé -> pas Paris ou impossible à interpréter
    return None

# ================================
# 4) Application du nettoyage
# ================================

print("Nettoyage / normalisation de la localisation (codes 75xxx uniquement)...")
df["loc_code"] = df["localisation"].apply(extraire_code_paris)

nb_non_null = df["loc_code"].notna().sum()
print(f"Codes postaux parisiens trouvés : {nb_non_null} lignes sur {len(df)}")
print()

print("Répartition des codes postaux (loc_code) :")
print(df["loc_code"].value_counts().sort_index())
print()

# ================================
# 5) Filtrer uniquement les lignes Paris (75xxx)
# ================================

df_paris = df[df["loc_code"].notna()].copy()

# On remplace la localisation par le code propre
df_paris["localisation"] = df_paris["loc_code"]
df_paris = df_paris.drop(columns=["loc_code"])

print("Lignes conservées (Paris uniquement) :", len(df_paris))

# ================================
# 6) Export
# ================================

df_paris.to_csv(OUTPUT_PATH, sep=";", index=False, encoding="utf-8")
print("Fichier généré :", OUTPUT_PATH)
print("Terminé.")
