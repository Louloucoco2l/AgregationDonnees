#agrege depuis les differents datasets temporels tout ce qui pourrait correpondre a Paris
#il reste encore des ventes non effectuees a paris, aucune colonne n a ete supprimee
#calcule le prix moyen au m² avec les colonnes valeur fonciere et surface reelle bati/surface terrain

import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

fichiers = [
    "../../../../data/old_dataset/brut/valeursfoncieres-2020-s2.txt",
    "../../../../data/old_dataset/brut/valeursfoncieres-2021.txt",
    "../../../../data/old_dataset/brut/valeursfoncieres-2022.txt",
    "../../../../data/old_dataset/brut/valeursfoncieres-2023.txt",
    "../../../../data/old_dataset/brut/valeursfoncieres-2024.txt",
    "../../../../data/old_dataset/brut/valeursfoncieres-2025-s1.txt"
]

colonnes = [
    "Identifiant de document",
    "Reference document",
    "1 Articles CGI",
    "2 Articles CGI",
    "3 Articles CGI",
    "4 Articles CGI",
    "5 Articles CGI",
    "No disposition",
    "Date mutation",
    "Nature mutation",
    "Valeur fonciere",
    "No voie",
    "B/T/Q",
    "Type de voie",
    "Code voie",
    "Voie",
    "Code postal",
    "Commune",
    "Code departement",
    "Code commune",
    "Prefixe de section",
    "Section",
    "No plan",
    "No Volume",
    "1er lot",
    "Surface Carrez du 1er lot",
    "2eme lot",
    "Surface Carrez du 2eme lot",
    "3eme lot",
    "Surface Carrez du 3eme lot",
    "4eme lot",
    "Surface Carrez du 4eme lot",
    "5eme lot",
    "Surface Carrez du 5eme lot",
    "Nombre de lots",
    "Code type local",
    "Type local",
    "Identifiant local",
    "Surface reelle bati",
    "Nombre pieces principales",
    "Nature culture",
    "Nature culture speciale",
    "Surface terrain"
]

fichier_sortie = os.path.join(base_dir, "../../../../data/old_dataset/cleaned/valeursfoncieres-paris-2020-2025.2.csv")

#traite par paquets, plus digeste
chunksize = 500000

for fichier in fichiers:
    chemin = os.path.join(base_dir, fichier)
    if not os.path.exists(chemin):
        print(f"Fichier introuvable : {chemin}")
        continue

    print(f"\nTraitement de : {os.path.basename(chemin)}")

    chunks = pd.read_csv(
        chemin,
        sep='|',
        dtype=str,
        names=colonnes,
        header=0,
        chunksize=chunksize,
        low_memory=False
    )

    for i, chunk in enumerate(chunks):
        chunk = chunk.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Filtrage multi critères Paris
        paris_mask = (
            (chunk["Code postal"].astype(str).str.contains('75', na=False)) &
            (chunk["Commune"].astype(str).str.contains("PARIS", case=False, na=False)) &
            (chunk["Code departement"].astype(str).str.contains('75', na=False))
        )
        paris_chunk = chunk[paris_mask].copy()

        #Ajout de la colonne "Annee"
        annee = fichier.split('-')[1]  # extrait "2020", "2021", "2024", etc.
        paris_chunk["Annee"] = annee

        #ecriture append
        mode = 'a' if os.path.exists(fichier_sortie) else 'w'
        header = not os.path.exists(fichier_sortie)
        paris_chunk.to_csv(
            fichier_sortie,
            sep=';',
            index=False,
            encoding='utf-8',
            header=header,
            mode=mode,
            quoting=1
        )

        print(f"Chunk {i+1}: {len(paris_chunk)} lignes ajoutées ({annee})")

print(f"\nFusion complète terminée : {fichier_sortie}")