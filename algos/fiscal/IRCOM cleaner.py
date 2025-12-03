"""
    Nettoyeur de données fiscales DGFiP - IRCOM revenus
    Extrait les données par arrondissement depuis excels en supprimant les lignes de somme
    Agrège les données de 2020 à 2023
"""

import pandas as pd
import os
import sys

INPUT_DIR = "../../datas/fiscal"
OUTPUT_DIR = "./"
OUTPUT_FILE = "ircom_2020-2023_paris_clean.csv"

# Fichiers à agréger
FICHIERS_ANNEES = {
    "2020": "2020.xlsx",
    "2021": "2021.xlsx",
    "2022": "2022.xlsx",
    "2023": "2023.xlsx"
}


class IRCOMCleaner:
    """Pipeline de nettoyage pour données fiscales IRCOM"""

    def __init__(self, fichier_input, annee):
        """
        Initialise le cleaner
        Args:
            fichier_input: Chemin vers le fichier Excel IRCOM
            annee: Année des données (ex: '2020')
        """
        self.fichier_input = fichier_input
        self.annee = str(annee)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        self.data_start_row = 20

        self.colonnes_finales = [
            'annee', 'dep', 'code_commune', 'libelle_commune', 'tranche_rfr',
            'nb_foyers_fiscaux', 'rfr_foyers_fiscaux', 'impot_net_total',
            'nb_foyers_imposes', 'rfr_foyers_imposes',
            'traitements_salaires_nb_foyers', 'traitements_salaires_montant',
            'retraites_pensions_nb_foyers', 'retraites_pensions_montant'
        ]

        self.colonnes_numeriques = [
            'nb_foyers_fiscaux', 'rfr_foyers_fiscaux', 'impot_net_total',
            'nb_foyers_imposes', 'rfr_foyers_imposes',
            'traitements_salaires_nb_foyers', 'traitements_salaires_montant',
            'retraites_pensions_nb_foyers', 'retraites_pensions_montant'
        ]

    def load_data(self):
        """Charge le fichier Excel"""
        print("CHARGEMENT")

        if not os.path.exists(self.fichier_input):
            print(f"Erreur: Fichier introuvable: {self.fichier_input}")
            return None

        print(f"Chargement: {os.path.basename(self.fichier_input)}")

        try:
            df_raw = pd.read_excel(self.fichier_input)
        except Exception as e:
            print(f"Erreur lecture: {e}")
            return None

        print(f"  Fichier chargé: {df_raw.shape[0]} lignes x {df_raw.shape[1]} colonnes")

        df_data = df_raw.iloc[self.data_start_row:].copy()

        df_data.columns = [
            'colonne_0', 'dep', 'code_commune', 'libelle_commune',
            'tranche_rfr', 'nb_foyers_fiscaux', 'rfr_foyers_fiscaux',
            'impot_net_total', 'nb_foyers_imposes', 'rfr_foyers_imposes',
            'traitements_salaires_nb_foyers', 'traitements_salaires_montant',
            'retraites_pensions_nb_foyers', 'retraites_pensions_montant'
        ]

        df_data = df_data.drop('colonne_0', axis=1)

        print(f"  Données extraites: {len(df_data)} lignes")

        return df_data

    def clean_data(self, df):
        """Nettoie et filtre les données"""
        print("NETTOYAGE ET FILTRAGE")

        # Supprimer les lignes vides
        avant = len(df)
        df = df.dropna(how='all')
        apres = len(df)
        if avant - apres > 0:
            print(f"  Lignes vides supprimées: {avant - apres}")

        # Supprimer dep NaN
        avant = len(df)
        df = df[df['dep'].notna()]
        apres = len(df)
        if avant - apres > 0:
            print(f"  Lignes sans département supprimées: {avant - apres}")

        # Supprimer Total
        avant = len(df)
        df = df[df['tranche_rfr'].astype(str).str.lower().str.strip() != 'total']
        apres = len(df)
        print(f"  Lignes 'Total' supprimées: {avant - apres}")

        # Supprimer lignes *
        avant = len(df)
        df = df[~df['dep'].astype(str).str.contains('\\*', na=False)]
        apres = len(df)
        if avant - apres > 0:
            print(f"  Lignes de notes supprimées: {avant - apres}")

        # Supprimer code_commune NaN
        avant = len(df)
        df = df[df['code_commune'].notna()]
        apres = len(df)
        if avant - apres > 0:
            print(f"  Lignes département agrégé supprimées: {avant - apres}")

        print(f"\n  Lignes restantes: {len(df)}")

        return df

    def convert_types(self, df):
        """Convertit les types de données"""
        print("CONVERSION DES TYPES")

        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()

        for col in self.colonnes_numeriques:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['annee'] = self.annee

        df_clean = df[self.colonnes_finales].copy()

        print(f"  Colonnes finales: {len(df_clean.columns)}")
        print(f"  Lignes finales: {len(df_clean)}")

        return df_clean

    def validate_and_stats(self, df):
        """Affiche les statistiques de validation"""
        print("STATISTIQUES ET VALIDATION")

        print("Répartition par arrondissement:")
        for commune, count in df['libelle_commune'].value_counts().sort_index().items():
            print(f"  {commune}: {count} lignes")

        print("\nRépartition par tranche de RFR:")
        for tranche, count in df['tranche_rfr'].value_counts().items():
            print(f"  {tranche}: {count} lignes")

        print("\nStatistiques sur nb_foyers_fiscaux:")
        stats = df['nb_foyers_fiscaux'].describe()
        print(f"  Moyenne: {stats['mean']:,.0f}")
        print(f"  Médiane: {stats['50%']:,.0f}")
        print(f"  Min: {stats['min']:,.0f}")
        print(f"  Max: {stats['max']:,.0f}")

        print(f"\nTotal foyers fiscaux: {df['nb_foyers_fiscaux'].sum():,.0f}")
        print(f"Total RFR: {df['rfr_foyers_fiscaux'].sum():,.0f} k€")
        print(f"Total impôt net: {df['impot_net_total'].sum():,.0f} k€")

        return True

    def export_data(self, df, output_file):
        """Exporte les données nettoyées"""
        print("EXPORT")

        try:
            df.to_csv(output_file, sep=';', index=False, encoding='utf-8', quoting=1)
            print(f"Fichier généré: {output_file}")
            print(f"  Lignes exportées: {len(df)}")
            print(f"  Colonnes exportées: {len(df.columns)}")
            return True
        except Exception as e:
            print(f"Erreur export: {e}")
            return False

    def run_pipeline(self):
        """Exécute le pipeline complet pour une année"""
        print(f"NETTOYAGE DONNÉES FISCALES IRCOM {self.annee}")

        df = self.load_data()
        if df is None:
            return None

        df = self.clean_data(df)
        df = self.convert_types(df)

        self.validate_and_stats(df)

        return df


