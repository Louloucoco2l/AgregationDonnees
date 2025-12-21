import pickle
import pandas as pd
import numpy as np
import requests
import streamlit as st
from src.config import paths

MODELS_DIR = paths.models.path

class MLPredictor:
    def __init__(self):
        self.model_linear = None
        self.model_logistic = None
        self.scaler = None
        self.feature_names = None
        self._load_models()

    def _load_models(self):
        try:
            with open(MODELS_DIR / "model_linear_regression.pkl", 'rb') as f:
                self.model_linear = pickle.load(f)
            with open(MODELS_DIR / "model_logistic_regression.pkl", 'rb') as f:
                self.model_logistic = pickle.load(f)
            with open(MODELS_DIR / "scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            with open(MODELS_DIR / "feature_names.pkl", 'rb') as f:
                self.feature_names = pickle.load(f)
        except Exception as e:
            print(f"Erreur chargement: {e}")

    def geocode_address(self, address: str):
        #utilisation de l'API publique Adresse
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {'q': address, 'citycode': '75056', 'limit': 1}

        try:
            r = requests.get(url, params=params)
            data = r.json()
            if data['features']:
                props = data['features'][0]['properties']
                coords = data['features'][0]['geometry']['coordinates']
                postcode = props.get('postcode')

                #detection arrondissement
                if postcode and str(postcode).startswith('75'):
                    arrondissement = int(str(postcode)[-2:])
                else:
                    arrondissement = 1 # Fallback

                return {
                    'latitude': coords[1],
                    'longitude': coords[0],
                    'arrondissement': arrondissement,
                    'label': props.get('label')
                }
        except Exception as e:
            print(f"Erreur Geocoding: {e}")
        return None

    def prepare_features(self, surface_m2, nb_pieces, annee, latitude, longitude, code_arrondissement):
        #distance point 0 (notre dame)
        R = 6371
        lat_nd, lon_nd = 48.853, 2.3499
        phi1, phi2 = np.radians(latitude), np.radians(lat_nd)
        dphi = np.radians(lat_nd - latitude)
        dlambda = np.radians(lon_nd - longitude)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
        dist_center = 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        #dictionnaire
        data = {
            'log_surface_m2': np.log1p(surface_m2),
            'dist_center': dist_center,
            'annee_norm': (annee - 2020) / 5.0,
            'nb_pieces_fill': float(nb_pieces),
            'latitude': latitude,
            'longitude': longitude
        }

        #one hot encoding
        for i in range(1, 21):
            col_name = f"arrond_{i}"
            if col_name in self.feature_names:
                data[col_name] = 1 if code_arrondissement == i else 0

        #DataFrame aligné
        df = pd.DataFrame([data])
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0

        return df[self.feature_names]

    def estimate_complet(self, surface_m2, nb_pieces, annee, address_str):
        # geocodage
        geo = self.geocode_address(address_str)
        if not geo:
            return {'error': "Adresse introuvable à Paris"}

        #préparation
        X = self.prepare_features(
            surface_m2, nb_pieces, annee,
            geo['latitude'], geo['longitude'], geo['arrondissement']
        )

        #le scaler renvoie un numpy array (sans nom), on le remet en DataFrame pour que Sklearn arrête de crier
        X_scaled_array = self.scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled_array, columns=self.feature_names)

        #prédiction
        prix_m2 = self.model_linear.predict(X_scaled)[0]

        #classification
        probas = self.model_logistic.predict_proba(X_scaled)[0]
        classe = self.model_logistic.predict(X_scaled)[0]

        return {
            'prix_m2_estime': prix_m2,
            'prix_total_estime': prix_m2 * surface_m2,
            'prix_m2_min': prix_m2 * 0.80,
            'prix_m2_max': prix_m2 * 1.20,
            'prix_total_min': (prix_m2 * surface_m2) * 0.80,
            'prix_total_max': (prix_m2 * surface_m2) * 1.20,
            'classification': "Cher" if classe == 1 else "Bon marché",
            'probabilite_cher': probas[1],
            'probabilite_bon_marche': probas[0],
            'confiance': max(probas) * 100,
            'geo_info': geo
        }

@st.cache_resource
def get_predictor():
    return MLPredictor()