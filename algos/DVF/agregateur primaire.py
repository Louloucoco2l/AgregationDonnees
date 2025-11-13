"""
    Script d'agrégation des données DVF depuis les fichiers bruts
    Produit 3 fichiers :
    1. valeursfoncieres-paris-2020-2025.1.csv : toutes les données Paris
    2. valeursfoncieres-paris-2020-2025.1-exploitables.csv : données avec surface et valeur
    3. valeursfoncieres-paris-2020-2025.1-inexploitables.csv : données sans surface ou valeur
"""

import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# Fichiers DVF à traiter
fichiers = [
    "../../datas/downloaded/brut/valeursfoncieres-2020-s2.txt",
    "../../datas/downloaded/brut/valeursfoncieres-2021.txt",
    "../../datas/downloaded/brut/valeursfoncieres-2022.txt",
    "../../datas/downloaded/brut/valeursfoncieres-2023.txt",
    "../../datas/downloaded/brut/valeursfoncieres-2024.txt",
    "../../datas/downloaded/brut/valeursfoncieres-2025-s1.txt"
]

colonnes = [
    "Identifiant de document",
    "Reference document",
    "1 Articles CGI",
    "2 Articles CGI",
    "3 Articles CGI",
    "4 Articles CGI",
    "5 Articles CGI",
    "No disposition",
    "Date mutation",
    "Nature mutation",
    "Valeur fonciere",
    "No voie",
    "B/T/Q",
    "Type de voie",
    "Code voie",
    "Voie",
    "Code postal",
    "Commune",
    "Code departement",
    "Code commune",
    "Prefixe de section",
    "Section",
    "No plan",
    "No Volume",
    "1er lot",
    "Surface Carrez du 1er lot",
    "2eme lot",
    "Surface Carrez du 2eme lot",
    "3eme lot",
    "Surface Carrez du 3eme lot",
    "4eme lot",
    "Surface Carrez du 4eme lot",
    "5eme lot",
    "Surface Carrez du 5eme lot",
    "Nombre de lots",
    "Code type local",
    "Type local",
    "Identifiant local",
    "Surface reelle bati",
    "Nombre pieces principales",
    "Nature culture",
    "Nature culture speciale",
    "Surface terrain"
]

# Fichiers de sortie
fichier_tous = os.path.join(base_dir, "../../datas/downloaded/cleaned/valeursfoncieres-paris-2020-2025.1.csv")
fichier_exploitables = os.path.join(base_dir,
                                    "../../datas/downloaded/cleaned/valeursfoncieres-paris-2020-2025.1-exploitables.csv")
fichier_inexploitables = os.path.join(base_dir,
                                      "../../datas/downloaded/cleaned/valeursfoncieres-paris-2020-2025.1-inexploitables.csv")

# Traite par paquets, plus digeste
chunksize = 500000

compteur_tous = 0
compteur_exploitables = 0
compteur_inexploitables = 0

print("=" * 70)
print("AGRÉGATION DVF PARIS 2020-2025")
print("=" * 70)

