import streamlit as st
from src.dashboard.utils.viz_helper import render_image, render_html

st.set_page_config(page_title="Analyse Annonces", layout="wide")
st.title("Analyse des Annonces (Offre du Marché)")

tab_map, tab_source, tab_prix = st.tabs([
    "Localisation des Annonces",
    "Sources & Volumes",
    "Analyse des Prix"
])

with tab_map:
    st.subheader("Carte des annonces en ligne")
    render_html("scrapped/carte_annonces_paris.html", height=700)

with tab_source:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Parts de marché par Source")
        render_image("scrapped/volume_source.png")
    with col2:
        st.subheader("Positionnement Prix par Source")
        render_image("scrapped/distribution_prix_source.png")

with tab_prix:
    st.subheader("Corrélation Prix / Surface")
    render_image("scrapped/prix_surface.png", width=800)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribution par nombre de pièces")
        render_image("scrapped/distribution_pieces.png")
    with col2:
        st.subheader("Matrice Type x Arrondissement")
        render_image("scrapped/heatmap_type_arrondissement.png")

    st.subheader("Classement des arrondissements (Offre)")
    render_image("scrapped/classement_arrondissements.png")