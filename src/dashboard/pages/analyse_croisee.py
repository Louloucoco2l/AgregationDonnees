import streamlit as st
from src.dashboard.utils.viz_helper import render_html

st.set_page_config(page_title="Analyses Croisées", layout="wide")
st.title("Croisement : Immobilier vs Revenus vs Temps")

st.markdown("""
Cette section croise les données DVF (Prix actés) avec les données Fiscales (RFR) 
pour analyser l'accessibilité et les corrélations économiques.
""")

tab_corr, tab_access, tab_evol = st.tabs([
    "Corrélations Prix/Revenus",
    "Accessibilité Immobilière",
    "Évolution Interactive"
])

with tab_corr:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Corrélation RFR vs Prix m²")
        render_html("viz_croisee/correlation_rfr_prix_m2.html", height=500)
    with col2:
        st.subheader("Nuage de points détaillé")
        render_html("viz_croisee/scatter_rfr_prix_m2.html", height=500)

with tab_access:
    st.subheader("Tableau de bord de l'accessibilité")
    render_html("viz_croisee/dashboard_accessibilite.html", height=800)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ratio Prix / Revenu")
        render_html("viz_croisee/ratio_prix_revenu.html", height=500)
    with col2:
        st.subheader("Années de revenus pour un T2")
        # J'ai mis les deux fichiers potentiels cités, décommentez celui que vous préférez
        render_html("viz_croisee/annees_rfr_pour_t2.html", height=500)
        # render_html("viz_croisee/annees_revenus_t2.html", height=500)

with tab_evol:
    st.subheader("Évolution conjointe Prix vs RFR (Play Axis)")
    render_html("viz_croisee/evolution_interactive_prix_rfr.html", height=700)

    st.subheader("Heatmap d'évolution des prix")
    render_html("viz_croisee/heatmap_evolution_prix.html", height=600)