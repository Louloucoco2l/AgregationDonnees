"""
    Pipeline de nettoyage complet pour annonces immobilières scrappées

    Étapes:
    1. Fusion des fichiers bruts par source
    2. Nettoyage des données (prix, surface, type)
    3. Normalisation géolocalisation (codes 75XXX)
    4. Suppression des doublons
    5. Validation et export final
"""

import os
import glob
import re
import pandas as pd
import sys


class AnnoncesCleaner:
    """Pipeline de nettoyage pour annonces scrappées"""

    def __init__(self):
        """Initialise les chemins"""
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.current_dir, "..", "..", ".."))
        self.base_dir = os.path.join(self.project_root, "data", "scrapped")

        # Créer répertoire s'il n'existe pas
        os.makedirs(self.base_dir, exist_ok=True)

        self.expected_columns = [
            "type", "prix", "prix_m2", "surface",
            "nb_pieces", "localisation", "details"
        ]

    def find_scrapped_files(self):
        """Localise tous les fichiers scrappés"""
        pattern = os.path.join(self.base_dir, "annonces_*_paris*.csv")
        files = glob.glob(pattern)
        return sorted(files)

    def detect_source(self, filename):
        """Détecte la source depuis le nom du fichier"""
        name_lower = filename.lower()

        sources_map = {
            "orpi": "orpi",
            "laforet": "laforet",
            "century21": "century21",
            "plaza": "stephane_plaza",
            "lefigaro": "lefigaro"
        }

        for pattern, source in sources_map.items():
            if pattern in name_lower:
                return source

        return "autre"

    def merge_sources(self):
        """Fusionne tous les fichiers scrappés"""
        print("ETAPE 1 - FUSION SOURCES")

        files = [
            "../../../../data/scrapped/annonces_orpi_paris.csv",
            "../../../../data/scrapped/annonces_laforet_paris.csv",
            "../../../../data/scrapped/annonces_century21_paris.csv",
            "../../../../data/scrapped/annonces_stephane_plaza_paris.csv",
            "../../../../data/scrapped/annonces_lefigaro_paris.csv"
        ]

        if not files:
            print("Erreur: Aucun fichier scrappé trouvé dans {}".format(self.base_dir))
            return None

        print("Fichiers trouvés: {}\n".format(len(files)))
        for f in files:
            print("  - {}".format(os.path.basename(f)))

        all_dfs = []

        for filepath in files:
            filename = os.path.basename(filepath)
            print("\nTraitement: {}".format(filename))

            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                print("  Erreur lecture: {}".format(str(e)))
                continue

            # Ajouter colonnes manquantes
            for col in self.expected_columns:
                if col not in df.columns:
                    df[col] = None

            # Sélectionner et ordonner colonnes
            df = df[self.expected_columns]

            # Ajouter source
            source = self.detect_source(filename)
            df["source"] = source

            print("  OK - {} lignes (source: {})".format(len(df), source))
            all_dfs.append(df)

        if not all_dfs:
            print("\nErreur: Aucun dataframe à fusionner")
            return None

        df_merged = pd.concat(all_dfs, ignore_index=True)

        output_path = os.path.join(self.base_dir, "annonces_paris_merged.csv")
        df_merged.to_csv(output_path, sep=";", index=False, encoding="utf-8")

        print("Fusion terminée: {} lignes".format(len(df_merged)))
        print("Fichier généré: {}".format(output_path))

        return df_merged

    def clean_prix(self, val):
        """Nettoie prix: '509 000 €' → 509000.0"""
        if pd.isna(val):
            return None

        s = str(val).lower().strip().replace("\xa0", " ")

        if "non disponible" in s or "aucun" in s:
            return None

        if "€" in s:
            s = s.split("€")[0]

        s = s.replace(" ", "").replace(",", ".")

        digits = "".join(c for c in s if c.isdigit() or c == ".")

        try:
            return float(digits) if digits else None
        except ValueError:
            return None

    def clean_surface(self, val):
        """Nettoie surface: '71 m²' → 71.0"""
        if pd.isna(val):
            return None

        s = str(val).lower().strip().replace("\xa0", " ")

        if "non disponible" in s or "aucun" in s:
            return None

        for token in ["m²", "m2", " m", "m"]:
            s = s.replace(token, "")

        s = s.replace(" ", "").replace(",", ".")

        digits = "".join(c for c in s if c.isdigit() or c == ".")

        try:
            return float(digits) if digits else None
        except ValueError:
            return None

    def clean_prix_m2(self, val):
        """Nettoie prix/m² si présent"""
        if pd.isna(val):
            return None

        s = str(val).lower().strip().replace("\xa0", " ")

        if "non disponible" in s or "aucun" in s:
            return None

        for token in ["soit", "/m2", "/m²", "/ m2", "/ m²"]:
            s = s.replace(token, "")

        if "€" in s:
            s = s.split("€")[0]

        s = s.replace(" ", "").replace(",", ".")

        digits = "".join(c for c in s if c.isdigit() or c == ".")

        try:
            return float(digits) if digits else None
        except ValueError:
            return None

    def clean_type(self, type_val, details_val):
        """Normalise type de bien"""
        t = "" if pd.isna(type_val) else str(type_val).lower().strip()
        d = "" if pd.isna(details_val) else str(details_val).lower().strip()

        # Pas de type → chercher dans details
        if t == "" or "non disponible" in t or "à vendre" in t or "a vendre" in t:
            if "appartement" in d or "appart" in d:
                return "Appartement"
            return None

        if "appartement" in t or "appart" in t or "duplex" in t or "loft" in t:
            return "Appartement"

        if "maison" in t:
            return "Maison"

        if "locaux" in t or "commercial" in t or "bureau" in t:
            return "Locaux"

        if "garage" in t or "parking" in t:
            return "Garage"

        # Types à supprimer
        if any(x in t for x in ["peniche", "viager", "hotel", "immeuble", "propriet"]):
            return None

        # Couper avant "à vendre" ou "a vendre"
        if " à " in t:
            t = t.split(" à ")[0].strip()
        elif " a " in t:
            t = t.split(" a ")[0].strip()

        return t.capitalize() if t else None

    def clean_nb_pieces(self, val):
        """Extrait nombre de pièces"""
        if pd.isna(val):
            return None

        s = str(val).lower()
        m = re.search(r"\d+", s)

        if not m:
            return None

        try:
            return int(m.group())
        except ValueError:
            return None

    def clean_localisation(self, val):
        """Extrait code postal 75XXX"""
        if pd.isna(val):
            return None

        s = str(val).strip().lower()

        if s == "":
            return None

        # Chercher code postal 75XXX
        m = re.search(r"\b75\d{3}\b", s)
        if m:
            return m.group().upper()

        # Chercher arrondissement (1-20)
        m_arr = re.match(r"^\s*(\d{1,2})(er|ème|eme|e)?\b", s)
        if m_arr:
            arr = int(m_arr.group(1))
            if 1 <= arr <= 20:
                return "75{:03d}".format(arr)

        return None

    def clean_data(self, df):
        """Nettoie les colonnes numeriques et catégories"""
        print("ETAPE 2 - NETTOYAGE DONNEES")

        print("Nettoyage type de bien...")
        df["type"] = df.apply(
            lambda row: self.clean_type(row["type"], row["details"]),
            axis=1
        )

        print("Suppression types invalides...")
        avant = len(df)
        df = df[df["type"].notna()]
        df = df[df["type"].str.strip() != ""]
        apres = len(df)
        print("  Lignes supprimées: {}".format(avant - apres))

        print("\nNettoyage données numériques...")
        df["prix_num"] = df["prix"].apply(self.clean_prix)
        df["surface_num"] = df["surface"].apply(self.clean_surface)
        df["prix_m2_num"] = df["prix_m2"].apply(self.clean_prix_m2)

        # Calculer prix/m² manquant
        print("Calcul prix/m² manquant...")
        mask = (
                df["prix_m2_num"].isna() &
                df["prix_num"].notna() &
                df["surface_num"].notna() &
                (df["surface_num"] > 0)
        )
        df.loc[mask, "prix_m2_num"] = df.loc[mask, "prix_num"] / df.loc[mask, "surface_num"]
        df["prix_m2_num"] = df["prix_m2_num"].round(2)

        print("Nettoyage localisation...")
        df["localisation_clean"] = df["localisation"].apply(self.clean_localisation)

        print("Nettoyage nb_pieces...")
        df["nb_pieces_num"] = df["nb_pieces"].apply(self.clean_nb_pieces)

        # Supprimer lignes sans surface
        print("\nSuppression lignes sans surface...")
        avant = len(df)
        df = df[df["surface_num"].notna()]
        apres = len(df)
        print("  Lignes supprimées: {}".format(avant - apres))

        # Sélectionner colonnes finales
        df_clean = df[[
            "source", "type", "prix_num", "surface_num",
            "prix_m2_num", "nb_pieces_num", "localisation_clean", "details"
        ]].rename(columns={
            "prix_num": "prix",
            "surface_num": "surface",
            "prix_m2_num": "prix_m2",
            "nb_pieces_num": "nb_pieces",
            "localisation_clean": "localisation"
        })

        print("Nettoyage terminé: {} lignes".format(len(df_clean)))

        return df_clean

    def filter_paris_only(self, df):
        """Filtre uniquement annonces Paris (75XXX)"""
        print("ETAPE 3 - FILTRAGE PARIS UNIQUEMENT")

        avant = len(df)
        df_paris = df[df["localisation"].notna()].copy()
        apres = len(df_paris)

        print("Lignes avec localisation: {} sur {}".format(apres, avant))
        print("Lignes supprimées: {}".format(avant - apres))

        print("\nRépartition par arrondissement:")
        print(df_paris["localisation"].value_counts().sort_index())

        print("Résultat: {} lignes Paris".format(len(df_paris)))

        return df_paris

    def remove_duplicates(self, df):
        """Supprime doublons"""
        print("ETAPE 4 - SUPPRESSION DOUBLONS")

        avant = len(df)

        # Déterminer doublons sur: type + prix + surface + localisation
        duplicates_mask = df.duplicated(
            subset=["type", "prix", "surface", "localisation"],
            keep="first"
        )

        nb_duplicates = duplicates_mask.sum()
        print("Doublons détectés (type + prix + surface + localisation): {}".format(nb_duplicates))

        if nb_duplicates > 0:
            print("\nExemples de doublons:")
            dupes = df[duplicates_mask].head(5)
            for idx, row in dupes.iterrows():
                print("  - {} ({}) - {}€ - {}m²".format(
                    row["type"], row["localisation"], row["prix"], row["surface"]
                ))

        df_uniq = df[~duplicates_mask].reset_index(drop=True)

        apres = len(df_uniq)

        print("Avant: {} lignes".format(avant))
        print("Après: {} lignes".format(apres))
        print("Supprimés: {} doublons".format(nb_duplicates))

        return df_uniq

    def validate_and_export(self, df):
        """Valide et exporte les données finales"""
        print("ETAPE 5 - VALIDATION ET EXPORT")

        print("Statistiques finales:")
        print("  Total lignes: {}".format(len(df)))
        print("  Colonnes: {}".format(len(df.columns)))

        print("\nRépartition par type:")
        print(df["type"].value_counts())

        print("\nRépartition par source:")
        print(df["source"].value_counts())

        print("\nRépartition par arrondissement:")
        print(df["localisation"].value_counts().sort_index())

        # Stats numériques
        for col in ["prix", "surface", "prix_m2"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        print("\nStatistiques numériques:")
        print(df[["prix", "surface", "prix_m2"]].describe())

        # Export
        output_path = os.path.join(self.base_dir, "annonces_paris_final.csv")
        df.to_csv(output_path, sep=";", index=False, encoding="utf-8")

        print("Fichier généré: {}".format(output_path))

        return output_path

    def run_pipeline(self):
        """Exécute le pipeline complet"""
        print("PIPELINE NETTOYAGE ANNONCES SCRAPPEES")
        print("Répertoire base: {}".format(self.base_dir))
        print()

        # Étape 1: Fusion
        df_merged = self.merge_sources()
        if df_merged is None:
            return False

        # Étape 2: Nettoyage
        df_clean = self.clean_data(df_merged)

        # Étape 3: Filtrage Paris
        df_paris = self.filter_paris_only(df_clean)

        # Étape 4: Doublons
        df_unique = self.remove_duplicates(df_paris)

        # Étape 5: Export
        output_path = self.validate_and_export(df_unique)

        print("PIPELINE COMPLETE - SUCCESS")

        return True


def main():
    cleaner = AnnoncesCleaner()
    success = cleaner.run_pipeline()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()