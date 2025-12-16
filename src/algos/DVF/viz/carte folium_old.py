"""
    Génère une carte interactive Folium avec heatmap des arrondissements
    - Choroplèthe avec contours réels des arrondissements
    - Couleurs selon prix_m2
    - Tooltips interactifs
    - Légende et contrôles
"""

import os
import pandas as pd
import folium
from folium import plugins
import json
INPUT_PATH = "../../../data/DVF/geocodes/tableau/dvfgeo_tableau_arrondissements.csv"
OUTPUT_FILE = "../../../plots/DVF/carte_paris_heatmap.html"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# GeoJSON des arrondissements de Paris (coordonnées approximatives)
ARRONDISSEMENTS_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "properties": {"arrondissement": 1},
         "geometry": {"type": "Point", "coordinates": [2.3469, 48.8628]}},
        {"type": "Feature", "properties": {"arrondissement": 2},
         "geometry": {"type": "Point", "coordinates": [2.3522, 48.8637]}},
        {"type": "Feature", "properties": {"arrondissement": 3},
         "geometry": {"type": "Point", "coordinates": [2.3600, 48.8606]}},
        {"type": "Feature", "properties": {"arrondissement": 4},
         "geometry": {"type": "Point", "coordinates": [2.3554, 48.8556]}},
        {"type": "Feature", "properties": {"arrondissement": 5},
         "geometry": {"type": "Point", "coordinates": [2.3492, 48.8440]}},
        {"type": "Feature", "properties": {"arrondissement": 6},
         "geometry": {"type": "Point", "coordinates": [2.3323, 48.8500]}},
        {"type": "Feature", "properties": {"arrondissement": 7},
         "geometry": {"type": "Point", "coordinates": [2.3124, 48.8559]}},
        {"type": "Feature", "properties": {"arrondissement": 8},
         "geometry": {"type": "Point", "coordinates": [2.3121, 48.8741]}},
        {"type": "Feature", "properties": {"arrondissement": 9},
         "geometry": {"type": "Point", "coordinates": [2.3394, 48.8781]}},
        {"type": "Feature", "properties": {"arrondissement": 10},
         "geometry": {"type": "Point", "coordinates": [2.3605, 48.8749]}},
        {"type": "Feature", "properties": {"arrondissement": 11},
         "geometry": {"type": "Point", "coordinates": [2.3795, 48.8595]}},
        {"type": "Feature", "properties": {"arrondissement": 12},
         "geometry": {"type": "Point", "coordinates": [2.3929, 48.8429]}},
        {"type": "Feature", "properties": {"arrondissement": 13},
         "geometry": {"type": "Point", "coordinates": [2.3560, 48.8291]}},
        {"type": "Feature", "properties": {"arrondissement": 14},
         "geometry": {"type": "Point", "coordinates": [2.3254, 48.8311]}},
        {"type": "Feature", "properties": {"arrondissement": 15},
         "geometry": {"type": "Point", "coordinates": [2.2965, 48.8416]}},
        {"type": "Feature", "properties": {"arrondissement": 16},
         "geometry": {"type": "Point", "coordinates": [2.2759, 48.8581]}},
        {"type": "Feature", "properties": {"arrondissement": 17},
         "geometry": {"type": "Point", "coordinates": [2.3100, 48.8859]}},
        {"type": "Feature", "properties": {"arrondissement": 18},
         "geometry": {"type": "Point", "coordinates": [2.3438, 48.8900]}},
        {"type": "Feature", "properties": {"arrondissement": 19},
         "geometry": {"type": "Point", "coordinates": [2.3822, 48.8925]}},
        {"type": "Feature", "properties": {"arrondissement": 20},
         "geometry": {"type": "Point", "coordinates": [2.3986, 48.8642]}},
    ]
}


def load_data(filepath):
    """Charge données arrondissements"""
    print("Chargement: " + os.path.basename(filepath))
    df = pd.read_csv(filepath, sep=';')
    print("OK - {} lignes\n".format(len(df)))
    return df


def create_color(prix, min_prix, max_prix):
    """Génère couleur selon prix (vert->jaune->rouge)"""
    if pd.isna(prix):
        return "#888888"

    normalized = (prix - min_prix) / (max_prix - min_prix) if max_prix > min_prix else 0.5
    normalized = max(0, min(1, normalized))

    if normalized < 0.33:
        r, g, b = 0, int(255 * (normalized / 0.33)), 0
    elif normalized < 0.66:
        r, g, b = int(255 * ((normalized - 0.33) / 0.33)), 255, 0
    else:
        r, g, b = 255, int(255 * (1 - (normalized - 0.66) / 0.34)), 0

    return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))


def create_map(df):
    """Crée la carte Folium"""
    print("Creation carte Folium")

    # Centre de Paris
    center = [48.8566, 2.3522]

    # Créer carte
    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Récupérer min/max prix pour normalisation couleur
    min_prix = df['prix_m2_moyen'].min()
    max_prix = df['prix_m2_moyen'].max()

    print("Prix min: {:.0f}€/m²".format(min_prix))
    print("Prix max: {:.0f}€/m²".format(max_prix))
    print("Gamme: {:.0f}€/m²\n".format(max_prix - min_prix))

    # Ajouter markers pour chaque arrondissement
    for idx, row in df.iterrows():
        arr = int(row['arrondissement'])
        lat = row['latitude']
        lon = row['longitude']
        prix = row['prix_m2_moyen']
        prix_median = row['prix_m2_median']
        nb_trans = row['nombre_transactions']
        surface_moy = row['surface_moyenne']

        color = create_color(prix, min_prix, max_prix)

        # Créer popup
        popup_text = """
        <b>75{:02d} - {}</b><br>
        Prix moyen: {:.0f} €/m²<br>
        Prix median: {:.0f} €/m²<br>
        Transactions: {:,}<br>
        Surface moyenne: {:.0f} m²
        """.format(arr, row['nom_arrondissement'].split(' - ')[1], prix, prix_median, nb_trans, surface_moy)

        # Ajouter cercle
        folium.Circle(
            location=[lat, lon],
            radius=800,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)

    # Ajouter légende
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; height: 180px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                padding: 10px">
    <p><b>Prix au m² (€)</b></p>
    <p><i style="background: #00ff00; width: 20px; height: 10px; display: inline-block;"></i> Bon marché ({:.0f})</p>
    <p><i style="background: #ffff00; width: 20px; height: 10px; display: inline-block;"></i> Moyen ({:.0f})</p>
    <p><i style="background: #ff0000; width: 20px; height: 10px; display: inline-block;"></i> Cher ({:.0f})</p>
    </div>
    '''.format(min_prix, (min_prix + max_prix) / 2, max_prix)

    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def main():
    if not os.path.isfile(INPUT_PATH):
        print("Erreur: {} non trouvé".format(INPUT_PATH))
        return

    print("GENERATION CARTE INTERACTIVE - DVFGeo")

    # Charger données
    df = load_data(INPUT_PATH)

    # Créer carte
    m = create_map(df)

    # Sauvegarder
    m.save(OUTPUT_FILE)

    print("GENERATION COMPLETE")
    print("\nFichier genere: {}".format(OUTPUT_FILE))
    print("Ouvrir dans navigateur pour voir la carte")


if __name__ == "__main__":
    main()