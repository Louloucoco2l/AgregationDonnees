"""
    Script de nettoyage old_dataset géocodées - VERSION OPTIMISÉE v2
    - Supprime colonnes vides
    - Filtre sur Paris
    - Ajoute prix_m2 et arrondissement
    - Filtre les aberrantes HAUTES ET BASSES
    - Exclut les ventes symboliques et prix irréalistes

    Entrée: dvf_paris_2020-2025-exploitables.csv
    Sorties:
    - dvf_paris_clean.csv (données filtrées)
    - dvf_paris_aberrantes_haute.csv (outliers hauts)
    - dvf_paris_aberrantes_basse.csv (outliers bas / ventes symboliques)
"""

import sys
import pandas as pd
import numpy as np
from src.config import paths


INPUT_PATH = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables.csv"
OUTPUT_NORMAL = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_ABERRANTES_HAUTE = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-aberrantes-haute.csv"
OUTPUT_ABERRANTES_BASSE = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-aberrantes-basse.csv"

# Seuils de filtrage bas (prix/m² minimum réaliste pour Paris)
SEUIL_PRIX_M2_MIN = 2000  # €/m² - en dessous = vente symbolique/donation
SEUIL_VALEUR_MIN = 10000  # € - valeur foncière minimum


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

    # Surface composite (priorité: bâti, puis terrain)
    df['surface_m2_retenue'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: round(row['valeur_fonciere'] / row['surface_m2_retenue'], 2)  # Changement ici
        if pd.notna(row['valeur_fonciere'])
           and pd.notna(row['surface_m2_retenue'])
           and row['surface_m2_retenue'] > 0
        else None,
        axis=1
    )

    # Arrondissement depuis code_commune (75001-75020)
    df['code_arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)

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
    print("ANALYSE DE DISTRIBUTION - DÉTECTION OUTLIERS")

    prix = df['prix_m2'].dropna()

    # Percentiles clés
    p01 = prix.quantile(0.01)
    p05 = prix.quantile(0.05)
    p10 = prix.quantile(0.10)
    p50 = prix.quantile(0.50)
    p75 = prix.quantile(0.75)
    p90 = prix.quantile(0.90)
    p95 = prix.quantile(0.95)
    p99 = prix.quantile(0.99)
    p999 = prix.quantile(0.999)

    print(f"\nPercentiles clés:")
    print(f"  1er: {p01:>15,.0f}€/m²")
    print(f"  5e: {p05:>15,.0f}€/m²")
    print(f"  10e: {p10:>15,.0f}€/m²")
    print(f"  50e (médiane): {p50:>15,.0f}€/m²")
    print(f"  75e: {p75:>15,.0f}€/m²")
    print(f"  90e: {p90:>15,.0f}€/m²")
    print(f"  95e: {p95:>15,.0f}€/m²")
    print(f"  99e: {p99:>15,.0f}€/m²")
    print(f"  99.9e: {p999:>15,.0f}€/m²")

    # Méthode IQR
    Q1 = prix.quantile(0.25)
    Q3 = prix.quantile(0.75)
    IQR = Q3 - Q1

    # Seuil haut = Q3 + 3×IQR
    seuil_haut_iqr = Q3 + 3 * IQR

    print(f"\nMÉTHODE IQR:")
    print(f"  Q1 (25e): {Q1:>15,.0f}€/m²")
    print(f"  Q3 (75e): {Q3:>15,.0f}€/m²")
    print(f"  IQR: {IQR:>15,.0f}€/m²")
    print(f"  Seuil haut (Q3 + 3×IQR): {seuil_haut_iqr:>15,.0f}€/m²")

    # Méthode MAD
    median = prix.median()
    mad = np.median(np.abs(prix - median))
    seuil_mad_high = median + 3.5 * mad

    print(f"\nMÉTHODE MAD (Median Absolute Deviation):")
    print(f"  Médiane: {median:>15,.0f}€/m²")
    print(f"  MAD: {mad:>15,.0f}€/m²")
    print(f"  Seuil haut (Médiane + 3.5×MAD): {seuil_mad_high:>15,.0f}€/m²")

    # Seuil final haut
    seuil_haut = max(seuil_haut_iqr, seuil_mad_high)

    # Seuil bas fixe (réaliste pour Paris)
    seuil_bas = SEUIL_PRIX_M2_MIN

    print(f"\nSEUILS FINAUX RETENUS:")
    print(f"  Seuil BAS: {seuil_bas:>15,.0f}€/m² (fixe - prix minimum réaliste Paris)")
    print(f"  Seuil HAUT: {seuil_haut:>15,.0f}€/m² (max IQR/MAD)")

    return seuil_bas, seuil_haut


# Dans clean.py, modifiez la fonction apply_filter

def apply_filter(df, seuil_bas, seuil_haut):
    """Applique le filtrage: exclut aberrantes basses/hautes ET types de biens non pertinents"""
    print("FILTRAGE - ABERRANTES ET TYPES DE BIENS")

    # 1. Filtre Type de Local : On ne garde que les Appartements
    # Les Maisons à Paris sont des outliers statistiques (hôtels particuliers, impasses privées...)
    # Les Dépendances/Locaux commerciaux polluent le prix au m² habitable.
    mask_type = df['type_local'] == 'Appartement'

    # 2. Filtre Surface : On exclut les "micro-surfaces" (< 9m²) souvent des chambres de bonne ou WC
    # et les très grands plateaux (> 300m²) qui sont des marchés de niche.
    mask_surface = (df['surface_m2_retenue'] >= 9) & (df['surface_m2_retenue'] <= 300)

    # 3. Filtres Prix (existants)
    mask_trop_bas = (df['prix_m2'] < seuil_bas) | (df['valeur_fonciere'] < SEUIL_VALEUR_MIN)
    mask_trop_haut = df['prix_m2'] > seuil_haut

    # Combinaison
    mask_normal = mask_type & mask_surface & ~mask_trop_bas & ~mask_trop_haut & df['prix_m2'].notna()

    df_normal = df[mask_normal].copy()

    # Pour info (stats des rejets)
    n_total = len(df)
    n_kept = len(df_normal)
    print(f"  Total initial : {n_total}")
    print(f"  Après filtre Appartement & Surface (9-300m²) : {len(df[mask_type & mask_surface])}")
    print(f"  Final (après filtre prix) : {n_kept} ({n_kept / n_total * 100:.1f}%)")

    # On retourne des DFs vides pour les aberrantes pour ne pas casser la signature,
    # ou on filtre juste les aberrantes du dataset 'normal' pour l'export.
    # Pour simplifier ici, on garde la logique de retour mais on sait que df_normal est purifié.
    df_aberrantes_basse = df[mask_trop_bas].copy()  # Juste pour info
    df_aberrantes_haute = df[mask_trop_haut].copy()

    return df_normal, df_aberrantes_basse, df_aberrantes_haute

def analyze_aberrantes_basses(df_aberrantes):
    """Analyse les aberrantes basses"""
    if len(df_aberrantes) == 0:
        print("\nAucune aberrante basse détectée.")
        return

    print("ANALYSE DES ABERRANTES BASSES (ventes symboliques)")

    print(f"\nPrix/m² des aberrantes basses:")
    print(f"  Min: {df_aberrantes['prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df_aberrantes['prix_m2'].max():>10,.0f}€/m²")
    print(f"  Médiane: {df_aberrantes['prix_m2'].median():>10,.0f}€/m²")

    print(f"\nValeur foncière:")
    print(f"  Min: {df_aberrantes['valeur_fonciere'].min():>12,.0f}€")
    print(f"  Max: {df_aberrantes['valeur_fonciere'].max():>12,.0f}€")
    print(f"  Médiane: {df_aberrantes['valeur_fonciere'].median():>12,.0f}€")

    print(f"\nRépartition par nature de mutation:")
    nature_counts = df_aberrantes['nature_mutation'].value_counts()
    for nature, count in nature_counts.items():
        pct = count / len(df_aberrantes) * 100
        print(f"  {str(nature)[:40]:40s}: {count:>6} ({pct:>5.1f}%)")

    print(f"\nRépartition par type de local:")
    type_counts = df_aberrantes['type_local'].value_counts()
    for tlocal, count in type_counts.items():
        pct = count / len(df_aberrantes) * 100
        print(f"  {str(tlocal)[:40]:40s}: {count:>6} ({pct:>5.1f}%)")


def analyze_aberrantes_hautes(df_aberrantes):
    """Analyse les aberrantes hautes"""
    if len(df_aberrantes) == 0:
        print("\nAucune aberrante haute détectée.")
        return

    print("ANALYSE DES ABERRANTES HAUTES")

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
    arr_counts = df_aberrantes['code_arrondissement'].value_counts().sort_index()
    for arr, count in arr_counts.items():
        pct = count / len(df_aberrantes) * 100
        print(f"  75{int(arr):02d}: {count:>6} ({pct:>5.1f}%)")

    print(f"\nTop 10 adresses les plus chères:")
    top_10 = df_aberrantes.nlargest(10, 'prix_m2')[    ['adresse_numero', 'adresse_nom_voie', 'type_local', 'prix_m2', 'valeur_fonciere', 'surface_m2_retenue']]
    for idx, row in top_10.iterrows():
        print(f"  {row['adresse_numero']} {row['adresse_nom_voie']} - {row['type_local']}")
        print( f"    → {row['prix_m2']:>10,.0f}€/m² ({row['valeur_fonciere']:>12,.0f}€ / {row['surface_m2_retenue']:>8,.0f}m²)")

def analyze_normal(df_normal):
    """Analyse des données normales"""
    print("ANALYSE DES DONNÉES NORMALES (FILTRÉES)")

    print(f"\nPrix/m²:")
    print(f"  Min: {df_normal['prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df_normal['prix_m2'].max():>10,.0f}€/m²")
    print(f"  Médiane: {df_normal['prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df_normal['prix_m2'].mean():>10,.0f}€/m²")
    print(f"  Écart-type: {df_normal['prix_m2'].std():>10,.0f}€/m²")

    print(f"\nValeur foncière:")
    print(f"  Min: {df_normal['valeur_fonciere'].min():>12,.0f}€")
    print(f"  Max: {df_normal['valeur_fonciere'].max():>12,.0f}€")
    print(f"  Médiane: {df_normal['valeur_fonciere'].median():>12,.0f}€")

    print(f"\nSurface:")
    print(f"  Min: {df_normal['surface_m2_retenue'].min():>10,.0f}m²")
    print(f"  Max: {df_normal['surface_m2_retenue'].max():>10,.0f}m²")
    print(f"  Médiane: {df_normal['surface_m2_retenue'].median():>10,.0f}m²")


def export_data(df_normal, df_aberrantes_basse, df_aberrantes_haute):
    """Exporte les données"""
    print("EXPORT")

    try:
        df_normal.to_csv(OUTPUT_NORMAL, sep=';', index=False, encoding='utf-8')
        print(f"{len(df_normal)} lignes normales")
        print(f"{OUTPUT_NORMAL}")
    except Exception as e:
        print(f"Erreur export normal: {e}")
        return False

    try:
        df_aberrantes_haute.to_csv(OUTPUT_ABERRANTES_HAUTE, sep=';', index=False, encoding='utf-8')
        print(f"{len(df_aberrantes_haute)} lignes aberrantes (hautes)")
        print(f"{OUTPUT_ABERRANTES_HAUTE}")
    except Exception as e:
        print(f"Erreur export aberrantes hautes: {e}")
        return False

    try:
        df_aberrantes_basse.to_csv(OUTPUT_ABERRANTES_BASSE, sep=';', index=False, encoding='utf-8')
        print(f"{len(df_aberrantes_basse)} lignes aberrantes (basses)")
        print(f"{OUTPUT_ABERRANTES_BASSE}")
    except Exception as e:
        print(f"Erreur export aberrantes basses: {e}")
        return False

    return True


def main():
    if not INPUT_PATH.is_file():
        print(f"Fichier introuvable: {INPUT_PATH}")
        sys.exit(1)

    print("NETTOYAGE old_dataset GÉOCODÉES - FILTRAGE COMPLET (HAUT + BAS)")

    # Charger et préparer
    df = load_and_prepare(INPUT_PATH)

    # Supprimer colonnes vides
    df = remove_empty_columns(df)

    # Analyser distribution et trouver seuils
    seuil_bas, seuil_haut = analyze_distribution(df)

    # Filtrage
    df_normal, df_aberrantes_basse, df_aberrantes_haute = apply_filter(df, seuil_bas, seuil_haut)

    # Analyser aberrantes basses
    analyze_aberrantes_basses(df_aberrantes_basse)

    # Analyser aberrantes hautes
    analyze_aberrantes_hautes(df_aberrantes_haute)

    # Analyser normales
    analyze_normal(df_normal)

    # Export
    if export_data(df_normal, df_aberrantes_basse, df_aberrantes_haute):
        print("NETTOYAGE COMPLÉTÉ AVEC SUCCÈS")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()