import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH pour que les imports fonctionnent
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.dashboard.utils.data_loader import load_all_data

st.set_page_config(
    page_title="Immobilier Paris - Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement données (avec cache)
data = load_all_data()

st.title("Analyse du Marché Immobilier Parisien")
st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Prix médian/m²", "10 458€", "+2.3%")
# ...