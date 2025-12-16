"""
    Script d'analyse détaillée old_dataset géocodées
    Produit max de métriques : stats globales, spatiales, temporelles, par type

    Entrée: dvf_paris_2020-2025-exploitables.csv
"""

import sys
import pandas as pd
from src.config import paths


INPUT_PATH = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_DIR = paths.data.dvf.analysis.path


def load_and_prepare(filepath):
    """Charge et prépare les données"""
    print(f"Chargement: {filepath.name}")

    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversion numérique
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce')
    df['annee'] = pd.to_numeric(df['annee'], errors='coerce')

    # Surface composite
    df['surface'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: row['valeur_fonciere'] / row['surface']
        if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface']) and row['surface'] > 0
        else None,
        axis=1
    )

    # Arrondissement depuis code_commune (75001-75020)
    df['arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)

    print(f"✓ {len(df)} lignes chargées\n")
    return df

def statistical_analysis(df):
    """Analyse statistique globale"""
    print("ANALYSE STATISTIQUE GLOBALE")

    stats = df['prix_m2'].describe()
    print(stats)

    print(f"\nPercentiles:")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        val = df['prix_m2'].quantile(p/100)
        print(f"  {p:2d}e: {val:>10,.0f}€/m²")

    print(f"\nMesures de dispersion:")
    print(f"  Médiane: {df['prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df['prix_m2'].mean():>10,.0f}€/m²")
    print(f"  Écart-type: {df['prix_m2'].std():>10,.0f}€/m²")
    print(f"  Min: {df['prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df['prix_m2'].max():>10,.0f}€/m²")

def iqr_method(df):
    """Méthode IQR"""
    print("MÉTHODE IQR (Interquartile Range)")

    Q1 = df['prix_m2'].quantile(0.25)
    Q3 = df['prix_m2'].quantile(0.75)
    IQR = Q3 - Q1

    seuil_bas = Q1 - 1.5 * IQR
    seuil_haut = Q3 + 1.5 * IQR

    print(f"Q1 (25e): {Q1:>10,.0f}€/m²")
    print(f"Q3 (75e): {Q3:>10,.0f}€/m²")
    print(f"IQR: {IQR:>10,.0f}€/m²")
    print(f"\nSeuils d'aberrance:")
    print(f"  Bas: {seuil_bas:>10,.0f}€/m²")
    print(f"  Haut: {seuil_haut:>10,.0f}€/m²")

    aberrantes = df[(df['prix_m2'] < seuil_bas) | (df['prix_m2'] > seuil_haut)]
    normales = df[(df['prix_m2'] >= seuil_bas) & (df['prix_m2'] <= seuil_haut)]

    print(f"\nRésultats:")
    print(f"  Normales: {len(normales):>8} ({len(normales)/len(df)*100:>5.1f}%)")
    print(f"  Aberrantes: {len(aberrantes):>8} ({len(aberrantes)/len(df)*100:>5.1f}%)")

    return aberrantes, normales

def by_arrondissement(df):
    """Analyse spatiale par arrondissement"""
    print("ANALYSE PAR ARRONDISSEMENT")

    districts = []
    for arr in sorted(df['arrondissement'].unique()):
        arr_data = df[df['arrondissement'] == arr]

        if len(arr_data) == 0:
            continue

        districts.append({
            'Arr': int(arr),
            'Lignes': len(arr_data),
            'Médiane': f"{arr_data['prix_m2'].median():>10,.0f}",
            'Moyenne': f"{arr_data['prix_m2'].mean():>10,.0f}",
            'Écart-type': f"{arr_data['prix_m2'].std():>10,.0f}",
            'Min': f"{arr_data['prix_m2'].min():>10,.0f}",
            'Max': f"{arr_data['prix_m2'].max():>10,.0f}",
            'Lat': f"{arr_data['latitude'].mean():.4f}",
            'Lon': f"{arr_data['longitude'].mean():.4f}"
        })

    districts_df = pd.DataFrame(districts)
    print(districts_df.to_string(index=False))

    return districts_df

def by_type_local(df):
    """Analyse par type de local"""
    print("ANALYSE PAR TYPE DE LOCAL")

    types = []
    for tlocal in df['type_local'].dropna().unique():
        type_data = df[df['type_local'] == tlocal]['prix_m2']

        if len(type_data) < 10:
            continue

        types.append({
            'Type local': str(tlocal)[:35],
            'Lignes': len(type_data),
            'Médiane': f"{type_data.median():>10,.0f}",
            'Moyenne': f"{type_data.mean():>10,.0f}",
            'Min': f"{type_data.min():>10,.0f}",
            'Max': f"{type_data.max():>10,.0f}"
        })

    types_df = pd.DataFrame(types).sort_values('Lignes', ascending=False)
    print(types_df.to_string(index=False))

    return types_df

def temporal_analysis(df):
    """Analyse temporelle"""
    print("ANALYSE TEMPORELLE (Année)")

    temporal = []
    for year in sorted(df['annee'].dropna().unique()):
        year_data = df[df['annee'] == year]['prix_m2']

        if len(year_data) == 0:
            continue

        temporal.append({
            'Année': int(year),
            'Lignes': len(year_data),
            'Médiane': f"{year_data.median():>10,.0f}",
            'Moyenne': f"{year_data.mean():>10,.0f}",
            'Écart-type': f"{year_data.std():>10,.0f}"
        })

    temporal_df = pd.DataFrame(temporal)
    print(temporal_df.to_string(index=False))

    return temporal_df

def correlations_analysis(df):
    """Corrélations entre variables"""
    print("CORRÉLATIONS")

    cols = ['prix_m2', 'valeur_fonciere', 'surface', 'nombre_pieces_principales', 'arrondissement']
    corr_data = df[cols].apply(pd.to_numeric, errors='coerce').dropna()

    if len(corr_data) > 0:
        corr = corr_data.corr(method='pearson')
        print(corr.to_string())

    return corr_data

def export_analysis(df, districts_df, types_df, temporal_df):
    """Exporte les analyses"""
    print("EXPORT")

    # Export arrondissements
    districts_df.to_csv(
        OUTPUT_DIR/ "analysis_arrondissements.csv",
        sep=';', index=False, encoding='utf-8'
    )
    print(f"✓ analysis_arrondissements.csv")

    # Export types
    types_df.to_csv(
        OUTPUT_DIR/ "analysis_types_locaux.csv",
        sep=';', index=False, encoding='utf-8'
    )
    print(f"analysis_types_locaux.csv")

    # Export temporel
    temporal_df.to_csv(
        OUTPUT_DIR/ "analysis_temporel.csv",
        sep=';', index=False, encoding='utf-8'
    )
    print(f"analysis_temporel.csv")

def main():
    if not INPUT_PATH.isfile():
        print(f"Fichier introuvable: {INPUT_PATH}")
        sys.exit(1)

    df = load_and_prepare(INPUT_PATH)

    # Analyses
    statistical_analysis(df)
    districts_df = by_arrondissement(df)
    types_df = by_type_local(df)
    temporal_df = temporal_analysis(df)
    corr_data = correlations_analysis(df)

    # Export
    export_analysis(df, districts_df, types_df, temporal_df)

if __name__ == "__main__":
    main()