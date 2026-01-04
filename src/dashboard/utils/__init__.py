"""
Utilitaires pour le dashboard Streamlit

Expose les fonctions principales pour simplifier les imports, pas de chemin long dans chaque fichier :
    from src.dashboard.utils import load_dvf, MLPredictor, load_static_plot
"""

# Data loaders
from .data_loader import (
    load_dvf_data,
    load_rfr_data,
    load_annonces_data
)

# ML predictor
from .ml_predictor import (
    MLPredictor,
    get_predictor
)

# Viz helper
from .viz_helper import (
    render_image,
    render_html
)

__all__ = [
    # Data
    'load_dvf_data',
    'load_rfr_data',
    'load_annonces_data',

    # ML
    'MLPredictor',
    'get_predictor',

    # Viz
    'render_image',
    'render_html'
]