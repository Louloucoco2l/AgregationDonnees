"""
    Script d'analyse détaillée pour identifier les meilleures stratégies
    de détection des valeurs aberrantes dans les données DVF Paris
"""
import os
import sys
import pandas as pd
import numpy as np

INPUT_PATH = "../../datas/downloaded/cleaned/valeursfoncieres-paris-2020-2025.1.csv"
OUTPUT_DIR = "../../datas/downloaded/analysis/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_and_prepare(filepath):
    """Charge et prépare les données"""
    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversion numérique
    df['Valeur fonciere'] = pd.to_numeric(
        df['Valeur fonciere'].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    df['Surface reelle bati'] = pd.to_numeric(
        df['Surface reelle bati'].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    df['Surface terrain'] = pd.to_numeric(
        df['Surface terrain'].astype(str).str.replace(',', '.'),
        errors='coerce'
    )
    df['Surface'] = df['Surface reelle bati'].fillna(df['Surface terrain'])
    df['Prix_m2'] = df['Valeur fonciere'] / df['Surface']

    return df

def statistical_analysis(df):
    """Analyse statistique globale"""
    print("\n" + "="*70)
    print("ANALYSE STATISTIQUE GLOBALE")
    print("="*70)

    stats = df['Prix_m2'].describe()
    print(stats)

    # Percentiles
    print(f"\nPercentiles:")
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        val = df['Prix_m2'].quantile(p/100)
        print(f"  {p:2d}e: {val:>10,.0f}€/m²")

    # Écarts
    print(f"\nMesures de dispersion:")
    print(f"  Médiane: {df['Prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df['Prix_m2'].mean():>10,.0f}€/m²")
    print(f"  Écart-type: {df['Prix_m2'].std():>10,.0f}€/m²")
    print(f"  Min: {df['Prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df['Prix_m2'].max():>10,.0f}€/m²")

    return stats

def iqr_method(df):
    """Méthode IQR (Interquartile Range)"""
    print("\n" + "="*70)
    print("MÉTHODE IQR (Interquartile Range)")
    print("="*70)

    Q1 = df['Prix_m2'].quantile(0.25)
    Q3 = df['Prix_m2'].quantile(0.75)
    IQR = Q3 - Q1

    seuil_bas = Q1 - 1.5 * IQR
    seuil_haut = Q3 + 1.5 * IQR

    print(f"Q1 (25e percentile): {Q1:>10,.0f}€/m²")
    print(f"Q3 (75e percentile): {Q3:>10,.0f}€/m²")
    print(f"IQR: {IQR:>10,.0f}€/m²")
    print(f"\nSeuils d'aberrance:")
    print(f"  Bas: {seuil_bas:>10,.0f}€/m²")
    print(f"  Haut: {seuil_haut:>10,.0f}€/m²")

    aberrantes = df[(df['Prix_m2'] < seuil_bas) | (df['Prix_m2'] > seuil_haut)]
    normales = df[(df['Prix_m2'] >= seuil_bas) & (df['Prix_m2'] <= seuil_haut)]

    print(f"\nRésultats IQR:")
    print(f"  Lignes normales: {len(normales)} ({len(normales)/len(df)*100:.1f}%)")
    print(f"  Lignes aberrantes: {len(aberrantes)} ({len(aberrantes)/len(df)*100:.1f}%)")

    return aberrantes, normales, seuil_bas, seuil_haut

def std_method(df, nb_sigma=3):
    """Méthode écart-type"""
    print("\n" + "="*70)
    print(f"MÉTHODE ÉCART-TYPE ({nb_sigma}σ)")
    print("="*70)

    mean = df['Prix_m2'].mean()
    std = df['Prix_m2'].std()

    seuil_bas = mean - nb_sigma * std
    seuil_haut = mean + nb_sigma * std

    print(f"Moyenne: {mean:>10,.0f}€/m²")
    print(f"Écart-type: {std:>10,.0f}€/m²")
    print(f"\nSeuils d'aberrance ({nb_sigma}σ):")
    print(f"  Bas: {seuil_bas:>10,.0f}€/m²")
    print(f"  Haut: {seuil_haut:>10,.0f}€/m²")

    aberrantes = df[(df['Prix_m2'] < seuil_bas) | (df['Prix_m2'] > seuil_haut)]
    normales = df[(df['Prix_m2'] >= seuil_bas) & (df['Prix_m2'] <= seuil_haut)]

    print(f"\nRésultats {nb_sigma}σ:")
    print(f"  Lignes normales: {len(normales)} ({len(normales)/len(df)*100:.1f}%)")
    print(f"  Lignes aberrantes: {len(aberrantes)} ({len(aberrantes)/len(df)*100:.1f}%)")

    return aberrantes, normales, seuil_bas, seuil_haut

def by_district_analysis(df):
    """Analyse par arrondissement"""
    print("\n" + "="*70)
    print("ANALYSE PAR ARRONDISSEMENT")
    print("="*70)

    # Extrait l'arrondissement du code postal (75001 -> 01)
    df['Arrondissement'] = df['Code postal'].astype(str).str[-2:]

    districts = []
    for arr in sorted(df['Arrondissement'].unique()):
        if pd.isna(arr) or arr == '':
            continue

        arr_data = df[df['Arrondissement'] == arr]['Prix_m2']
        if len(arr_data) == 0:
            continue

        Q1 = arr_data.quantile(0.25)
        Q3 = arr_data.quantile(0.75)
        median = arr_data.median()
        mean = arr_data.mean()
        std = arr_data.std()

        districts.append({
            'Arrondissement': f"75{arr}",
            'Lignes': len(arr_data),
            'Médiane': f"{median:>8,.0f}",
            'Moyenne': f"{mean:>8,.0f}",
            'Écart-type': f"{std:>8,.0f}",
            'Min': f"{arr_data.min():>8,.0f}",
            'Max': f"{arr_data.max():>8,.0f}"
        })

    districts_df = pd.DataFrame(districts)
    print(districts_df.to_string(index=False))

    return df

def by_type_local_analysis(df):
    """Analyse par type de local"""
    print("\n" + "="*70)
    print("ANALYSE PAR TYPE DE LOCAL")
    print("="*70)

    types = []
    for tlocal in df['Type local'].dropna().unique():
        type_data = df[df['Type local'] == tlocal]['Prix_m2']

        if len(type_data) < 10:  # Ignore les petits groupes
            continue

        Q1 = type_data.quantile(0.25)
        Q3 = type_data.quantile(0.75)
        IQR = Q3 - Q1
        median = type_data.median()
        mean = type_data.mean()

        types.append({
            'Type local': str(tlocal)[:40],
            'Lignes': len(type_data),
            'Médiane': f"{median:>8,.0f}",
            'Moyenne': f"{mean:>8,.0f}",
            'Min': f"{type_data.min():>8,.0f}",
            'Max': f"{type_data.max():>8,.0f}",
            'IQR': f"{IQR:>8,.0f}"
        })

    types_df = pd.DataFrame(types).sort_values('Lignes', ascending=False)
    print(types_df.to_string(index=False))

    return df

def export_outliers(df, aberrantes_iqr, aberrantes_std):
    """Exporte les outliers pour inspection"""
    print("\n" + "="*70)
    print("EXPORT DES DONNÉES")
    print("="*70)

    # Top 100 aberrantes (IQR)
    top_aberrantes = aberrantes_iqr.nlargest(100, 'Prix_m2')[
        ['Voie', 'Code postal', 'Type local', 'Valeur fonciere', 'Surface', 'Prix_m2', 'Annee']
    ]
    top_aberrantes.to_csv(
        os.path.join(OUTPUT_DIR, "top-100-aberrantes-iqr.csv"),
        sep=';', index=False, encoding='utf-8'
    )
    print(f"✓ Top 100 aberrantes (IQR): {os.path.join(OUTPUT_DIR, 'top-100-aberrantes-iqr.csv')}")

    # Comparaison des deux méthodes
    ids_iqr = set(aberrantes_iqr.index)
    ids_std = set(aberrantes_std.index)

    common = ids_iqr & ids_std
    only_iqr = ids_iqr - ids_std
    only_std = ids_std - ids_iqr

    print(f"\nComparaison IQR vs Écart-type:")
    print(f"  Aberrantes (IQR): {len(ids_iqr)}")
    print(f"  Aberrantes (3σ): {len(ids_std)}")
    print(f"  Communes aux deux: {len(common)}")
    print(f"  Seulement IQR: {len(only_iqr)}")
    print(f"  Seulement 3σ: {len(only_std)}")

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"Fichier introuvable: {INPUT_PATH}")
        sys.exit(1)

    print(f"Chargement de {INPUT_PATH}...")
    df = load_and_prepare(INPUT_PATH)
    print(f"✓ {len(df)} lignes chargées")

    # Analyses
    statistical_analysis(df)
    aberrantes_iqr, normales_iqr, sb_iqr, sh_iqr = iqr_method(df)
    aberrantes_std, normales_std, sb_std, sh_std = std_method(df, nb_sigma=3)
    by_district_analysis(df)
    by_type_local_analysis(df)
    export_outliers(df, aberrantes_iqr, aberrantes_std)

    print("\n" + "="*70)
    print("✓ Analyse complète terminée")
    print("="*70)

if __name__ == "__main__":
    main()