for fichier in fichiers:
    chemin = os.path.join(base_dir, fichier)
    if not os.path.exists(chemin):
        print(f" Fichier introuvable : {chemin}")
        continue

    print(f"\n Traitement de : {os.path.basename(chemin)}")

    chunks = pd.read_csv(
        chemin,
        sep='|',
        dtype=str,
        names=colonnes,
        header=0,
        chunksize=chunksize,
        low_memory=False
    )

    for i, chunk in enumerate(chunks):
        # Strip whitespace
        chunk = chunk.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Filtrage multi critères Paris
        paris_mask = (
                (chunk["Code postal"].astype(str).str.contains('75', na=False)) &
                (chunk["Commune"].astype(str).str.contains("PARIS", case=False, na=False)) &
                (chunk["Code departement"].astype(str).str.contains('75', na=False))
        )
        paris_chunk = chunk[paris_mask].copy()

        # Ajout de la colonne "Annee"
        annee = fichier.split('-')[1]  # extrait "2020", "2021", "2024", etc.
        paris_chunk["Annee"] = annee

        # ========== FICHIER 1 : TOUS ==========
        if len(paris_chunk) > 0:
            mode = 'a' if os.path.exists(fichier_tous) else 'w'
            header = not os.path.exists(fichier_tous)
            paris_chunk.to_csv(
                fichier_tous,
                sep=';',
                index=False,
                encoding='utf-8',
                header=header,
                mode=mode,
                quoting=1
            )
            compteur_tous += len(paris_chunk)

        # ========== SÉPARATION EXPLOITABLE / INEXPLOITABLE ==========
        # Conversion numérique pour vérification
        paris_chunk['Valeur fonciere_num'] = pd.to_numeric(
            paris_chunk['Valeur fonciere'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
        paris_chunk['Surface reelle bati_num'] = pd.to_numeric(
            paris_chunk['Surface reelle bati'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
        paris_chunk['Surface terrain_num'] = pd.to_numeric(
            paris_chunk['Surface terrain'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )

        # Surface composite
        paris_chunk['Surface_composite'] = paris_chunk['Surface reelle bati_num'].fillna(
            paris_chunk['Surface terrain_num'])

        # Masque exploitable : Valeur fonciere ET Surface > 0
        exploitable_mask = (
                paris_chunk['Valeur fonciere_num'].notna() &
                paris_chunk['Surface_composite'].notna() &
                (paris_chunk['Surface_composite'] > 0)
        )

        paris_exploitable = paris_chunk[exploitable_mask].copy()
        paris_inexploitable = paris_chunk[~exploitable_mask].copy()

        # Supprime les colonnes temporaires
        for col in ['Valeur fonciere_num', 'Surface reelle bati_num', 'Surface terrain_num', 'Surface_composite']:
            paris_exploitable.drop(col, axis=1, errors='ignore', inplace=True)
            paris_inexploitable.drop(col, axis=1, errors='ignore', inplace=True)

        # ========== FICHIER 2 : EXPLOITABLES ==========
        if len(paris_exploitable) > 0:
            mode = 'a' if os.path.exists(fichier_exploitables) else 'w'
            header = not os.path.exists(fichier_exploitables)
            paris_exploitable.to_csv(
                fichier_exploitables,
                sep=';',
                index=False,
                encoding='utf-8',
                header=header,
                mode=mode,
                quoting=1
            )
            compteur_exploitables += len(paris_exploitable)

        # ========== FICHIER 3 : INEXPLOITABLES ==========
        if len(paris_inexploitable) > 0:
            mode = 'a' if os.path.exists(fichier_inexploitables) else 'w'
            header = not os.path.exists(fichier_inexploitables)
            paris_inexploitable.to_csv(
                fichier_inexploitables,
                sep=';',
                index=False,
                encoding='utf-8',
                header=header,
                mode=mode,
                quoting=1
            )
            compteur_inexploitables += len(paris_inexploitable)

        # Affichage progress
        exp_pct = len(paris_exploitable) / len(paris_chunk) * 100 if len(paris_chunk) > 0 else 0
        inexpl_pct = len(paris_inexploitable) / len(paris_chunk) * 100 if len(paris_chunk) > 0 else 0

        print(f"  Chunk {i + 1}: {len(paris_chunk):>6} lignes ({annee})")
        print(f"           ├─ {len(paris_exploitable):>6} exploitables ({exp_pct:>5.1f}%)")
        print(f"           └─ {len(paris_inexploitable):>6} inexploitables ({inexpl_pct:>5.1f}%)")

print("\n" + "=" * 70)
print("AGRÉGATION COMPLÉTÉE")
print("=" * 70)

print(f"\nRÉSUMÉ :")
print(f"\n  TOUTES LES DONNÉES")
print(f"   Fichier: {fichier_tous}")
print(f"   Lignes: {compteur_tous:>8}")

print(f"\n  EXPLOITABLES (Valeur + Surface > 0)")
print(f"   Fichier: {fichier_exploitables}")
print(f"   Lignes: {compteur_exploitables:>8} ({compteur_exploitables / compteur_tous * 100:>5.1f}%)")

print(f"\n  INEXPLOITABLES (manque Valeur ou Surface)")
print(f"   Fichier: {fichier_inexploitables}")
print(f"   Lignes: {compteur_inexploitables:>8} ({compteur_inexploitables / compteur_tous * 100:>5.1f}%)")

print(f"\nVérification: {compteur_exploitables + compteur_inexploitables} = {compteur_tous}")