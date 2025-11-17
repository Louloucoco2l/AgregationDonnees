"""
    Script de nettoyage DVF géocodées - VERSION OPTIMISÉE
    - Supprime colonnes vides
    - Filtre sur Paris
    - Ajoute prix_m2 et arrondissement
    - Filtre UNIQUEMENT les hautes aberrantes (pas les basses considerees commme prix symboliques)
    - Détecte les vrais outliers, pas les biens chers légitimes

    Entrée: dvf_paris_2020-2025-exploitables.csv
    Sorties:
    - dvf_paris_clean.csv (normal + basses valeurs conservées)
    - dvf_paris_aberrantes_haute.csv (outliers hauts uniquement)
"""

import os
import sys
import pandas as pd
import numpy as np

INPUT_PATH = "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025-exploitables.csv"
OUTPUT_NORMAL = INPUT_PATH.replace('.csv', '-clean.csv')
OUTPUT_ABERRANTES_HAUTE = INPUT_PATH.replace('-exploitables.csv', '-aberrantes-haute.csv')

def load_and_prepare(filepath):
    """Charge et prépare les données"""
    print(f"Chargement: {os.path.basename(filepath)}")

    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversion numérique
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce')

    # Surface composite (priorité: bâti, puis terrain)
    df['surface'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: round(row['valeur_fonciere'] / row['surface'], 2)
        if pd.notna(row['valeur_fonciere'])
           and pd.notna(row['surface'])
           and row['surface'] > 0
        else None,
        axis=1
    )

    # Arrondissement depuis code_commune (75001-75020)
    df['arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)

    # Date mutation au format datetime
    df['date_mutation'] = pd.to_datetime(df['date_mutation'], errors='coerce')
    df['annee'] = df['date_mutation'].dt.year
    df['mois'] = df['date_mutation'].dt.month

    print(f"✓ {len(df)} lignes chargées\n")
    return df

def remove_empty_columns(df):
    """Supprime colonnes entièrement vides"""
    initial_cols = len(df.columns)

    df = df.dropna(axis=1, how='all')

    removed = initial_cols - len(df.columns)
    print(f"✓ {removed} colonnes vides supprimées")
    print(f"✓ {len(df.columns)} colonnes conservées\n")

    return df

def analyze_distribution(df):
    """Analyse distribution pour détecter les vrais outliers"""
    print("="*70)
    print("ANALYSE DE DISTRIBUTION - DÉTECTION OUTLIERS")
    print("="*70)

    prix = df['prix_m2'].dropna()

    # Percentiles clés
    p50 = prix.quantile(0.50)
    p75 = prix.quantile(0.75)
    p90 = prix.quantile(0.90)
    p95 = prix.quantile(0.95)
    p99 = prix.quantile(0.99)
    p999 = prix.quantile(0.999)

    print(f"\nPercentiles clés:")
    print(f"  50e (médiane): {p50:>15,.0f}€/m²")
    print(f"  75e: {p75:>15,.0f}€/m²")
    print(f"  90e: {p90:>15,.0f}€/m²")
    print(f"  95e: {p95:>15,.0f}€/m²")
    print(f"  99e: {p99:>15,.0f}€/m²")
    print(f"  99.9e: {p999:>15,.0f}€/m²")

    # Méthode IQR modifiée (UNIQUEMENT pour détecté les HAUTES aberrantes)
    Q1 = prix.quantile(0.25)
    Q3 = prix.quantile(0.75)
    IQR = Q3 - Q1

    # Seuil bas = on ignore (on veut garder les petites valeurs)
    # Seuil haut = Q3 + 3×IQR (plus strict que 1.5 pour éviter de perdre les vrais biens)
    seuil_haut_iqr = Q3 + 3 * IQR

    print(f"\nMÉTHODE IQR (pour HAUTES aberrantes uniquement):")
    print(f"  Q1 (25e): {Q1:>15,.0f}€/m²")
    print(f"  Q3 (75e): {Q3:>15,.0f}€/m²")
    print(f"  IQR: {IQR:>15,.0f}€/m²")
    print(f"  Seuil haut (Q3 + 3×IQR): {seuil_haut_iqr:>15,.0f}€/m²")

    # Détecte les outliers extrêmes (méthode MAD - Median Absolute Deviation)
    median = prix.median()
    mad = np.median(np.abs(prix - median))
    modified_z_score = 0.6745 * (prix - median) / (mad + 1e-10)  # +1e-10 pour éviter division par 0

    seuil_mad_high = median + 3.5 * mad  # Stricte pour hautes valeurs

    print(f"\nMÉTHODE MAD (Median Absolute Deviation - robuste):")
    print(f"  Médiane: {median:>15,.0f}€/m²")
    print(f"  MAD: {mad:>15,.0f}€/m²")
    print(f"  Seuil haut (Médiane + 3.5×MAD): {seuil_mad_high:>15,.0f}€/m²")

    # Utiliser le seuil le plus permissif (le plus haut) pour ne pas être trop strict
    seuil_final = max(seuil_haut_iqr, seuil_mad_high)

    print(f"\nSEUIL FINAL RETENU: {seuil_final:>15,.0f}€/m²")
    print(f"   (Prend le plus élevé des deux méthodes pour éviter sur-filtrage)")

    return seuil_final

def apply_filter(df, seuil_haut):
    """Applique le filtrage: garde tout sauf hautes aberrantes"""
    print("\n" + "="*70)
    print("🔍 FILTRAGE - HAUTES ABERRANTES UNIQUEMENT")
    print("="*70)

    # Normal = tout ce qui est <= seuil
    mask_normal = df['prix_m2'] <= seuil_haut
    df_normal = df[mask_normal].copy()

    # Aberrantes hautes = ce qui est > seuil
    df_aberrantes_haute = df[~mask_normal].copy()

    print(f"\nRésultats:")
    print(f"  Normal (< {seuil_haut:,.0f}€/m²): {len(df_normal):>8} ({len(df_normal)/len(df)*100:>5.1f}%)")
    print(f"  Aberrantes hautes: {len(df_aberrantes_haute):>8} ({len(df_aberrantes_haute)/len(df)*100:>5.1f}%)")

    return df_normal, df_aberrantes_haute

def analyze_aberrantes(df_aberrantes):
    """Analyse les aberrantes hautes"""
    print("\n" + "="*70)
    print("ANALYSE DES ABERRANTES HAUTES")
    print("="*70)

    print(f"\nPrix/m² des aberrantes:")
    print(f"  Min: {df_aberrantes['prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df_aberrantes['prix_m2'].max():>10,.0f}€/m²")
    print(f"  Médiane: {df_aberrantes['prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df_aberrantes['prix_m2'].mean():>10,.0f}€/m²")

    print(f"\nRépartition par type de local:")
    type_counts = df_aberrantes['type_local'].value_counts()
    for tlocal, count in type_counts.items():
        pct = count / len(df_aberrantes) * 100
        print(f"  {str(tlocal)[:40]:40s}: {count:>6} ({pct:>5.1f}%)")

    print(f"\nRépartition par arrondissement:")
    arr_counts = df_aberrantes['arrondissement'].value_counts().sort_index()
    for arr, count in arr_counts.items():
        pct = count / len(df_aberrantes) * 100
        print(f"  75{int(arr):02d}: {count:>6} ({pct:>5.1f}%)")

    print(f"\nTop 10 adresses les plus chères:")
    top_10 = df_aberrantes.nlargest(10, 'prix_m2')[['adresse_numero', 'adresse_nom_voie', 'type_local', 'prix_m2', 'valeur_fonciere', 'surface']]
    for idx, row in top_10.iterrows():
        print(f"  {row['adresse_numero']} {row['adresse_nom_voie']} - {row['type_local']}")
        print(f"    → {row['prix_m2']:>10,.0f}€/m² ({row['valeur_fonciere']:>12,.0f}€ / {row['surface']:>8,.0f}m²)")

def analyze_normal(df_normal):
    """Analyse des données normales"""
    print("\n" + "="*70)
    print("ANALYSE DES DONNÉES NORMALES")
    print("="*70)

    print(f"\nPrix/m²:")
    print(f"  Min: {df_normal['prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df_normal['prix_m2'].max():>10,.0f}€/m²")
    print(f"  Médiane: {df_normal['prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df_normal['prix_m2'].mean():>10,.0f}€/m²")
    print(f"  Écart-type: {df_normal['prix_m2'].std():>10,.0f}€/m²")

def export_data(df_normal, df_aberrantes_haute):
    """Exporte les données"""
    print("\n" + "="*70)
    print("EXPORT")
    print("="*70)

    try:
        df_normal.to_csv(OUTPUT_NORMAL, sep=';', index=False, encoding='utf-8')
        print(f"✓ {len(df_normal)} lignes normales")
        print(f"  → {OUTPUT_NORMAL}")
    except Exception as e:
        print(f"Erreur export normal: {e}")
        return False

    try:
        df_aberrantes_haute.to_csv(OUTPUT_ABERRANTES_HAUTE, sep=';', index=False, encoding='utf-8')
        print(f"✓ {len(df_aberrantes_haute)} lignes aberrantes (hautes)")
        print(f"  → {OUTPUT_ABERRANTES_HAUTE}")
    except Exception as e:
        print(f"Erreur export aberrantes: {e}")
        return False

    return True

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"Fichier introuvable: {INPUT_PATH}")
        sys.exit(1)

    print("="*70)
    print("NETTOYAGE DVF GÉOCODÉES - HAUTES ABERRANTES UNIQUEMENT")
    print("="*70 + "\n")

    # Charger et préparer
    df = load_and_prepare(INPUT_PATH)

    # Supprimer colonnes vides
    df = remove_empty_columns(df)

    # Analyser distribution et trouver seuil
    seuil_haut = analyze_distribution(df)

    # Filtrage
    df_normal, df_aberrantes_haute = apply_filter(df, seuil_haut)

    # Analyser aberrantes hautes
    analyze_aberrantes(df_aberrantes_haute)

    # Analyser normales
    analyze_normal(df_normal)

    # Export
    if export_data(df_normal, df_aberrantes_haute):
        print("\n" + "="*70)
        print("NETTOYAGE COMPLÉTÉ AVEC SUCCÈS")
        print("="*70)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()