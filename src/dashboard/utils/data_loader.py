import pandas as pd
import streamlit as st
from pathlib import Path
import numpy as np

# Détection de l'environnement (Local ou Serveur)
try:
    from src.config import paths

    # Utilisation des chemins config si disponible
    BASE_DIR = Path(__file__).resolve().parents[3]
    PATH_DVF = BASE_DIR / "data/DVF/geocodes/cleaned/dvf_paris_2020-2025-exploitables-clean.csv"
    PATH_RFR = BASE_DIR / "data/fiscal/cleaned/ircom_2020-2023_paris_clean.csv"
    PATH_ANNONCES = BASE_DIR / "data/scrapped/annonces_paris_clean_final.csv"
except ImportError:
    # Fallback chemins relatifs
    PATH_DVF = Path("data/DVF/geocodes/cleaned/dvf_paris_2020-2025-exploitables-clean.csv")
    PATH_RFR = Path("data/fiscal/cleaned/ircom_2020-2023_paris_clean.csv")
    PATH_ANNONCES = Path("data/scrapped/annonces_paris_clean_final.csv")


@st.cache_data
def load_dvf_data():
    """Charge les données DVF."""
    if not PATH_DVF.exists():
        return pd.DataFrame()

    df = pd.read_csv(PATH_DVF, sep=';', low_memory=False)

    # Standardisation Arrondissement (1-20)
    if 'code_arrondissement' not in df.columns and 'arrondissement' in df.columns:
        df.rename(columns={'arrondissement': 'code_arrondissement'}, inplace=True)

    return df


@st.cache_data
def load_rfr_data(aggregate=True):
    """
    Charge les données fiscales IRCOM.

    Args:
        aggregate (bool): Si True, retourne une ligne par arrondissement (moyennes).
                          Si False, retourne les données détaillées par tranche RFR.
    """
    if not PATH_RFR.exists():
        return pd.DataFrame()

    df = pd.read_csv(PATH_RFR, sep=';')

    # Création colonne code_arrondissement (1-20) depuis code_commune (101-120)
    # Le fichier montre code_commune=101 pour Paris 1er.
    if 'code_commune' in df.columns:
        df['code_arrondissement'] = df['code_commune'] % 100

    if aggregate:
        # On agrège pour avoir une vision par arrondissement/année (pour les cartes)
        # RFR Moyen = Somme(RFR total du foyer) / Somme(Nb foyers)
        df_agg = df.groupby(['annee', 'code_arrondissement']).agg({
            'nb_foyers_fiscaux': 'sum',
            'rfr_foyers_fiscaux': 'sum',
            'impot_net_total': 'sum'
        }).reset_index()

        df_agg['revenu_fiscal_moyen'] = (df_agg['rfr_foyers_fiscaux'] / df_agg[
            'nb_foyers_fiscaux']) * 1000000  # Si c'était en K€ vérifier unité
        # Note: Dans ircom clean, rfr_foyers_fiscaux semble être la somme exacte ou en K€ ?
        # Snippet: "rfr_foyers_fiscaux";"8001.877" pour 2684 foyers -> ~3€ ? Non, c'est en K€.
        # Donc * 1000 pour avoir des euros.
        df_agg['revenu_fiscal_moyen'] = (df_agg['rfr_foyers_fiscaux'] * 1000) / df_agg['nb_foyers_fiscaux']

        return df_agg
    else:
        # On retourne les données brutes avec tranches pour l'analyse détaillée
        return df


@st.cache_data
def load_annonces_data():
    """Charge les annonces scrappées."""
    if not PATH_ANNONCES.exists():
        return pd.DataFrame()

    df = pd.read_csv(PATH_ANNONCES, sep=';')

    # Standardisation Arrondissement (75016 -> 16)
    if 'localisation' in df.columns:
        # Extraction des 2 derniers chiffres
        df['code_arrondissement'] = df['localisation'].astype(str).str[-2:].astype(int)

    # Renommage colonne type
    if 'type' in df.columns and 'type_local' not in df.columns:
        df.rename(columns={'type': 'type_local'}, inplace=True)

    return df