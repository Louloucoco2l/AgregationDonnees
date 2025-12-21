import sys
from src.config import paths
import streamlit as st
import streamlit.components.v1 as components
import folium
import plotly.graph_objects as go
from src.dashboard.utils.ml_predictor import get_predictor
import requests
API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(page_title="Estimation API", layout="wide")

st.title("Estimation via API")
st.markdown(f"Ce dashboard interroge l'API locale (**{API_URL}**) qui loggue les requêtes en base de données.")

#FORMULAIRE
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

    submitted = st.form_submit_button("Lancer l'estimation (API)", type="primary")

#APPEL API
if submitted and adresse:
    with st.spinner("Communication avec le serveur d'IA..."):
        try:
            # Préparation du JSON à envoyer
            payload = {
                "surface": surface,
                "pieces": pieces,
                "annee": annee,
                "adresse": adresse
            }

            #envoi de la requête POST
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                result = response.json()  # Récupération de la réponse

                #AFFICHAGE
                if 'error' in result:  # Si l'API renvoie une erreur métier
                    st.error(result['error'])
                else:
                    st.success(f"Localisé : {result['geo_info']['label']}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Prix m²", f"{result['prix_m2_estime']:,.0f} €")
                    c2.metric("Total", f"{result['prix_total_estime']:,.0f} €")
                    c3.metric("Confiance", f"{result['confiance']:.1f}%")

                    st.divider()

                    # Carte
                    col_map, col_gauge = st.columns(2)
                    with col_map:
                        lat, lon = result['geo_info']['latitude'], result['geo_info']['longitude']
                        m = folium.Map(location=[lat, lon], zoom_start=15)
                        folium.Marker([lat, lon], popup=result['geo_info']['label'],
                                      icon=folium.Icon(color="red", icon="home")).add_to(m)
                        components.html(m._repr_html_(), height=300)

                    # Jauge
                    with col_gauge:
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number", value=result['probabilite_cher'] * 100,
                            title={'text': "Probabilité 'Cher'"},
                            gauge={'axis': {'range': [0, 100]},
                                   'bar': {'color': "#e74c3c" if result['probabilite_cher'] > 0.5 else "#2ecc71"}}
                        ))
                        fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                        st.plotly_chart(fig, use_container_width=True)

                    # Détails JSON
                    with st.expander("Voir la réponse JSON brute de l'API"):
                        st.json(result)

            else:
                st.error(f"Erreur API ({response.status_code}) : {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("Impossible de contacter l'API. Vérifiez que `src/api/main.py` est bien lancé.")