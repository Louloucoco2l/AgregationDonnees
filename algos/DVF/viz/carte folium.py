"""
    Génère une carte interactive Folium avec coloration réelle des arrondissements
    - Utilise le vrai GeoJSON polygonal de Paris
    - Choroplèthe basée sur prix moyen au m²
    - Tooltips interactifs
    - Légende
"""

import os
import pandas as pd
import folium
import json

INPUT_PATH = "../../../datas/DVF/geocodes/tableau/dvfgeo_tableau_arrondissements.csv"
GEOJSON_PATH = "../../../datas/arrondissements.geojson"
OUTPUT_FILE = "../../../plots/DVF/carte_paris_heatmap.1.html"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def load_data(filepath):
    """Charge données arrondissements"""
    print("Chargement: " + os.path.basename(filepath))
    df = pd.read_csv(filepath, sep=';')
    print("OK - {} lignes\n".format(len(df)))
    return df


def load_geojson(filepath):
    """Charge GeoJSON polygonal des arrondissements"""
    print("Chargement GeoJSON arrondissements…")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"GeoJSON introuvable : {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("OK - GeoJSON chargé\n")
    return data


def create_map(df, geojson):
    """Crée la carte Folium"""

    print("=" * 70)
    print("Creation carte Folium")
    print("=" * 70 + "\n")

    # Centre de Paris
    center = [48.8566, 2.3522]

    # Créer carte
    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # borne couleurs
    min_prix = df['prix_m2_moyen'].min()
    max_prix = df['prix_m2_moyen'].max()

    print(f"Prix min : {min_prix:.0f} €/m²")
    print(f"Prix max : {max_prix:.0f} €/m²\n")

    # CHOROPLETHE — coloration réelle des arrondissements
    choropleth = folium.Choropleth(
        geo_data=geojson,
        name="Choroplèthe prix/m2",
        data=df,
        columns=["arrondissement", "prix_m2_moyen"],
        key_on="feature.properties.c_ar",   # champ du GeoJSON (numéro arrondissement)
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.6,
        line_color="black",
        nan_fill_color="grey",
        legend_name="Prix moyen au m²",
    ).add_to(m)

    # TOOLTIP (nom + numéro arrondissement)
    folium.GeoJson(
        geojson,
        name="Arrondissements",
        tooltip=folium.features.GeoJsonTooltip(
            fields=["l_ar"],
            aliases=["Arrondissement :"],
            localize=True,
            sticky=True
        )
    ).add_to(m)

    # POPUPS — afficher prix, transactions, surface, etc.
    for idx, row in df.iterrows():
        arr = int(row["arrondissement"])
        prix = row["prix_m2_moyen"]
        median = row["prix_m2_median"]
        trans = row["nombre_transactions"]
        surf = row["surface_moyenne"]
        nom = row["nom_arrondissement"]

        popup_html = f"""
        <b>{nom}</b><br>
        Prix moyen : {prix:.0f} €/m²<br>
        Prix médian : {median:.0f} €/m²<br>
        Transactions : {trans:,}<br>
        Surface moyenne : {surf:.0f} m²
        """

        # on place le popup sur le barycentre de l'arrondissement
        if not pd.isna(row["latitude"]) and not pd.isna(row["longitude"]):
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

    # couche
    folium.LayerControl().add_to(m)

    return m


def main():
    print("=" * 70)
    print("GENERATION CARTE INTERACTIVE - DVFGeo")
    print("=" * 70 + "\n")

    # Charger données
    df = load_data(INPUT_PATH)

    # Charger GeoJSON polygonal
    geojson = load_geojson(GEOJSON_PATH)

    # Créer carte
    m = create_map(df, geojson)

    # Sauvegarder
    m.save(OUTPUT_FILE)

    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print("\nFichier genere : {}".format(OUTPUT_FILE))
    print("Ouvrir dans navigateur pour voir la carte")


if __name__ == "__main__":
    main()
