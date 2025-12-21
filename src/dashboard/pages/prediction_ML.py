import sys
from pathlib import Path

# --- HACK PYTHONPATH ---
root_path = str(Path(__file__).resolve().parents[3])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
import streamlit.components.v1 as components
import folium
import plotly.graph_objects as go
from src.dashboard.utils.ml_predictor import get_predictor

st.set_page_config(page_title="Estimation", layout="wide")

st.title("Estimation Intelligente")
st.markdown("Entrez l'adresse précise pour une estimation basée sur la géolocalisation exacte.")

predictor = get_predictor()

# --- FORMULAIRE ---
with st.form("estimation_form"):
    col_addr, col_dummy = st.columns([2, 1])
    with col_addr:
        adresse = st.text_input("Adresse du bien (Paris)", value="10 rue de Rivoli, 75001 Paris")

    col1, col2, col3 = st.columns(3)
    with col1:
        surface = st.number_input("Surface (m²)", min_value=9.0, max_value=300.0, value=50.0)
    with col2:
        pieces = st.number_input("Nombre de pièces", min_value=1, max_value=10, value=2)
    with col3:
        annee = st.selectbox("Année de vente estimée", [2024, 2025, 2026], index=1)

    submitted = st.form_submit_button("Lancer l'estimation", type="primary")

# --- RÉSULTATS ---
if submitted and adresse:
    with st.spinner("Géocodage et calcul en cours..."):
        result = predictor.estimate_complet(surface, pieces, annee, adresse)

    if 'error' in result:
        st.error(f"Erreur : {result['error']}")
    else:
        st.success(f"📍 Localisé : {result['geo_info']['label']}")

        # 1. KPIs Principaux
        c1, c2, c3 = st.columns(3)
        c1.metric("Prix m² Estimé", f"{result['prix_m2_estime']:,.0f} €")
        c2.metric("Prix Total", f"{result['prix_total_estime']:,.0f} €")
        c3.metric("Confiance Modèle", f"{result['confiance']:.1f}% ({result['classification']})")

        st.divider()

        # 2. Visuels (Carte & Jauge)
        col_map, col_gauge = st.columns(2)

        with col_map:
            st.markdown("##### Localisation")
            lat, lon = result['geo_info']['latitude'], result['geo_info']['longitude']
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(
                [lat, lon],
                popup=result['geo_info']['label'],
                icon=folium.Icon(color="red", icon="home")
            ).add_to(m)

            # Affichage stable via HTML
            map_html = m._repr_html_()
            components.html(map_html, height=300)

        with col_gauge:
            st.markdown("##### Probabilité 'Cher'")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result['probabilite_cher'] * 100,
                title={'text': "Probabilité"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#e74c3c" if result['probabilite_cher'] > 0.5 else "#2ecc71"},
                    'steps': [{'range': [0, 50], 'color': "lightgray"}]
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

            st.info(f"Fourchette : **{result['prix_total_min']:,.0f} €** - **{result['prix_total_max']:,.0f} €**")

        st.divider()

        # 3. Détails Techniques & Comparaison (Restaurés)
        st.subheader("Détails de l'estimation")

        col_probs, col_json = st.columns(2)

        with col_probs:
            st.markdown("**Comparaison des probabilités**")
            # Graphique à barres comparatif
            fig2 = go.Figure(data=[
                go.Bar(
                    x=['Bon marché', 'Cher'],
                    y=[result['probabilite_bon_marche'], result['probabilite_cher']],
                    marker_color=['#2ecc71', '#e74c3c'],
                    text=[f"{result['probabilite_bon_marche']*100:.1f}%", f"{result['probabilite_cher']*100:.1f}%"],
                    textposition='auto',
                )
            ])
            fig2.update_layout(
                yaxis_title="Probabilité",
                yaxis_range=[0, 1],
                height=300,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_json:
            st.markdown("**Données brutes du modèle**")
            # Affichage JSON dans un expander ouvert par défaut ou non
            with st.expander("Voir le JSON complet", expanded=True):
                st.json(result)