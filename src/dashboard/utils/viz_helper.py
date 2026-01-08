import streamlit as st
from pathlib import Path
from PIL import Image

# Définition de la racine du projet (3 niveaux au-dessus de ce fichier)
# src/dashboard/utils/viz_helper.py -> src/dashboard/utils -> src/dashboard -> src -> ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLOTS_DIR = PROJECT_ROOT / "plots"


def render_image(relative_path, caption=None, width=None):
    """Affiche une image PNG/JPG depuis le dossier plots"""
    file_path = PLOTS_DIR / relative_path

    if not file_path.exists():
        st.warning(f"Image introuvable : {relative_path}")
        return

    image = Image.open(file_path)
    st.image(image, caption=caption, width=width, use_container_width=(width is None))


def render_html(relative_path, height=600):
    """Affiche un fichier HTML interactif (Folium/Plotly)"""
    file_path = PLOTS_DIR / relative_path

    if not file_path.exists():
        st.warning(f"Fichier HTML introuvable : {relative_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=height, scrolling=True)