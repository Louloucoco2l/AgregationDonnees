import os
import re
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "datas", "scrapped")

INPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_fusion_brut.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "annonces_paris_clean.csv")

print("Dossier CSV :", BASE_DIR)
print("Fichier fusion :", INPUT_PATH)


if not os.path.isfile(INPUT_PATH):
    print("Fichier introuvable :", INPUT_PATH)
    raise SystemExit(1)

print("Chargement du fichier...")
df = pd.read_csv(INPUT_PATH, sep=";", dtype=str)
print("Lignes chargées :", len(df))


for col in ["type", "prix", "prix_m2", "surface", "nb_pieces", "localisation", "details", "source"]:
    if col not in df.columns:
        df[col] = None

# ================================
#  Fonctions de nettoyage
# ================================

def clean_prix(val):
    """Nettoie la colonne prix: '509 000 €' -> 509000.0"""
    if pd.isna(val):
        return None
    s = str(val).lower().strip().replace("\xa0", " ")
    if "non disponible" in s:
        return None
    if "€" in s:
        s = s.split("€")[0]
    s = s.replace(" ", "").replace(",", ".")
    digits = "".join(c for c in s if c.isdigit() or c == ".")
    return float(digits) if digits else None

def clean_surface(val):
    """Nettoie la surface: '71 m²' -> 71.0"""
    if pd.isna(val):
        return None
    s = str(val).lower().strip().replace("\xa0", " ")
    if "non disponible" in s:
        return None
    for token in ["m²", "m2", " m", "m"]:
        s = s.replace(token, "")
    s = s.replace(" ", "").replace(",", ".")
    digits = "".join(c for c in s if c.isdigit() or c == ".")
    return float(digits) if digits else None

def clean_prix_m2(val):
    """Nettoie le prix/m² si déjà présent."""
    if pd.isna(val):
        return None
    s = str(val).lower().strip().replace("\xa0", " ")
    if "non disponible" in s:
        return None
    for token in ["soit", "/m2", "/m²", "/ m2", "/ m²"]:
        s = s.replace(token, "")
    if "€" in s:
        s = s.split("€")[0]
    s = s.replace(" ", "").replace(",", ".")
    digits = "".join(c for c in s if c.isdigit() or c == ".")
    return float(digits) if digits else None

def clean_type(val_type, val_details):
    """
    Nettoyage simple de type:
    - 'Appartement F3 à vendre' -> 'Appartement'
    - si type = vide / non disponible, on regarde 'details'
    """
    t = "" if pd.isna(val_type) else str(val_type).lower().strip()
    d = "" if pd.isna(val_details) else str(val_details).lower().strip()

    # Si type contient appartement
    if "appartement" in t or "appart" in t:
        return "Appartement"

    # Si type vide ou non dispo -> on regarde la description
    if t == "" or "non disponible" in t or "à vendre" in t or "a vendre" in t:
        if "appartement" in d or "appart" in d:
            return "Appartement"
        return None

    # Sinon: on coupe avant " à " si présent
    if " à " in t:
        t = t.split(" à ")[0].strip()
    elif " a " in t:
        t = t.split(" a ")[0].strip()

    if t:
        return t.capitalize()
    return None

def clean_nb_pieces(val):
    """Extrait le premier nombre: '3 pièces' -> 3, 'T4 (4 pièces)' -> 4."""
    if pd.isna(val):
        return None
    s = str(val).lower()
    m = re.search(r"\d+", s)
    if not m:
        return None
    try:
        return int(m.group())
    except ValueError:
        return None

def clean_localisation(val):
    """
    - Si un code postal 75xxx est présent, on garde juste ça (ex: '75013')
    - Sinon, on enlève 'paris' et on garde le reste
    """
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "":
        return None

    s_lower = s.lower()

    # Chercher un code postal 75xxx
    m = re.search(r"\b75\d{3}\b", s_lower)
    if m:
        return m.group().upper()

    # Sinon, enlever 'paris'
    s_no_paris = s_lower.replace("paris", "").strip()
    if s_no_paris == "":
        return None

    return s_no_paris.capitalize()

