"""
    Génère visualisations PNG avec matplotlib
    - Série temporelle
    - Distribution prix/m²
    - Comparaison arrondissements
    - Heatmap type x arrondissement
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from src.config import paths

INPUT_TEMPOREL = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_temporel.csv"
INPUT_ARROND = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_arrondissements.csv"
INPUT_TYPE = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_type_local.csv"
OUTPUT_DIR = paths.plots.DVF.path

# Configuration matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_data():
    """Charge les 3 datasets"""
    print("Chargement des donnees...")
    df_temp = pd.read_csv(INPUT_TEMPOREL, sep=';')
    df_arr = pd.read_csv(INPUT_ARROND, sep=';')
    df_type = pd.read_csv(INPUT_TYPE, sep=';')
    print("OK\n")
    return df_temp, df_arr, df_type


def plot_serie_temporelle(df_temp):
    """Evolution prix/m² par arrondissement sur le temps"""
    print("Creation: serie_temporelle.png")

    fig, ax = plt.subplots(figsize=(14, 8))

    for arr in sorted(df_temp['arrondissement'].unique()):
        subset = df_temp[df_temp['arrondissement'] == arr].sort_values('annee')
        ax.plot(subset['annee'], subset['prix_m2_moyen'],
                marker='o', label='75{:02d}'.format(int(arr)), linewidth=2)

    ax.set_xlabel('Annee', fontsize=12, fontweight='bold')
    ax.set_ylabel('Prix moyen (€/m²)', fontsize=12, fontweight='bold')
    ax.set_title('Evolution du prix au m² par arrondissement (2020-2025)',
                 fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2, fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'serie_temporelle.png', dpi=150)
    plt.close()
    print("OK\n")

def plot_serie_temporelle(df_temp):
    """Evolution prix/m² par arrondissement sur le temps"""
    print("Creation: serie_temporelle.png")

    fig, ax = plt.subplots(figsize=(14, 8))

    arrs = sorted(df_temp['arrondissement'].unique())
    n_colors = 20
    # Utiliser une palette de 20 couleurs pour une meilleure lisibilité
    #if n_colors <= 20:
    colors = sns.color_palette("tab20", n_colors=n_colors)
    #else:
    #    colors = sns.color_palette("hsv", n_colors=n_colors)

    for arr, color in zip(arrs, colors):
        subset = df_temp[df_temp['arrondissement'] == arr].sort_values('annee')
        ax.plot(subset['annee'], subset['prix_m2_moyen'],
                marker='o', label='75{:02d}'.format(int(arr)), linewidth=2, color=color)

    ax.set_xlabel('Annee', fontsize=12, fontweight='bold')
    ax.set_ylabel('Prix moyen (€/m²)', fontsize=12, fontweight='bold')
    ax.set_title('Evolution du prix au m² par arrondissement (2020-2025)',
                 fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2, fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'serie_temporelle.png', dpi=150)
    plt.close()
    print("OK\n")


def plot_classement_arrondissements(df_arr):
    """Classement des arrondissements par prix moyen"""
    print("Creation: classement_arrondissements.png")

    df_sorted = df_arr.sort_values('prix_m2_moyen', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 10))

    colors = plt.cm.RdYlGn(np.linspace(0, 1, len(df_sorted)))
    bars = ax.barh(df_sorted['nom_arrondissement'], df_sorted['prix_m2_moyen'], color=colors)

    ax.set_xlabel('Prix moyen (€/m²)', fontsize=12, fontweight='bold')
    ax.set_title('Classement des arrondissements par prix au m² (2020-2025)',
                 fontsize=14, fontweight='bold')

    # Ajouter valeurs sur les barres
    for i, (idx, row) in enumerate(df_sorted.iterrows()):
        ax.text(row['prix_m2_moyen'] + 200, i, '{:.0f}€'.format(row['prix_m2_moyen']),
                va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'classement_arrondissements.png', dpi=150)
    plt.close()
    print("OK\n")


def plot_distribution_prix(df_arr):
    """Distribution des prix moyen entre arrondissements"""
    print("Creation: distribution_prix.png")

    fig, ax = plt.subplots(figsize=(16, 8))


    # Box plot
    plt.boxplot(df_arr['prix_m2_moyen'], vert=True, patch_artist=True,
                boxprops=dict(facecolor='lightblue', alpha=0.7))
    ax.set_ylabel('Prix moyen (€/m²)', fontsize=11, fontweight='bold')
    ax.set_title('Boite a moustaches', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Statistiques
    stats_text = "Moyenne: {:.0f}€/m²\nMediane: {:.0f}€/m²\nEcart-type: {:.0f}€/m²".format(
        df_arr['prix_m2_moyen'].mean(),
        df_arr['prix_m2_moyen'].median(),
        df_arr['prix_m2_moyen'].std()
    )
    plt.text(1.3, df_arr['prix_m2_moyen'].median(), stats_text, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'distribution_prix.png', dpi=150)
    plt.close()
    print("OK\n")


def plot_heatmap_type_arrond(df_type):
    """Heatmap prix par type x arrondissement"""
    print("Creation: heatmap_type_arrondissement.png")

    # Créer matrice
    pivot = df_type.pivot_table(
        values='prix_m2_moyen',
        index='type_local',
        columns='arrondissement',
        aggfunc='first'
    )

    # Créer heatmap
    fig, ax = plt.subplots(figsize=(16, 8))

    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='RdYlGn_r',
                cbar_kws={'label': 'Prix (€/m²)'}, ax=ax, linewidths=0.5)

    ax.set_xlabel('Arrondissement', fontsize=12, fontweight='bold')
    ax.set_ylabel('Type de local', fontsize=12, fontweight='bold')
    ax.set_title('Heatmap: Prix au m² par type de local et arrondissement',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'heatmap_type_arrondissement.png', dpi=150)
    plt.close()
    print("OK\n")


def plot_volume_transactions(df_arr):
    """Volume de transactions par arrondissement"""
    print("Creation: volume_transactions.png")

    df_sorted = df_arr.sort_values('nombre_transactions', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 8))

    bars = ax.bar(range(len(df_sorted)), df_sorted['nombre_transactions'],
                  color='steelblue', alpha=0.7, edgecolor='black')

    ax.set_xticks(range(len(df_sorted)))
    ax.set_xticklabels(df_sorted['nom_arrondissement'], rotation=45, ha='right')
    ax.set_ylabel('Nombre de transactions', fontsize=12, fontweight='bold')
    ax.set_title('Volume de transactions par arrondissement (2020-2025)',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'volume_transactions.png', dpi=150)
    plt.close()
    print("OK\n")


def main():
    print("GENERATION VISUALISATIONS - DVFGeo")

    # Charger données
    df_temp, df_arr, df_type = load_data()

    # Créer visualisations
    print("CREATION GRAPHIQUES")

    plot_serie_temporelle(df_temp)
    plot_classement_arrondissements(df_arr)
    plot_distribution_prix(df_arr)
    plot_heatmap_type_arrond(df_type)
    plot_volume_transactions(df_arr)

    print("GENERATION COMPLETE")
    print("\nFichiers generes dans: {}".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()