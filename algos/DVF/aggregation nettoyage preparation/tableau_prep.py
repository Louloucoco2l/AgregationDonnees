"""
    Script de préparation des données DVFGeo pour Tableau Public (finalement non utilisé, trop de limitations. tout est depuis python)
    Génère 4 fichiers CSV optimisés pour visualisations Tableau

    Entrée: dvfgeo_paris_2020-2025-exploitables-clean.csv
    Sorties:
    - dvfgeo_tableau_arrondissements.csv (20 lignes)
    - dvfgeo_tableau_temporel.csv (120 lignes)
    - dvfgeo_tableau_type_local.csv (80 lignes)
    - dvfgeo_tableau_detail.csv (191K lignes)
"""

import os
import sys
import pandas as pd

INPUT_PATH = "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_DIR = "../../../datas/downloaded/geocodes/tableau/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Coordonnées centrales des 20 arrondissements de Paris
ARRONDISSEMENTS = {
    1: {"nom": "1er", "lat": 48.8628, "lon": 2.3469},
    2: {"nom": "2e", "lat": 48.8637, "lon": 2.3522},
    3: {"nom": "3e", "lat": 48.8606, "lon": 2.3600},
    4: {"nom": "4e", "lat": 48.8530, "lon": 2.3554},
    5: {"nom": "5e", "lat": 48.8467, "lon": 2.3523},
    6: {"nom": "6e", "lat": 48.8490, "lon": 2.3333},
    7: {"nom": "7e", "lat": 48.8549, "lon": 2.3103},
    8: {"nom": "8e", "lat": 48.8698, "lon": 2.3078},
    9: {"nom": "9e", "lat": 48.8771, "lon": 2.3382},
    10: {"nom": "10e", "lat": 48.8734, "lon": 2.3609},
    11: {"nom": "11e", "lat": 48.8636, "lon": 2.3801},
    12: {"nom": "12e", "lat": 48.8407, "lon": 2.3978},
    13: {"nom": "13e", "lat": 48.8273, "lon": 2.3558},
    14: {"nom": "14e", "lat": 48.8289, "lon": 2.3278},
    15: {"nom": "15e", "lat": 48.8427, "lon": 2.2892},
    16: {"nom": "16e", "lat": 48.8565, "lon": 2.2777},
    17: {"nom": "17e", "lat": 48.8803, "lon": 2.2888},
    18: {"nom": "18e", "lat": 48.8893, "lon": 2.3449},
    19: {"nom": "19e", "lat": 48.8925, "lon": 2.3885},
    20: {"nom": "20e", "lat": 48.8599, "lon": 2.4079},
}