# ================================
# 4) Nettoyage de TYPE
# ================================

print("Nettoyage de la colonne type...")
df["type"] = df.apply(lambda row: clean_type(row["type"], row["details"]), axis=1)

# Corrections supplémentaires simples sur type
print("Corrections supplémentaires sur la colonne type...")

type_lower = df["type"].str.lower().fillna("")

# duplex -> Appartement
df.loc[type_lower.str.contains("duplex"), "type"] = "Appartement"

# loft -> Appartement
df.loc[type_lower.str.contains("loft"), "type"] = "Appartement"

# maison neuve / maisson neuve -> Maison
df.loc[
    type_lower.str.contains("maison neuve") | type_lower.str.contains("maisson neuve"),
    "type"
] = "Maison"

# locaux professionnels -> Locaux
df.loc[
    type_lower.str.contains("locaux") & type_lower.str.contains("profession"),
    "type"
] = "Locaux"

# péniche, viager, hôtel, immeuble, propriété -> suppression des lignes
mask_a_supprimer = (
    type_lower.str.contains("peniche")
    | type_lower.str.contains("péniche")
    | type_lower.str.contains("viager")
    | type_lower.str.contains("hotel")
    | type_lower.str.contains("hôtel")
    | type_lower.str.contains("immeuble")
    | type_lower.str.contains("propriet")
    | type_lower.str.contains("propriét")
)

nb_suppr = mask_a_supprimer.sum()
print("Lignes supprimées (peniche/viager/hotel/immeuble/propriete) :", nb_suppr)
df = df[~mask_a_supprimer]


print("Suppression des lignes avec type vide ou NaN...")
avant = len(df)

df = df[df["type"].notna()]               # supprime NaN
df = df[df["type"].str.strip() != ""]     # supprime ""

apres = len(df)
print("Lignes supprimées pour type manquant :", avant - apres)

# ================================
# 5) Nettoyage de nb_pieces et localisation
# ================================

print("Nettoyage de nb_pieces...")
df["nb_pieces_num"] = df["nb_pieces"].apply(clean_nb_pieces)

print("Nettoyage de localisation...")
df["localisation_clean"] = df["localisation"].apply(clean_localisation)

# ================================
# 6) Nettoyage prix, surface, prix_m2
# ================================

print("Nettoyage prix, surface, prix_m2...")

df["prix_num"] = df["prix"].apply(clean_prix)
df["surface_num"] = df["surface"].apply(clean_surface)
df["prix_m2_num"] = df["prix_m2"].apply(clean_prix_m2)

# Calcul de prix/m² manquant à partir de prix et surface
mask_calc = (
    df["prix_m2_num"].isna()
    & df["prix_num"].notna()
    & df["surface_num"].notna()
    & (df["surface_num"] > 0)
)
df.loc[mask_calc, "prix_m2_num"] = df.loc[mask_calc, "prix_num"] / df.loc[mask_calc, "surface_num"]

# Arrondir prix/m² à 2 décimales
df["prix_m2_num"] = df["prix_m2_num"].round(2)

# ================================
# 7) Suppression des lignes invalides
# ================================

print("Suppression des lignes avec surface manquante...")
avant = len(df)
df = df[df["surface_num"].notna()]
apres = len(df)
print("Lignes supprimées pour surface manquante :", avant - apres)

# ================================
# 8) DataFrame final
# ================================

df_clean = df[[
    "source",
    "type",
    "prix_num",
    "surface_num",
    "prix_m2_num",
    "nb_pieces_num",
    "localisation_clean",
    "details",
]].rename(columns={
    "prix_num": "prix",
    "surface_num": "surface",
    "prix_m2_num": "prix_m2",
    "nb_pieces_num": "nb_pieces",
    "localisation_clean": "localisation",
})

print("Taille du fichier propre :", len(df_clean))

# ================================
# 9) Export
# ================================

df_clean.to_csv(OUTPUT_PATH, sep=";", index=False, encoding="utf-8")
print("Nettoyage terminé.")
print("Fichier généré :", OUTPUT_PATH)
