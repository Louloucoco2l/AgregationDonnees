"""
Constructeur de visualisations pour le dashboard

Fonctions :
    - load_static_plot() : Charge un plot HTML pré-généré
    - generate_prix_m2_by_arrondissement() : Bar chart dynamique
    - generate_evolution_temporelle() : Série temporelle
    - load_precomputed_data() : Charge données pré-agrégées
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.config import paths

PLOTS_DIR = paths.plots.path
DATA_DIR = paths.data.path


# ============================================================================
# STRATÉGIE 1 : CHARGER PLOTS STATIQUES PRÉ-GÉNÉRÉS
# ============================================================================

def load_static_plot(plot_name: str, plot_type: str = "viz_croisee"):
    """
    Charge un plot HTML pré-généré depuis plots/

    Args:
        plot_name: Nom du fichier (ex: "heatmap_evolution_prix.html")
        plot_type: Sous-dossier (DVF, fiscal, viz_croisee, scrapped)

    Returns:
        HTML string pour st.components.v1.html() ou None si introuvable

    Exemple:
        >>> html = load_static_plot("annees_rfr_pour_t2.html", "viz_croisee")
        >>> st.components.v1.html(html, height=600)
    """
    plot_path = PLOTS_DIR / plot_type / plot_name

    if not plot_path.exists():
        st.error(f"❌ Plot introuvable : {plot_path}")
        return None

    with open(plot_path, 'r', encoding='utf-8') as f:
        return f.read()


# ============================================================================
# STRATÉGIE 2 : GÉNÉRER PLOTS DYNAMIQUES À LA DEMANDE
# ============================================================================

@st.cache_data(ttl=600)  # Cache 10 min
def generate_prix_m2_by_arrondissement(
        df: pd.DataFrame,
        arrondissements: list,
        annee_min: int,
        annee_max: int
):
    """
    Génère un bar chart filtré dynamiquement

    Args:
        df: DataFrame DVF
        arrondissements: Liste arrondissements sélectionnés
        annee_min, annee_max: Période

    Returns:
        Plotly Figure

    Exemple:
        >>> from src.dashboard.utils import load_dvf, generate_prix_m2_by_arrondissement
        >>> df = load_dvf()
        >>> fig = generate_prix_m2_by_arrondissement(df, [10, 11, 18], 2020, 2023)
        >>> st.plotly_chart(fig)
    """
    # Filtrer données
    df_filtered = df[
        (df['arrondissement'].isin(arrondissements)) &
        (df['annee'].between(annee_min, annee_max))
        ]

    # Agréger
    df_agg = df_filtered.groupby('arrondissement').agg({
        'prix_m2': 'median'
    }).reset_index().sort_values('prix_m2', ascending=False)

    # Créer plot
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_agg['arrondissement'].astype(str) + 'e',
        y=df_agg['prix_m2'],
        marker_color='#3498db',
        text=df_agg['prix_m2'].round(0),
        textposition='outside'
    ))

    fig.update_layout(
        title=f"Prix médian au m² ({annee_min}-{annee_max})",
        xaxis_title="Arrondissement",
        yaxis_title="Prix/m² (€)",
        template="plotly_white",
        height=500
    )

    return fig


@st.cache_data(ttl=600)
def generate_evolution_temporelle(
        df: pd.DataFrame,
        arrondissements: list
):
    """
    Génère une série temporelle multi-lignes

    Args:
        df: DataFrame DVF
        arrondissements: Liste arrondissements à afficher

    Returns:
        Plotly Figure

    Exemple:
        >>> fig = generate_evolution_temporelle(df, [10, 11, 18, 19, 20])
        >>> st.plotly_chart(fig)
    """
    df_filtered = df[df['arrondissement'].isin(arrondissements)]

    df_agg = df_filtered.groupby(['annee', 'arrondissement']).agg({
        'prix_m2': 'median'
    }).reset_index()

    fig = go.Figure()

    for arr in arrondissements:
        df_arr = df_agg[df_agg['arrondissement'] == arr]
        fig.add_trace(go.Scatter(
            x=df_arr['annee'],
            y=df_arr['prix_m2'],
            mode='lines+markers',
            name=f"{arr}e"
        ))

    fig.update_layout(
        title="Évolution du prix médian/m²",
        xaxis_title="Année",
        yaxis_title="Prix/m² (€)",
        template="plotly_white",
        height=500
    )

    return fig


# ============================================================================
# STRATÉGIE 3 : PLOTS HYBRIDES (DONNÉES STATIQUES + FILTRES DYNAMIQUES)
# ============================================================================

@st.cache_data(ttl=3600)
def load_precomputed_data(dataset_name: str):
    """
    Charge des données pré-agrégées pour plots rapides

    Args:
        dataset_name: Nom du fichier sans extension
            - "dvfgeo_tableau_arrondissements"
            - "dvfgeo_tableau_temporel"
            - "dvfgeo_tableau_type_local"

    Returns:
        DataFrame pré-agrégé

    Exemple:
        >>> df_arr = load_precomputed_data("dvfgeo_tableau_arrondissements")
        >>> print(df_arr.columns)
    """
    data_path = DATA_DIR / "DVF" / "geocodes" / "tableau" / f"{dataset_name}.csv"
    return pd.read_csv(data_path, sep=';')