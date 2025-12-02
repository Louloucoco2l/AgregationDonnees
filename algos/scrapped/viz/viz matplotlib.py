"""
    Visualisations PNG des annonces scrappées
    - Distribution prix/m² par source
    - Comparaison arrondissements
    - Heatmap type x arrondissement
    - Distribution par nombre de pièces
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

INPUT_PATH = "../../../datas/scrapped/annonces_paris_clean_final.csv"
OUTPUT_DIR = "../../../plots/scrapped/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_data():
    """Charge les données scrappées"""
    print("Chargement des donnees...")
    df = pd.read_csv(INPUT_PATH, sep=';')

    # Extraire numéro arrondissement (75007 -> 7)
    df['arrondissement'] = df['localisation'].astype(str).str.extract(r'750?(\d{1,2})').astype(float)

    print(f"OK - {len(df)} annonces\n")
    return df


def plot_distribution_prix_source(df):
    """Distribution prix/m² par source"""
    print("Creation: distribution_prix_source.png")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Boxplot par source
    sns.boxplot(data=df, x='source', y='prix_m2', ax=axes[0], palette='Set2')
    axes[0].set_xlabel('Source', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Prix (€/m²)', fontsize=12, fontweight='bold')
    axes[0].set_title('Distribution prix/m² par source', fontsize=14, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=45)

    # Histogramme global
    for source in df['source'].unique():
        subset = df[df['source'] == source]['prix_m2'].dropna()
        axes[1].hist(subset, bins=50, alpha=0.5, label=source)

    axes[1].set_xlabel('Prix (€/m²)', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Fréquence', fontsize=12, fontweight='bold')
    axes[1].set_title('Histogramme prix/m² par source', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'distribution_prix_source.png'), dpi=150)
    plt.close()
    print("OK\n")


def plot_classement_arrondissements(df):
    """Classement des arrondissements par prix moyen"""
    print("Creation: classement_arrondissements.png")

    # Agrégation par arrondissement
    df_arr = df.groupby('arrondissement').agg({
        'prix_m2': ['mean', 'median', 'count']
    }).reset_index()
    df_arr.columns = ['arrondissement', 'prix_m2_moyen', 'prix_m2_median', 'nb_annonces']
    df_arr = df_arr.sort_values('prix_m2_moyen', ascending=False)
    df_arr['nom'] = df_arr['arrondissement'].apply(lambda x: f"75{int(x):02d}")

    fig, ax = plt.subplots(figsize=(12, 10))

    colors = plt.cm.RdYlGn(np.linspace(0, 1, len(df_arr)))
    bars = ax.barh(df_arr['nom'], df_arr['prix_m2_moyen'], color=colors)

    ax.set_xlabel('Prix moyen (€/m²)', fontsize=12, fontweight='bold')
    ax.set_title('Classement des arrondissements par prix au m² (Annonces scrappées)',
                 fontsize=14, fontweight='bold')

    for i, (idx, row) in enumerate(df_arr.iterrows()):
        ax.text(row['prix_m2_moyen'] + 100, i, f"{row['prix_m2_moyen']:.0f}€ ({int(row['nb_annonces'])})",
                va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'classement_arrondissements.png'), dpi=150)
    plt.close()
    print("OK\n")


def plot_heatmap_type_arrond(df):
    """Heatmap prix par type x arrondissement"""
    print("Creation: heatmap_type_arrondissement.png")

    pivot = df.pivot_table(
        values='prix_m2',
        index='type',
        columns='arrondissement',
        aggfunc='mean'
    )

    fig, ax = plt.subplots(figsize=(16, 6))

    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='RdYlGn_r',
                cbar_kws={'label': 'Prix (€/m²)'}, ax=ax, linewidths=0.5)

    ax.set_xlabel('Arrondissement', fontsize=12, fontweight='bold')
    ax.set_ylabel('Type de bien', fontsize=12, fontweight='bold')
    ax.set_title('Heatmap: Prix au m² par type et arrondissement (Scrappé)',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'heatmap_type_arrondissement.png'), dpi=150)
    plt.close()
    print("OK\n")


def plot_distribution_pieces(df):
    """Distribution par nombre de pièces"""
    print("Creation: distribution_pieces.png")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Boxplot prix/m² par nb pièces
    df_pieces = df[df['nb_pieces'].notna() & (df['nb_pieces'] <= 6)]
    sns.boxplot(data=df_pieces, x='nb_pieces', y='prix_m2', ax=axes[0], palette='coolwarm')
    axes[0].set_xlabel('Nombre de pièces', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Prix (€/m²)', fontsize=12, fontweight='bold')
    axes[0].set_title('Prix/m² par nombre de pièces', fontsize=14, fontweight='bold')

    # Comptage par nb pièces
    pieces_count = df_pieces['nb_pieces'].value_counts().sort_index()
    axes[1].bar(pieces_count.index.astype(int), pieces_count.values, color='steelblue', alpha=0.7)
    axes[1].set_xlabel('Nombre de pièces', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Nombre d\'annonces', fontsize=12, fontweight='bold')
    axes[1].set_title('Volume d\'annonces par nombre de pièces', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'distribution_pieces.png'), dpi=150)
    plt.close()
    print("OK\n")


def plot_prix_surface(df):
    """Scatter plot prix vs surface"""
    print("Creation: prix_surface.png")

    fig, ax = plt.subplots(figsize=(12, 8))

    for source in df['source'].unique():
        subset = df[df['source'] == source]
        ax.scatter(subset['surface'], subset['prix'], alpha=0.5, s=20, label=source)

    ax.set_xlabel('Surface (m²)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Prix (€)', fontsize=12, fontweight='bold')
    ax.set_title('Prix vs Surface par source', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'prix_surface.png'), dpi=150)
    plt.close()
    print("OK\n")


def plot_volume_source(df):
    """Volume d'annonces par source"""
    print("Creation: volume_source.png")

    fig, ax = plt.subplots(figsize=(10, 6))

    source_counts = df['source'].value_counts()
    bars = ax.bar(source_counts.index, source_counts.values, color='teal', alpha=0.7, edgecolor='black')

    ax.set_xlabel('Source', fontsize=12, fontweight='bold')
    ax.set_ylabel('Nombre d\'annonces', fontsize=12, fontweight='bold')
    ax.set_title('Volume d\'annonces par source', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)

    for bar, val in zip(bars, source_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50, str(val),
                ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'volume_source.png'), dpi=150)
    plt.close()
    print("OK\n")


def main():
    print("=" * 70)
    print("VISUALISATIONS - ANNONCES SCRAPPÉES")
    print("=" * 70 + "\n")

    df = load_data()

    print("=" * 70)
    print("CREATION GRAPHIQUES")
    print("=" * 70 + "\n")

    plot_distribution_prix_source(df)
    plot_classement_arrondissements(df)
    plot_heatmap_type_arrond(df)
    plot_distribution_pieces(df)
    plot_prix_surface(df)
    plot_volume_source(df)

    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nFichiers generes dans: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()