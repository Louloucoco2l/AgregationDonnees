"""
    Carte interactive Folium des annonces scrappées
    - Choroplèthe par arrondissement
    - Prix moyen au m²
"""

from src.config import paths
import pandas as pd
import folium
import json

INPUT_PATH = paths.data.scrapped/"annonces_paris_clean_final.csv"
GEOJSON_PATH = paths.data/"arrondissements.geojson"
OUTPUT_FILE = paths.plot.scrapped/"carte_annonces_paris.html"


def load_data():
    """Charge et agrège les données scrappées"""
    print("Chargement des donnees...")
    df = pd.read_csv(INPUT_PATH, sep=';')

    # Extraire numéro arrondissement
    df['arrondissement'] = df['localisation'].astype(str).str.extract(r'750?(\d{1,2})').astype(float)

    # Agrégation par arrondissement
    df_arr = df.groupby('arrondissement').agg({
        'prix_m2': ['mean', 'median', 'count'],
        'prix': 'mean',
        'surface': 'mean'
    }).reset_index()
    df_arr.columns = ['arrondissement', 'prix_m2_moyen', 'prix_m2_median',
                      'nb_annonces', 'prix_moyen', 'surface_moyenne']

    # Coordonnées barycentres arrondissements Paris
    barycentres = {
        1: (48.8606, 2.3376), 2: (48.8679, 2.3415), 3: (48.8637, 2.3615),
        4: (48.8544, 2.3574), 5: (48.8462, 2.3498), 6: (48.8499, 2.3331),
        7: (48.8566, 2.3150), 8: (48.8744, 2.3106), 9: (48.8769, 2.3379),
        10: (48.8758, 2.3619), 11: (48.8592, 2.3789), 12: (48.8396, 2.3876),
        13: (48.8322, 2.3561), 14: (48.8331, 2.3264), 15: (48.8421, 2.2992),
        16: (48.8637, 2.2769), 17: (48.8875, 2.3089), 18: (48.8925, 2.3444),
        19: (48.8817, 2.3822), 20: (48.8638, 2.3986)
    }

    df_arr['latitude'] = df_arr['arrondissement'].map(lambda x: barycentres.get(int(x), (None, None))[0])
    df_arr['longitude'] = df_arr['arrondissement'].map(lambda x: barycentres.get(int(x), (None, None))[1])

    print(f"OK - {len(df_arr)} arrondissements\n")
    return df_arr


def load_geojson(filepath):
    """Charge GeoJSON des arrondissements"""
    print("Chargement GeoJSON...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("OK\n")
    return data


def create_map(df, geojson):
    """Crée la carte Folium"""
    print("Creation carte Folium")

    center = [48.8566, 2.3522]
    m = folium.Map(location=center, zoom_start=12, tiles='OpenStreetMap')

    min_prix = df['prix_m2_moyen'].min()
    max_prix = df['prix_m2_moyen'].max()
    print(f"Prix min : {min_prix:.0f} €/m²")
    print(f"Prix max : {max_prix:.0f} €/m²\n")

    # Choroplèthe
    folium.Choropleth(
        geo_data=geojson,
        name="Choroplèthe prix/m²",
        data=df,
        columns=["arrondissement", "prix_m2_moyen"],
        key_on="feature.properties.c_ar",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.6,
        line_color="black",
        nan_fill_color="grey",
        legend_name="Prix moyen au m² (annonces)",
    ).add_to(m)

    # Tooltips
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

    # Markers avec popups
    for idx, row in df.iterrows():
        arr = int(row["arrondissement"])
        popup_html = f"""
        <b>75{arr:02d}</b><br>
        Prix moyen : {row['prix_m2_moyen']:.0f} €/m²<br>
        Prix médian : {row['prix_m2_median']:.0f} €/m²<br>
        Annonces : {int(row['nb_annonces'])}<br>
        Surface moyenne : {row['surface_moyenne']:.0f} m²
        """

        if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
            folium.Marker(
                [row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def main():
    print("CARTE INTERACTIVE - ANNONCES SCRAPPÉES")

    df = load_data()
    geojson = load_geojson(GEOJSON_PATH)
    m = create_map(df, geojson)

    m.save(OUTPUT_FILE)

    print(f"\nFichier genere : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()