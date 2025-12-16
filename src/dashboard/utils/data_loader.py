"""
Chargement des datasets avec cache Streamlit

Fonctions :
    - load_dvf() : Ventes DVF 2020-2025
    - load_ircom() : Revenus fiscaux 2020-2023
    - load_annonces() : Annonces scrappées
    - load_all_data() : Charge tout en un dict
"""

import streamlit as st
import pandas as pd
from src.config import paths

DATA_DIR = paths.data.path


@st.cache_data(ttl=3600)
def load_dvf():
    """
    Charge les ventes DVF géocodées nettoyées

    Returns:
        DataFrame avec ~191k lignes, colonnes :
            - id_mutation, date_mutation, valeur_fonciere
            - arrondissement, type_local, surface_reelle_bati
            - nombre_pieces_principales, prix_m2
            - latitude, longitude
    """
    return pd.read_csv(
        DATA_DIR / "DVF/geocodes/cleaned/dvf_paris_2020-2025-exploitables-clean.csv",
        sep=';'
    )


@st.cache_data(ttl=3600)
def load_ircom():
    """
    Charge les données fiscales IRCOM

    Returns:
        DataFrame avec ~640 lignes (20 arr × 8 tranches × 4 ans), colonnes :
            - annee, arrondissement, tranche_rfr
            - nb_foyers_fiscaux, rfr_foyers_fiscaux
            - impot_net_total
    """
    return pd.read_csv(
        DATA_DIR / "fiscal/cleaned/ircom_2020-2023_paris_clean.csv",
        sep=';'
    )


@st.cache_data(ttl=3600)
def load_annonces():
    """
    Charge les annonces immobilières scrappées

    Returns:
        DataFrame avec colonnes :
            - source, titre, prix, surface, prix_m2
            - type, pieces, arrondissement
            - adresse, url, date_scraping
    """
    return pd.read_csv(
        DATA_DIR / "scrapped/annonces_paris_clean_final.csv",
        sep=';'
    )


@st.cache_data(ttl=3600)
def load_dvf_tableau_arrondissements():
    """
    Charge le tableau pré-agrégé DVF par arrondissement

    Returns:
        DataFrame avec statistiques par arrondissement :
            - prix_m2_moyen, prix_m2_median, prix_m2_std
            - nombre_transactions, surface_moyenne
            - latitude, longitude
    """
    return pd.read_csv(
        DATA_DIR / "DVF/geocodes/tableau/dvfgeo_tableau_arrondissements.csv",
        sep=';'
    )


@st.cache_data(ttl=3600)
def load_dvf_tableau_temporel():
    """
    Charge le tableau pré-agrégé DVF par année et arrondissement

    Returns:
        DataFrame avec évolution temporelle :
            - annee, arrondissement
            - prix_m2_moyen, prix_m2_median
            - nombre_transactions, surface_moyenne
    """
    return pd.read_csv(
        DATA_DIR / "DVF/geocodes/tableau/dvfgeo_tableau_temporel.csv",
        sep=';'
    )


@st.cache_data(ttl=3600)
def load_dvf_tableau_type_local():
    """
    Charge le tableau pré-agrégé DVF par type de local et arrondissement

    Returns:
        DataFrame avec statistiques par type :
            - arrondissement, type_local
            - prix_m2_moyen, prix_m2_median
            - nombre_transactions, surface_moyenne
    """
    return pd.read_csv(
        DATA_DIR / "DVF/geocodes/tableau/dvfgeo_tableau_type_local.csv",
        sep=';'
    )


def load_all_data():
    """
    Charge tous les datasets principaux

    Returns:
        Dict avec clés : 'dvf', 'ircom', 'annonces'
    """
    return {
        'dvf': load_dvf(),
        'ircom': load_ircom(),
        'annonces': load_annonces()
    }