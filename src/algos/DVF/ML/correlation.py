import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from src.config import paths

INPUT_PATH = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_DIR = paths.plots.DVF.path

def main():

    df = pd.read_csv(INPUT_PATH, sep=';', low_memory=False)
    corr = df[['valeur_fonciere','adresse_numero','code_postal','code_commune','surface_reelle_bati','nombre_pieces_principales','surface_terrain','longitude','latitude','annee','surface_m2_retenue','prix_m2','code_arrondissement','mois']].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
    plt.savefig(OUTPUT_DIR/'correlation_matrix.png', dpi=150)
    print("Matrice de correlation sauvegardee.")

if __name__ == "__main__":
    main()