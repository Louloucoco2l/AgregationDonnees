import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.data_loader import load_dvf_data, load_rfr_data, load_annonces_data

st.set_page_config(page_title="DVF Paris - Accueil", layout="wide")

st.title("Observatoire Immobilier Parisien")
st.markdown("### Synthèse du marché : Ventes Actées vs Offre Actuelle vs Revenus")

# Chargement
df_dvf = load_dvf_data()
df_rfr_agg = load_rfr_data(aggregate=True)  # On prend la version agrégée pour les KPIs
df_ads = load_annonces_data()

# --- KPIs GLOBAUX (Dernière année disponible) ---
col1, col2, col3 = st.columns(3)

# KPI 1: DVF
with col1:
    st.subheader("Ventes Actées (DVF)")
    if not df_dvf.empty:
        last_year = df_dvf['annee'].max()
        df_last = df_dvf[df_dvf['annee'] == last_year]
        prix_actuel = df_last['prix_m2'].mean()
        vol = len(df_last)
        st.metric(f"Prix m² moyen ({last_year})", f"{prix_actuel:,.0f} €")
        st.metric("Volume transactions", f"{vol:,}")
    else:
        st.warning("DVF non disponible")

# KPI 2: Annonces
with col2:
    st.subheader("Offre Actuelle (Annonces)")
    if not df_ads.empty:
        prix_annonce = df_ads['prix_m2'].mean()
        nb_ads = len(df_ads)
        delta = ((prix_annonce - prix_actuel) / prix_actuel * 100) if not df_dvf.empty else 0
        st.metric("Prix m² moyen (Affiché)", f"{prix_annonce:,.0f} €", delta=f"{delta:+.1f}% vs DVF")
        st.metric("Volume annonces", f"{nb_ads:,}")
    else:
        st.warning("Annonces non disponibles")

# KPI 3: Fiscalité
with col3:
    st.subheader("Revenus (RFR)")
    if not df_rfr_agg.empty:
        last_rfr_year = df_rfr_agg['annee'].max()
        df_rfr_last = df_rfr_agg[df_rfr_agg['annee'] == last_rfr_year]

        # Moyenne pondérée pour tout Paris
        total_rfr = df_rfr_last['rfr_foyers_fiscaux'].sum() * 1000
        total_foyers = df_rfr_last['nb_foyers_fiscaux'].sum()
        rfr_moy_paris = total_rfr / total_foyers if total_foyers else 0

        st.metric(f"Revenu Fiscal Moyen ({last_rfr_year})", f"{rfr_moy_paris:,.0f} €/foyer")
    else:
        st.warning("Données fiscales non disponibles")

st.divider()

# --- GRAPHIQUE SYNTHÈSE ---
if not df_dvf.empty and not df_ads.empty:
    st.subheader("Écart de Prix par Arrondissement : Réalité (DVF) vs Prétentions (Annonces)")

    # Agrégation DVF (Dernière année)
    dvf_agg = df_dvf[df_dvf['annee'] == last_year].groupby('code_arrondissement')['prix_m2'].median().reset_index()
    dvf_agg['Type'] = f'Ventes ({last_year})'

    # Agrégation Annonces
    ads_agg = df_ads.groupby('code_arrondissement')['prix_m2'].median().reset_index()
    ads_agg['Type'] = 'Annonces (Actuel)'

    # Fusion
    df_chart = pd.concat([dvf_agg, ads_agg])

    fig = px.bar(df_chart, x='code_arrondissement', y='prix_m2', color='Type', barmode='group',
                 color_discrete_map={f'Ventes ({last_year})': '#2E86C1', 'Annonces (Actuel)': '#E74C3C'},
                 labels={'prix_m2': 'Prix Médian (€/m²)', 'code_arrondissement': 'Arrondissement'},
                 height=500)
    st.plotly_chart(fig, use_container_width=True)