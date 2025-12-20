import streamlit as st
from src.dashboard.utils.viz_helper import render_image, render_html

st.set_page_config(page_title="Analyse DVF", layout="wide")
st.title("Analyse des Valeurs Foncières (Données Actées)")

tab_map, tab_vol, tab_prix, tab_distrib = st.tabs([
    "Carte Interactive",
    "volumes & Temporalité",
    "prix & Classements",
    "boxplot Distributions"
])

with tab_map:
    st.subheader("Carte de chaleur des prix immobiliers")
    render_html("DVF/carte_paris_heatmap.html", height=700)

with tab_vol:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Évolution temporelle des prix")
        render_image("DVF/serie_temporelle.png")
    with col2:
        st.subheader("Volume de transactions par arrondissement")
        render_image("DVF/volume_transactions.png")

with tab_prix:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Classement des arrondissements (Prix/m²)")
        render_image("DVF/classement_arrondissements.png")
    with col2:
        st.subheader("Matrice Type de bien x Arrondissement")
        render_image("DVF/heatmap_type_arrondissement.png")

with tab_distrib:
    st.subheader("Distribution globale des prix")
    render_image("DVF/distribution_prix.png")