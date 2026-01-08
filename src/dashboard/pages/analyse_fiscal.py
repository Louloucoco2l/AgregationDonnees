import streamlit as st
from src.dashboard.utils.viz_helper import render_image, render_html

st.set_page_config(page_title="Analyse Fiscale", layout="wide")
st.title("Analyse des Revenus Fiscaux (RFR)")

tab_map, tab_evol, tab_ineq = st.tabs([
    "Cartographie des Revenus",
    "Évolution Temporelle",
    "Inégalités & Répartition"
])

with tab_map:
    st.subheader("Carte du RFR Moyen par Arrondissement")
    render_html("fiscal/heatmap_rfr_arrondissements.html", height=900)

    st.subheader("Détail par Arrondissement")
    render_html("fiscal/rfr_moyen_arrondissements.html", height=900)

with tab_evol:
    st.subheader("Dynamique des revenus fiscaux dans le temps")
    render_html("fiscal/evolution_rfr_temporelle.html", height=600)

with tab_ineq:
    st.subheader("Distribution des tranches de revenus")
    render_html("fiscal/distribution_tranches_stacked.html", height=800)

    st.subheader("Ratio d'inégalités (Q90/Q10)")
    render_html("fiscal/ratio_inegalites_arrondissements.html", height=800)