def main():
    """Point d'entrée principal - Agrège les 4 années"""

    print("AGRÉGATION DONNÉES FISCALES IRCOM 2020-2023")

    dfs_annees = []

    for annee, fichier in FICHIERS_ANNEES.items():
        fichier_path = os.path.join(INPUT_DIR, fichier)

        print(f"TRAITEMENT ANNÉE {annee}")

        if not os.path.exists(fichier_path):
            print(f"Fichier introuvable: {fichier_path}")
            print(f"   Année {annee} ignorée\n")
            continue

        cleaner = IRCOMCleaner(fichier_path, annee)
        df_annee = cleaner.run_pipeline()

        if df_annee is not None:
            dfs_annees.append(df_annee)
            print(f"Année {annee} traitée: {len(df_annee)} lignes")
        else:
            print(f"✗ Erreur traitement année {annee}")

    if len(dfs_annees) == 0:
        print("ERREUR: Aucune donnée n'a pu être chargée")
        sys.exit(1)

    print("AGRÉGATION DES DONNÉES")

    df_final = pd.concat(dfs_annees, ignore_index=True)

    print(f"Années agrégées: {len(dfs_annees)}")
    print(f"Total lignes: {len(df_final)}")
    print(f"Colonnes: {len(df_final.columns)}")

    print("STATISTIQUES GLOBALES")

    print("Répartition par année:")
    for annee, count in df_final['annee'].value_counts().sort_index().items():
        print(f"  {annee}: {count:,} lignes")

    print("\nRépartition par arrondissement (toutes années):")
    for commune, count in df_final['libelle_commune'].value_counts().sort_index().items():
        print(f"  {commune}: {count} lignes")

    print(f"\nTotal foyers fiscaux (toutes années): {df_final['nb_foyers_fiscaux'].sum():,.0f}")
    print(f"Total RFR (toutes années): {df_final['rfr_foyers_fiscaux'].sum():,.0f} k€")
    print(f"Total impôt net (toutes années): {df_final['impot_net_total'].sum():,.0f} k€")

    print("EXPORT FICHIER FINAL")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    try:
        df_final.to_csv(output_path, sep=';', index=False, encoding='utf-8', quoting=1)
        print(f"Fichier généré: {output_path}")
        print(f"Lignes exportées: {len(df_final):,}")
        print(f"Colonnes exportées: {len(df_final.columns)}")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
