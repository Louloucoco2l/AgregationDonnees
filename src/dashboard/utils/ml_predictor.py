import pickle
import pandas as pd
import numpy as np
import streamlit as st
from src.config import paths

MODELS_DIR = paths.models.path

# Coordonnées approximatives des centres d'arrondissements (Fallback)
ARRONDISSEMENT_COORDS = {
    1: (48.8626, 2.3363), 2: (48.8691, 2.3411), 3: (48.8637, 2.3615), 4: (48.8543, 2.3576),
    5: (48.8444, 2.3507), 6: (48.8491, 2.3326), 7: (48.8561, 2.3121), 8: (48.8727, 2.3075),
    9: (48.8776, 2.3375), 10: (48.8761, 2.3622), 11: (48.8590, 2.3789), 12: (48.8349, 2.4213),
    13: (48.8283, 2.3623), 14: (48.8296, 2.3271), 15: (48.8412, 2.2975), 16: (48.8603, 2.2620),
    17: (48.8873, 2.3067), 18: (48.8925, 2.3444), 19: (48.8817, 2.3822), 20: (48.8632, 2.4008)
}


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


class MLPredictor:
    def __init__(self):
        self.model_linear = None
        self.model_logistic = None
        self.scaler = None
        self.feature_names = None
        self._load_models()

    def _load_models(self):
        try:
            with open(MODELS_DIR / "model_linear_regression.pkl", 'rb') as f: self.model_linear = pickle.load(f)
            with open(MODELS_DIR / "model_logistic_regression.pkl", 'rb') as f: self.model_logistic = pickle.load(f)
            with open(MODELS_DIR / "scaler.pkl", 'rb') as f: self.scaler = pickle.load(f)
            with open(MODELS_DIR / "feature_names.pkl", 'rb') as f: self.feature_names = pickle.load(f)
        except Exception as e:
            print(f"Erreur chargement: {e}")

    def prepare_features(self, surface_m2, code_arrondissement, type_local, nb_pieces, annee, mois=6):

        # 1. Récupération Lat/Lon par défaut (centre arrondissement)
        lat, lon = ARRONDISSEMENT_COORDS.get(code_arrondissement, (48.8566, 2.3522))

        # Calcul distance centre
        dist_center = haversine_distance(lat, lon, 48.853, 2.3499)

        # 2. Construction dictionnaire de base
        data = {
            'log_surface_m2': np.log1p(surface_m2),
            'annee_norm': (annee - 2020) / 5,
            'mois_sin': np.sin(2 * np.pi * mois / 12),
            'mois_cos': np.cos(2 * np.pi * mois / 12),
            'nb_pieces_fill': float(nb_pieces),
            'latitude': lat,
            'longitude': lon
        }

        # 3. Gestion One-Hot Encoding (Arrondissements)
        # On met 1 dans la colonne 'arrond_X' correspondante, 0 ailleurs
        for i in range(1, 21):
            col_name = f"arrond_{i}"
            if col_name in self.feature_names:
                data[col_name] = 1 if code_arrondissement == i else 0

        # 4. Gestion One-Hot Encoding (Type Local)
        for t in ['Appartement', 'Maison', 'Local industriel. commercial ou assimilé', 'Dépendance']:
            col_name = f"type_{t}"
            if col_name in self.feature_names:
                data[col_name] = 1 if type_local == t else 0

        # 5. Gestion One-Hot Encoding (Nature - Défaut Vente)
        for col in self.feature_names:
            if col.startswith('nature_'):
                data[col] = 1 if col == 'nature_Vente' else 0

        # 6. Création DataFrame et alignement
        df = pd.DataFrame([data])

        # Remplir les colonnes manquantes (si le modèle a vu des catégories qu'on n'a pas listées)
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0

        return df[self.feature_names]



    def estimate_complet(self, surface_m2, code_arrondissement, type_local, nb_pieces, annee, mois=6):
        X = self.prepare_features(surface_m2, code_arrondissement, type_local, nb_pieces, annee, mois)
        X_scaled = self.scaler.transform(X)

        # Prédiction
        prix_m2 = self.model_linear.predict(X_scaled)[0]

        # Classification
        probas = self.model_logistic.predict_proba(X_scaled)[0]
        classe = self.model_logistic.predict(X_scaled)[0]

        return {
            'prix_m2_estime': prix_m2,
            'prix_total_estime': prix_m2 * surface_m2,
            'prix_m2_min': prix_m2 * 0.85, # Marge réaliste +/- 15%
            'prix_m2_max': prix_m2 * 1.15,
            'prix_total_min': (prix_m2 * surface_m2) * 0.85,
            'prix_total_max': (prix_m2 * surface_m2) * 1.15,
            'classification': "Cher" if classe == 1 else "Bon marché",
            'probabilite_cher': probas[1],
            'probabilite_bon_marche': probas[0],
            'confiance': max(probas) * 100
        }

@st.cache_resource
def get_predictor():
    return MLPredictor()