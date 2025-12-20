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
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Carte du RFR Moyen par Arrondissement")
        render_html("fiscal/heatmap_rfr_arrondissements.html", height=600)
    with col2:
        st.subheader("Détail par Arrondissement")
        render_html("fiscal/rfr_moyen_arrondissements.html", height=600)

with tab_evol:
    st.subheader("Dynamique des revenus fiscaux dans le temps")
    render_html("fiscal/evolution_rfr_temporelle.html", height=600)

with tab_ineq:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribution des tranches de revenus")
        render_html("fiscal/distribution_tranches_stacked.html", height=500)
    with col2:
        st.subheader("Ratio d'inégalités (Q90/Q10)")
        render_html("fiscal/ratio_inegalites_arrondissements.html", height=500)