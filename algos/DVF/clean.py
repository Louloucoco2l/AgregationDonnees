"""
    Script final : sépare les données DVF Paris en NORMALES et ABERRANTES
    Utilise la méthode IQR pour détecter les outliers

    Critères de filtrage :
    - Seuil bas IQR : 2 172€/m² (Q1 - 1.5*IQR)
    - Seuil haut IQR : 18 999€/m² (Q3 + 1.5*IQR)
"""
import os
import sys
import pandas as pd

INPUT_PATH = "../../datas/downloaded/cleaned/valeursfoncieres-paris-2020-2025.1-exploitables.csv"
OUTPUT_NORMAL = INPUT_PATH.replace('.csv', '-final.csv')
OUTPUT_ABERRANTES = INPUT_PATH.replace('-normal.csv', '-aberrantes-final.csv')

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

    # Surface composite
    df['Surface'] = df['Surface reelle bati'].fillna(df['Surface terrain'])

    # Prix au m²
    df['Prix_m2'] = df.apply(
        lambda row: round(row['Valeur fonciere'] / row['Surface'], 2)
        if pd.notna(row['Valeur fonciere'])
           and pd.notna(row['Surface'])
           and row['Surface'] > 0
        else None,
        axis=1
    )

    return df

def apply_iqr_filter(df):
    """Applique le filtrage IQR"""

    # Calcul des seuils
    Q1 = df['Prix_m2'].quantile(0.25)
    Q3 = df['Prix_m2'].quantile(0.75)
    IQR = Q3 - Q1

    seuil_bas = Q1 - 1.5 * IQR
    seuil_haut = Q3 + 1.5 * IQR

    print("\n" + "="*70)
    print("FILTRAGE IQR")
    print("="*70)
    print(f"Q1: {Q1:>10,.0f}€/m²")
    print(f"Q3: {Q3:>10,.0f}€/m²")
    print(f"IQR: {IQR:>10,.0f}€/m²")
    print(f"\nSeuils d'aberrance:")
    print(f"  Bas: {seuil_bas:>10,.0f}€/m²")
    print(f"  Haut: {seuil_haut:>10,.0f}€/m²")

    # Séparation
    mask_normal = (df['Prix_m2'] >= seuil_bas) & (df['Prix_m2'] <= seuil_haut)
    df_normal = df[mask_normal].copy()
    df_aberrantes = df[~mask_normal].copy()

    print(f"\nRésultats:")
    print(f"  Lignes normales: {len(df_normal):>8} ({len(df_normal)/len(df)*100:>5.1f}%)")
    print(f"  Lignes aberrantes: {len(df_aberrantes):>8} ({len(df_aberrantes)/len(df)*100:>5.1f}%)")

    return df_normal, df_aberrantes, seuil_bas, seuil_haut

def analyze_aberrantes(df_aberrantes):
    """Analyse les aberrantes"""

    print("\n" + "="*70)
    print("ANALYSE DES ABERRANTES")
    print("="*70)

    print("\nRépartition par type de local:")
    type_counts = df_aberrantes['Type local'].value_counts()
    for tlocal, count in type_counts.head(10).items():
        pct = count / len(df_aberrantes) * 100
        print(f"  {str(tlocal)[:40]:40s}: {count:>6} ({pct:>5.1f}%)")

    print("\nPrix/m² des aberrantes:")
    print(f"  Min: {df_aberrantes['Prix_m2'].min():>10,.0f}€/m²")
    print(f"  Max: {df_aberrantes['Prix_m2'].max():>10,.0f}€/m²")
    print(f"  Médiane: {df_aberrantes['Prix_m2'].median():>10,.0f}€/m²")
    print(f"  Moyenne: {df_aberrantes['Prix_m2'].mean():>10,.0f}€/m²")

def export_data(df_normal, df_aberrantes):
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
        df_aberrantes.to_csv(OUTPUT_ABERRANTES, sep=';', index=False, encoding='utf-8')
        print(f"✓ {len(df_aberrantes)} lignes aberrantes")
        print(f"  → {OUTPUT_ABERRANTES}")
    except Exception as e:
        print(f"Erreur export aberrantes: {e}")
        return False

    return True

def main():
    if not os.path.isfile(INPUT_PATH):
        print(f"Fichier introuvable: {INPUT_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"Chargement: {os.path.basename(INPUT_PATH)}")
    df = load_and_prepare(INPUT_PATH)
    print(f"✓ {len(df)} lignes chargées")

    # Filtrage IQR
    df_normal, df_aberrantes, sb, sh = apply_iqr_filter(df)

    # Analyse des aberrantes
    analyze_aberrantes(df_aberrantes)

    # Export
    if export_data(df_normal, df_aberrantes):
        print("\n" + "="*70)
        print("Traitement complété avec succès")
        print("="*70)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()