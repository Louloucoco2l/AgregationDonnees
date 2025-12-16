import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st
from src.dashboard.utils.ml_predictor import get_predictor
import plotly.graph_objects as go

st.set_page_config(page_title="Prédiction ML", layout="wide")

st.title("Estimation de Prix Immobilier")
st.markdown("Utilisez nos modèles ML pour estimer le prix d'un bien")

# Charger le predictor (avec cache)
predictor = get_predictor()

# Formulaire de saisie
with st.form("prediction_form"):
    col1, col2 = st.columns(2)

    with col1:
        surface = st.number_input(
            "Surface (m²)",
            min_value=10.0,
            max_value=300.0,
            value=65.0,
            step=5.0
        )

        arrondissement = st.selectbox(
            "Arrondissement",
            options=list(range(1, 21)),
            index=10  # 11e par défaut
        )

        type_local = st.selectbox(
            "Type de bien",
            options=[
                "Appartement",
                "Maison",
                "Local industriel. commercial ou assimilé",
                "Dépendance"
            ]
        )

    with col2:
        nombre_pieces = st.number_input(
            "Nombre de pièces",
            min_value=1,
            max_value=10,
            value=3
        )

        annee = st.selectbox(
            "Année",
            options=list(range(2020, 2026)),
            index=5  # 2025 par défaut
        )

        mois = st.slider(
            "Mois",
            min_value=1,
            max_value=12,
            value=6
        )

    submitted = st.form_submit_button("Estimer le prix", type="primary")

# Traitement de la prédiction
if submitted:
    with st.spinner("Calcul en cours..."):
        # Appeler le wrapper
        result = predictor.estimate_complet(
            surface_m2=surface,
            code_arrondissement=arrondissement,
            type_local=type_local,
            nb_pieces=nombre_pieces,
            annee=annee,
            mois=mois
        )

    # Affichage des résultats
    st.success("✓ Estimation terminée")

    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Prix/m² estimé",
            f"{result['prix_m2_estime']:,.0f} €",
            delta=None
        )

    with col2:
        st.metric(
            "Prix total estimé",
            f"{result['prix_total_estime']:,.0f} €",
            delta=None
        )

    with col3:
        st.metric(
            "Classification",
            result['classification'],
            delta=None
        )

    with col4:
        st.metric(
            "Confiance",
            f"{result['confiance']:.1f}%",
            delta=None
        )

    # Intervalle de confiance
    st.markdown("---")
    st.subheader("Intervalle de confiance (95%)")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"""
        **Prix/m²**
        - Minimum : {result['prix_m2_min']:,.0f} €
        - Estimé : {result['prix_m2_estime']:,.0f} €
        - Maximum : {result['prix_m2_max']:,.0f} €
        """)

    with col2:
        st.info(f"""
        **Prix total**
        - Minimum : {result['prix_total_min']:,.0f} €
        - Estimé : {result['prix_total_estime']:,.0f} €
        - Maximum : {result['prix_total_max']:,.0f} €
        """)

    # Graphique intervalle de confiance
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Prix/m²'],
        y=[result['prix_m2_estime']],
        error_y=dict(
            type='data',
            symmetric=False,
            array=[result['prix_m2_max'] - result['prix_m2_estime']],
            arrayminus=[result['prix_m2_estime'] - result['prix_m2_min']]
        ),
        marker_color='#3498db',
        name='Estimation'
    ))

    fig.update_layout(
        title="Intervalle de confiance du prix/m²",
        yaxis_title="Prix/m² (€)",
        template="plotly_white",
        height=400
    )

    st.plotly_chart(fig, width='stretch')

    # Probabilités de classification
    st.markdown("---")
    st.subheader("Probabilités de classification")

    fig2 = go.Figure(data=[
        go.Bar(
            x=['Bon marché', 'Cher'],
            y=[result['probabilite_bon_marche'], result['probabilite_cher']],
            marker_color=['#2ecc71', '#e74c3c'],
            text=[
                f"{result['probabilite_bon_marche'] * 100:.1f}%",
                f"{result['probabilite_cher'] * 100:.1f}%"
            ],
            textposition='outside'
        )
    ])

    fig2.update_layout(
        title="Probabilités de classification",
        yaxis_title="Probabilité",
        yaxis_tickformat='.0%',
        template="plotly_white",
        height=400
    )

    st.plotly_chart(fig2, width='stretch')

    # Détails techniques
    with st.expander("Détails techniques"):
        st.json(result)