def load_data(filepath):
    """Charge les données nettoyées"""
    print("Chargement: " + os.path.basename(filepath))

    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversion numérique
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce')

    # Surface composite
    df['surface'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: round(row['valeur_fonciere'] / row['surface'], 2)
        if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface']) and row['surface'] > 0
        else None,
        axis=1
    )

    # Arrondissement
    df['arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)

    # Date
    df['date_mutation'] = pd.to_datetime(df['date_mutation'], errors='coerce')
    df['annee'] = df['date_mutation'].dt.year

    print("OK - {} lignes chargees\n".format(len(df)))
    return df


def create_arrondissements(df):
    """Crée le fichier agrégé par arrondissement"""
    print("=" * 70)
    print("Creation: dvfgeo_tableau_arrondissements.csv")
    print("=" * 70)

    agg_data = []

    for arr in sorted(df['arrondissement'].unique()):
        arr_data = df[df['arrondissement'] == arr]

        if len(arr_data) == 0:
            continue

        agg_data.append({
            'arrondissement': int(arr),
            'nom_arrondissement': "75{:02d} - {}e".format(int(arr), int(arr)),
            'latitude': ARRONDISSEMENTS[int(arr)]['lat'],
            'longitude': ARRONDISSEMENTS[int(arr)]['lon'],
            'prix_m2_moyen': round(arr_data['prix_m2'].mean(), 2),
            'prix_m2_median': round(arr_data['prix_m2'].median(), 2),
            'prix_m2_min': round(arr_data['prix_m2'].min(), 2),
            'prix_m2_max': round(arr_data['prix_m2'].max(), 2),
            'prix_m2_std': round(arr_data['prix_m2'].std(), 2),
            'nombre_transactions': len(arr_data),
            'surface_moyenne': round(arr_data['surface'].mean(), 2),
            'valeur_moyenne': round(arr_data['valeur_fonciere'].mean(), 2),
        })

    df_arr = pd.DataFrame(agg_data)

    print("Nombre d'arrondissements: {}".format(len(df_arr)))
    print("Lignes: {}".format(len(df_arr)))
    print(df_arr.to_string(index=False))

    df_arr.to_csv(
        os.path.join(OUTPUT_DIR, "dvfgeo_tableau_arrondissements.csv"),
        sep=';', index=False, encoding='utf-8'
    )
    print("Export OK\n")

    return df_arr


def create_temporel(df):
    """Crée le fichier agrégé par année et arrondissement"""
    print("=" * 70)
    print("Creation: dvfgeo_tableau_temporel.csv")
    print("=" * 70)

    agg_data = []

    for annee in sorted(df['annee'].unique()):
        for arr in sorted(df['arrondissement'].unique()):
            subset = df[(df['annee'] == annee) & (df['arrondissement'] == arr)]

            if len(subset) == 0:
                continue

            agg_data.append({
                'annee': int(annee),
                'arrondissement': int(arr),
                'nom_arrondissement': "75{:02d}".format(int(arr)),
                'prix_m2_moyen': round(subset['prix_m2'].mean(), 2),
                'prix_m2_median': round(subset['prix_m2'].median(), 2),
                'nombre_transactions': len(subset),
                'surface_moyenne': round(subset['surface'].mean(), 2),
            })

    df_temp = pd.DataFrame(agg_data)

    print("Nombre de combinaisons (annee x arrondissement): {}".format(len(df_temp)))
    print("Apercu (premiers lignes):")
    print(df_temp.head(10).to_string(index=False))

    df_temp.to_csv(
        os.path.join(OUTPUT_DIR, "dvfgeo_tableau_temporel.csv"),
        sep=';', index=False, encoding='utf-8'
    )
    print("Export OK\n")

    return df_temp


def create_type_local(df):
    """Crée le fichier agrégé par type de local et arrondissement"""
    print("=" * 70)
    print("Creation: dvfgeo_tableau_type_local.csv")
    print("=" * 70)

    agg_data = []

    for arr in sorted(df['arrondissement'].unique()):
        for tlocal in df['type_local'].dropna().unique():
            subset = df[(df['arrondissement'] == arr) & (df['type_local'] == tlocal)]

            if len(subset) < 2:  # Ignore les petits groupes
                continue

            # Coordonnées du centre de l'arrondissement
            lat = ARRONDISSEMENTS[int(arr)]['lat']
            lon = ARRONDISSEMENTS[int(arr)]['lon']

            agg_data.append({
                'arrondissement': int(arr),
                'nom_arrondissement': "75{:02d}".format(int(arr)),
                'type_local': str(tlocal)[:50],
                'latitude': lat,
                'longitude': lon,
                'prix_m2_moyen': round(subset['prix_m2'].mean(), 2),
                'prix_m2_median': round(subset['prix_m2'].median(), 2),
                'nombre_transactions': len(subset),
                'surface_moyenne': round(subset['surface'].mean(), 2),
            })

    df_type = pd.DataFrame(agg_data)

    print("Nombre de combinaisons (type x arrondissement): {}".format(len(df_type)))
    print("Types de local:")
    print(df_type['type_local'].unique())

    df_type.to_csv(
        os.path.join(OUTPUT_DIR, "dvfgeo_tableau_type_local.csv"),
        sep=';', index=False, encoding='utf-8'
    )
    print("Export OK\n")

    return df_type


def create_detail(df):
    """Crée le fichier détail avec toutes les transactions"""
    print("=" * 70)
    print("Creation: dvfgeo_tableau_detail.csv")
    print("=" * 70)

    # Sélectionner colonnes pertinentes
    colonnes_output = [
        'date_mutation', 'annee', 'arrondissement',
        'adresse_numero', 'adresse_nom_voie', 'code_postal',
        'type_local', 'nature_mutation',
        'valeur_fonciere', 'surface', 'prix_m2',
        'nombre_pieces_principales',
        'latitude', 'longitude'
    ]

    df_detail = df[colonnes_output].copy()

    print("Nombre de transactions: {}".format(len(df_detail)))
    print("Colonnes: {}".format(len(df_detail.columns)))
    print("Apercu (premiers lignes):")
    print(df_detail.head(5).to_string())

    df_detail.to_csv(
        os.path.join(OUTPUT_DIR, "dvfgeo_tableau_detail.csv"),
        sep=';', index=False, encoding='utf-8'
    )
    print("\nExport OK\n")

    return df_detail


def print_summary():
    """Affiche un résumé des fichiers générés"""
    print("=" * 70)
    print("RESUME - FICHIERS GENERES POUR TABLEAU")
    print("=" * 70)

    print("\n1. dvfgeo_tableau_arrondissements.csv")
    print("   - 20 lignes (un par arrondissement)")
    print("   - Usage: Carte choroplèthe Paris")
    print("   - Colonnes: arrondissement, lat, lon, prix_moyen, prix_median, nb_transactions")

    print("\n2. dvfgeo_tableau_temporel.csv")
    print("   - 120 lignes (6 ans x 20 arrondissements)")
    print("   - Usage: Série temporelle, évolution année par année")
    print("   - Colonnes: annee, arrondissement, prix_moyen, nb_transactions")

    print("\n3. dvfgeo_tableau_type_local.csv")
    print("   - ~80 lignes (4 types x 20 arrondissements)")
    print("   - Usage: Comparaison par type (Appartement vs Commercial vs Dépendance)")
    print("   - Colonnes: type_local, arrondissement, lat, lon, prix_moyen, nb_transactions")

    print("\n4. dvfgeo_tableau_detail.csv")
    print("   - 191K lignes (toutes les transactions)")
    print("   - Usage: Drill-down, détail complet, filtres")
    print("   - Colonnes: date, adresse, prix_m2, surface, type_local, etc")

    print("\nOuverture dans Tableau Public:")
    print("  1. Aller sur https://public.tableau.com")
    print("  2. Create > New Data Source")
    print("  3. Upload dvfgeo_tableau_arrondissements.csv")
    print("  4. Creer feuille:")
    print("     - Longitude → Colonnes")
    print("     - Latitude → Lignes")
    print("     - Prix_m2_moyen → Couleur (bleu->rouge)")
    print("     - Nom_arrondissement → Tooltip")
    print("\n")


def main():
    if not os.path.isfile(INPUT_PATH):
        print("Erreur: Fichier introuvable: {}".format(INPUT_PATH))
        sys.exit(1)

    print("=" * 70)
    print("PREPARATION DONNEES TABLEAU - DVFGeo")
    print("=" * 70 + "\n")

    # Charger données
    df = load_data(INPUT_PATH)

    # Créer fichiers agrégés
    df_arr = create_arrondissements(df)
    df_temp = create_temporel(df)
    df_type = create_type_local(df)
    df_detail = create_detail(df)

    # Résumé
    print_summary()

    print("=" * 70)
    print("PREPARATION COMPLETE")
    print("=" * 70)
    print("\nFichiers generes dans: {}".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()