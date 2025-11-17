"""
    Agrégateur DVF géocodées depuis data.gouv.fr
    Filtre sur Paris (75) + sépare exploitable/inexploitable

    Source: https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees
    Données: 2020_75.csv à 2025_75.csv
"""

import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# Fichiers DVF géocodés (data.gouv.fr)
fichiers = [
    "../../../datas/downloaded/geocodes/brut/2020_75.csv",
    "../../../datas/downloaded/geocodes/brut/2021_75.csv",
    "../../../datas/downloaded/geocodes/brut/2022_75.csv",
    "../../../datas/downloaded/geocodes/brut/2023_75.csv",
    "../../../datas/downloaded/geocodes/brut/2024_75.csv",
    "../../../datas/downloaded/geocodes/brut/2025_75.csv",
]

# Fichiers de sortie
fichier_tous = os.path.join(base_dir, "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025.csv")
fichier_exploitables = os.path.join(base_dir, "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025-exploitables.csv")
fichier_inexploitables = os.path.join(base_dir, "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025-inexploitables.csv")

# Crée le répertoire s'il n'existe pas
output_dir = os.path.dirname(fichier_tous)
os.makedirs(output_dir, exist_ok=True)

# Supprime les fichiers existants
for f in [fichier_tous, fichier_exploitables, fichier_inexploitables]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"Ancien fichier supprimé: {os.path.basename(f)}")
        except PermissionError:
            print(f"Impossible de supprimer {os.path.basename(f)} - fermez le fichier")
            import sys
            sys.exit(1)

# Traite par paquets
chunksize = 500000

compteur_tous = 0
compteur_exploitables = 0
compteur_inexploitables = 0

print("="*70)
print("AGRÉGATION DVF GÉOCODÉES PARIS 2020-2025")
print("="*70)

for fichier in fichiers:
    chemin = os.path.join(base_dir, fichier)
    if not os.path.exists(chemin):
        print(f"Fichier introuvable : {chemin}")
        continue

    print(f"\nTraitement de : {os.path.basename(chemin)}")

    try:
        chunks = pd.read_csv(
            chemin,
            sep=',',
            dtype=str,
            encoding='utf-8',
            chunksize=chunksize,
            low_memory=False
        )
    except Exception as e:
        print(f"Erreur lecture : {e}")
        continue

    for i, chunk in enumerate(chunks):
        # Strip whitespace
        chunk = chunk.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Filtrage Paris : code_commune commence par 75 (75056 = Paris)
        paris_mask = (
            chunk["code_commune"].astype(str).str.startswith('75', na=False) &
            (chunk["nom_commune"].astype(str).str.contains('PARIS', case=False, na=False))
        )
        paris_chunk = chunk[paris_mask].copy()

        if len(paris_chunk) == 0:
            continue

        # Extraction année depuis date_mutation (format YYYY-MM-DD)
        try:
            paris_chunk["annee"] = pd.to_datetime(paris_chunk["date_mutation"], errors='coerce').dt.year.astype(str)
        except:
            # Fallback : extraire de nom fichier
            annee = os.path.basename(chemin).split('_')[0]
            paris_chunk["annee"] = annee

        # ========== FICHIER 1 : TOUS ==========
        if len(paris_chunk) > 0:
            try:
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
            except PermissionError:
                print(f"ERREUR : Impossible d'écrire dans {fichier_tous}")
                import sys
                sys.exit(1)

        # ========== SÉPARATION EXPLOITABLE / INEXPLOITABLE ==========
        # Conversion numérique
        paris_chunk['valeur_fonciere_num'] = pd.to_numeric(
            paris_chunk['valeur_fonciere'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
        paris_chunk['surface_reelle_bati_num'] = pd.to_numeric(
            paris_chunk['surface_reelle_bati'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
        paris_chunk['surface_terrain_num'] = pd.to_numeric(
            paris_chunk['surface_terrain'].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
        paris_chunk['latitude_num'] = pd.to_numeric(paris_chunk['latitude'], errors='coerce')
        paris_chunk['longitude_num'] = pd.to_numeric(paris_chunk['longitude'], errors='coerce')

        # Surface composite (priorité: bâti, puis terrain)
        paris_chunk['surface_composite'] = paris_chunk['surface_reelle_bati_num'].fillna(paris_chunk['surface_terrain_num'])

        # Masque exploitable : Valeur fonciere ET Surface > 0 ET coordonnées valides
        exploitable_mask = (
            paris_chunk['valeur_fonciere_num'].notna() &
            (paris_chunk['valeur_fonciere_num'] > 0) &
            paris_chunk['surface_composite'].notna() &
            (paris_chunk['surface_composite'] > 0) &
            paris_chunk['latitude_num'].notna() &
            paris_chunk['longitude_num'].notna()
        )

        paris_exploitable = paris_chunk[exploitable_mask].copy()
        paris_inexploitable = paris_chunk[~exploitable_mask].copy()

        # Supprime colonnes temporaires
        for col in ['valeur_fonciere_num', 'surface_reelle_bati_num', 'surface_terrain_num',
                    'surface_composite', 'latitude_num', 'longitude_num']:
            paris_exploitable.drop(col, axis=1, errors='ignore', inplace=True)
            paris_inexploitable.drop(col, axis=1, errors='ignore', inplace=True)

        # ========== FICHIER 2 : EXPLOITABLES ==========
        if len(paris_exploitable) > 0:
            try:
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
            except PermissionError as e:
                print(f"Erreur écriture exploitables: {e}")

        # ========== FICHIER 3 : INEXPLOITABLES ==========
        if len(paris_inexploitable) > 0:
            try:
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
            except PermissionError as e:
                print(f"Erreur écriture inexploitables: {e}")

        # Affichage progress
        exp_pct = len(paris_exploitable) / len(paris_chunk) * 100 if len(paris_chunk) > 0 else 0
        inexpl_pct = len(paris_inexploitable) / len(paris_chunk) * 100 if len(paris_chunk) > 0 else 0

        print(f"  Chunk {i+1}: {len(paris_chunk):>6} lignes")
        print(f"           ├─ {len(paris_exploitable):>6} exploitables ({exp_pct:>5.1f}%)")
        print(f"           └─ {len(paris_inexploitable):>6} inexploitables ({inexpl_pct:>5.1f}%)")

print("\n" + "="*70)
print("AGRÉGATION COMPLÉTÉE")
print("="*70)

print(f"\nRÉSUMÉ :")
print(f"\nTOUTES LES DONNÉES")
print(f"   Fichier: {fichier_tous}")
print(f"   Lignes: {compteur_tous:>8}")

print(f"\nEXPLOITABLES (Valeur + Surface + Coordonnées valides)")
print(f"   Fichier: {fichier_exploitables}")
print(f"   Lignes: {compteur_exploitables:>8} ({compteur_exploitables/compteur_tous*100:>5.1f}%)")

print(f"\nINEXPLOITABLES (manque Valeur, Surface ou Coordonnées)")
print(f"   Fichier: {fichier_inexploitables}")
print(f"   Lignes: {compteur_inexploitables:>8} ({compteur_inexploitables/compteur_tous*100:>5.1f}%)")

print(f"\nVérification: {compteur_exploitables + compteur_inexploitables} = {compteur_tous}")