import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st
from src.dashboard.utils.data_loader import load_dvf, load_ircom
from src.dashboard.utils.viz_builder import load_static_plot

st.set_page_config(page_title="Analyses Croisées", layout="wide")
st.set_page_config(page_title="Analyses Croisées", layout="wide")
st.title("Analyses Croisées entre DVF et IRCOM")

# Sidebar filters
with st.sidebar:
    st.header("Filtres")
    arrondissements = st.multiselect(
        "Arrondissements",
        options=list(range(1, 21)),
        default=list(range(1, 21))
    )
    annee_min, annee_max = st.slider(
        "Période",
        2020, 2023,
        (2020, 2023)
    )

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "Accessibilité T2",
    "Corrélation Prix/Revenus",
    "Évolution Comparative",
    "Dashboard Synthétique"
])


