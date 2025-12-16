"""
Visualisations croisées DVF x IRCOM
Analyse de l'accessibilité immobilière à Paris par arrondissement
"""

from src.config import paths
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

DVF_FILE = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables-clean.csv"
IRCOM_FILE = paths.data.fiscal.cleaned/"ircom_2020-2023_paris_clean.csv"
ANNONCES_FILE = paths.data.scrapped/"annonces_paris_clean_final.csv"

# Fichiers d'analyse DVF
DVF_ARR_FILE = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_arrondissements.csv"
DVF_TYPE_FILE = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_type_local.csv"
DVF_TEMP_FILE = paths.data.DVF.geocodes.tableau/"dvfgeo_tableau_temporel.csv"

OUTPUT_DIR = paths.plots.viz_croisee.path

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================
print("=" * 80)
print("CHARGEMENT DES DONNÉES")
print("=" * 80 + "\n")

# Charger IRCOM
df_ircom = pd.read_csv(IRCOM_FILE, sep=';', dtype={'dep': str, 'code_commune': str})
print(f"IRCOM chargé: {len(df_ircom)} lignes")

# Charger DVF tableaux
df_dvf_arr = pd.read_csv(DVF_ARR_FILE, sep=';')
df_dvf_type = pd.read_csv(DVF_TYPE_FILE, sep=';')
df_dvf_temp = pd.read_csv(DVF_TEMP_FILE, sep=';')
print(f"DVF arrondissements: {len(df_dvf_arr)} lignes")
print(f"DVF types locaux: {len(df_dvf_type)} lignes")
print(f"DVF temporel: {len(df_dvf_temp)} lignes")

# ============================================================================
# PRÉPARATION DES DONNÉES
# ============================================================================
print("\n" + "=" * 80)
print("PRÉPARATION DES DONNÉES")
print("=" * 80 + "\n")

# Extraire l'arrondissement depuis code_commune (format 754XX -> XX)
df_ircom['arrondissement'] = df_ircom['code_commune'].str[-2:].astype(int)

# Agréger IRCOM par arrondissement (moyenne 2020-2023)
df_ircom_agg = df_ircom.groupby('arrondissement').agg({
    'nb_foyers_fiscaux': 'sum',
    'rfr_foyers_fiscaux': 'sum'
}).reset_index()

# Calculer le RFR moyen par foyer
df_ircom_agg['rfr_moyen_par_foyer'] = (
    df_ircom_agg['rfr_foyers_fiscaux'] / df_ircom_agg['nb_foyers_fiscaux']*1000
)

print("Agrégation IRCOM par arrondissement:")
print(df_ircom_agg.head())

# Préparer DVF arrondissements
df_dvf_arr['arrondissement'] = df_dvf_arr['arrondissement'].astype(int)

# Fusionner DVF et IRCOM
df_merged = df_dvf_arr.merge(
    df_ircom_agg[['arrondissement', 'rfr_moyen_par_foyer']],
    on='arrondissement',
    how='left'
)

print(f"\nDonnées fusionnées: {len(df_merged)} arrondissements")

# ============================================================================
# VIZ 1: ANNÉES DE REVENUS POUR ACHETER UN T2 (45m²)
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 1: ANNÉES DE REVENUS POUR UN T2")
print("=" * 80 + "\n")

# Filtrer les appartements
df_appart = df_dvf_type[df_dvf_type['type_local'] == 'Appartement'].copy()
df_appart['arrondissement'] = df_appart['arrondissement'].astype(int)

# Calculer le prix moyen d'un T2 de 45m²
# CORRECTION: Les prix sont déjà en milliers d'euros dans valeur_fonciere
# On utilise prix_m2_moyen qui est déjà en €/m²
df_appart['prix_t2_45m2'] = df_appart['prix_m2_moyen'] * 45

# Fusionner avec IRCOM
df_t2 = df_appart.merge(
    df_ircom_agg[['arrondissement', 'rfr_moyen_par_foyer']],
    on='arrondissement',
    how='left'
)

# Calculer le nombre d'années de RFR nécessaires
df_t2['annees_rfr_pour_t2'] = df_t2['prix_t2_45m2'] / df_t2['rfr_moyen_par_foyer']

# Trier par nombre d'années
df_t2_sorted = df_t2.sort_values('annees_rfr_pour_t2')

# Créer le graphique
fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=df_t2_sorted['arrondissement'].astype(str) + 'e',
    y=df_t2_sorted['annees_rfr_pour_t2'],
    marker=dict(
        color=df_t2_sorted['annees_rfr_pour_t2'],
        colorscale='RdYlGn_r',
        showscale=True,
        colorbar=dict(title="Années")
    ),
    text=df_t2_sorted['annees_rfr_pour_t2'].round(1),
    textposition='outside',
    hovertemplate=(
        '<b>%{x}</b><br>' +
        'Années de RFR: %{y:.1f}<br>' +
        'Prix T2 45m²: %{customdata[0]:,.0f}€<br>' +
        'RFR moyen: %{customdata[1]:,.0f}€<br>' +
        '<extra></extra>'
    ),
    customdata=np.column_stack((
        df_t2_sorted['prix_t2_45m2'],
        df_t2_sorted['rfr_moyen_par_foyer']
    ))
))

fig1.update_layout(
    title="Nombre d'années de revenus fiscaux nécessaires pour acheter un T2 (45m²)",
    xaxis_title="Arrondissement",
    yaxis_title="Années de RFR",
    template="plotly_white",
    height=600,
    showlegend=False
)

output_file1 = OUTPUT_DIR/ "annees_rfr_pour_t2.html"
fig1.write_html(output_file1)
print(f" Graphique sauvegardé: {output_file1}")

# ============================================================================
# VIZ 2: SCATTER PLOT RFR vs PRIX/M²
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 2: CORRÉLATION RFR vs PRIX/M²")
print("=" * 80 + "\n")

# Préparer les données
df_scatter = df_merged.copy()
df_scatter['arrondissement_label'] = df_scatter['arrondissement'].astype(str) + 'e'

# Créer le scatter plot
fig2 = px.scatter(
    df_scatter,
    x='rfr_moyen_par_foyer',
    y='prix_m2_moyen',
    text='arrondissement_label',
    trendline='ols',
    labels={
        'rfr_moyen_par_foyer': 'RFR moyen par foyer (€)',
        'prix_m2_moyen': 'Prix moyen au m² (€)'
    },
    title="Corrélation entre revenus fiscaux et prix immobiliers par arrondissement"
)

fig2.update_traces(
    textposition='top center',
    marker=dict(size=12, color='#e74c3c', line=dict(width=2, color='white')),
    hovertemplate=(
        '<b>%{text}</b><br>' +
        'RFR moyen: %{x:,.0f}€<br>' +
        'Prix/m²: %{y:,.0f}€<br>' +
        '<extra></extra>'
    )
)

fig2.update_layout(
    template="plotly_white",
    height=600,
    showlegend=True
)

output_file2 = OUTPUT_DIR/ "correlation_rfr_prix_m2.html"
fig2.write_html(output_file2)
print(f" Graphique sauvegardé: {output_file2}")

# ============================================================================
# VIZ 3: ÉVOLUTION INTERACTIVE PRIX vs RFR (2020-2023)
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 3: ÉVOLUTION INTERACTIVE PRIX vs RFR")
print("=" * 80 + "\n")

# Préparer les données temporelles
df_dvf_temp['arrondissement'] = df_dvf_temp['arrondissement'].astype(int)

# Agréger IRCOM par arrondissement et année
df_ircom_temp = df_ircom.groupby(['arrondissement', 'annee']).agg({
    'nb_foyers_fiscaux': 'sum',
    'rfr_foyers_fiscaux': 'sum'
}).reset_index()

df_ircom_temp['rfr_moyen_par_foyer'] = (
    df_ircom_temp['rfr_foyers_fiscaux'] / df_ircom_temp['nb_foyers_fiscaux']*1000
)

# Fusionner DVF temporel avec IRCOM temporel
df_evolution = df_dvf_temp.merge(
    df_ircom_temp[['arrondissement', 'annee', 'rfr_moyen_par_foyer']],
    on=['arrondissement', 'annee'],
    how='left'
)

# Filtrer 2020-2023 (années communes)
df_evolution = df_evolution[df_evolution['annee'].between(2020, 2023)]

# Calculer les indices base 100 en 2020
df_indices = []

for arr in df_evolution['arrondissement'].unique():
    df_arr = df_evolution[df_evolution['arrondissement'] == arr].sort_values('annee')

    if len(df_arr) > 0 and df_arr.iloc[0]['annee'] == 2020:
        prix_2020 = df_arr.iloc[0]['prix_m2_moyen']
        rfr_2020 = df_arr.iloc[0]['rfr_moyen_par_foyer']

        if pd.notna(prix_2020) and pd.notna(rfr_2020) and prix_2020 > 0 and rfr_2020 > 0:
            df_arr['indice_prix'] = (df_arr['prix_m2_moyen'] / prix_2020) * 100
            df_arr['indice_rfr'] = (df_arr['rfr_moyen_par_foyer'] / rfr_2020) * 100
            df_indices.append(df_arr)

df_indices = pd.concat(df_indices, ignore_index=True)

# Créer l'animation
fig3 = px.scatter(
    df_indices,
    x='indice_rfr',
    y='indice_prix',
    animation_frame='annee',
    text=df_indices['arrondissement'].astype(str) + 'e',
    labels={
        'indice_rfr': 'Indice RFR (base 100 en 2020)',
        'indice_prix': 'Indice Prix/m² (base 100 en 2020)'
    },
    title="Évolution comparative des prix immobiliers et des revenus fiscaux (2020-2023)",
    range_x=[95, 115],
    range_y=[95, 115]
)

fig3.update_traces(
    textposition='top center',
    marker=dict(size=12, line=dict(width=2, color='white'))
)

# Ajouter une ligne de référence (évolution identique)
fig3.add_trace(go.Scatter(
    x=[95, 115],
    y=[95, 115],
    mode='lines',
    line=dict(dash='dash', color='gray'),
    name='Évolution identique',
    showlegend=True
))

fig3.update_layout(
    template="plotly_white",
    height=600
)

output_file3 = OUTPUT_DIR/ "evolution_interactive_prix_rfr.html"
fig3.write_html(output_file3)
print(f" Graphique sauvegardé: {output_file3}")

# ============================================================================
# VIZ 4: RATIO PRIX/REVENU PAR ARRONDISSEMENT
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 4: RATIO PRIX/REVENU")
print("=" * 80 + "\n")

df_ratio = df_merged.copy()
df_ratio['ratio_prix_revenu'] = df_ratio['prix_m2_moyen'] / df_ratio['rfr_moyen_par_foyer']
df_ratio = df_ratio.sort_values('ratio_prix_revenu')

fig4 = go.Figure()

fig4.add_trace(go.Bar(
    x=df_ratio['arrondissement'].astype(str) + 'e',
    y=df_ratio['ratio_prix_revenu'],
    marker=dict(
        color=df_ratio['ratio_prix_revenu'],
        colorscale='Reds',
        showscale=True,
        colorbar=dict(title="Ratio")
    ),
    text=df_ratio['ratio_prix_revenu'].round(3),
    textposition='outside',
    hovertemplate=(
        '<b>%{x}</b><br>' +
        'Ratio: %{y:.3f}<br>' +
        'Prix/m²: %{customdata[0]:,.0f}€<br>' +
        'RFR moyen: %{customdata[1]:,.0f}€<br>' +
        '<extra></extra>'
    ),
    customdata=np.column_stack((
        df_ratio['prix_m2_moyen'],
        df_ratio['rfr_moyen_par_foyer']
    ))
))

fig4.update_layout(
    title="Ratio Prix au m² / RFR moyen par arrondissement",
    xaxis_title="Arrondissement",
    yaxis_title="Ratio (Prix/m² / RFR)",
    template="plotly_white",
    height=600,
    showlegend=False
)

output_file4 = OUTPUT_DIR/ "ratio_prix_revenu.html"
fig4.write_html(output_file4)
print(f" Graphique sauvegardé: {output_file4}")

# ============================================================================
# VIZ 5: HEATMAP ÉVOLUTION DES PRIX PAR ARRONDISSEMENT (2020-2025)
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 5: HEATMAP ÉVOLUTION DES PRIX")
print("=" * 80 + "\n")

# Préparer les données pour la heatmap
df_heatmap_prix = df_dvf_temp.pivot_table(
    index='arrondissement',
    columns='annee',
    values='prix_m2_moyen',
    aggfunc='mean'
)

# Calculer l'évolution en % par rapport à 2020
if 2020 in df_heatmap_prix.columns:
    for year in df_heatmap_prix.columns:
        if year != 2020:
            col_name = f'evolution_{year}'
            df_heatmap_prix[col_name] = (
                (df_heatmap_prix[year] - df_heatmap_prix[2020]) / df_heatmap_prix[2020] * 100
            )

    # CORRECTION: Filtrer les colonnes d'évolution correctement
    evolution_cols = [col for col in df_heatmap_prix.columns if isinstance(col, str) and col.startswith('evolution_')]
    df_heatmap_evolution = df_heatmap_prix[evolution_cols].copy()
    df_heatmap_evolution.columns = [col.replace('evolution_', '') for col in df_heatmap_evolution.columns]

    # Créer la heatmap
    fig5 = go.Figure(data=go.Heatmap(
        z=df_heatmap_evolution.values,
        x=df_heatmap_evolution.columns,
        y=df_heatmap_evolution.index.astype(str) + 'e',
        colorscale='RdYlGn',
        zmid=0,
        text=df_heatmap_evolution.values.round(1),
        texttemplate='%{text}%',
        textfont={"size": 10},
        colorbar=dict(title="Évolution (%)")
    ))

    fig5.update_layout(
        title="Évolution des prix au m² par arrondissement (% par rapport à 2020)",
        xaxis_title="Année",
        yaxis_title="Arrondissement",
        template="plotly_white",
        height=700
    )

    output_file5 = OUTPUT_DIR/ "heatmap_evolution_prix.html"
    fig5.write_html(output_file5)
    print(f" Graphique sauvegardé: {output_file5}")
else:
    print("⚠ Année 2020 non disponible pour calculer l'évolution")

# ============================================================================
# VIZ 6: DASHBOARD SYNTHÉTIQUE
# ============================================================================
print("\n" + "=" * 80)
print("VIZ 6: DASHBOARD SYNTHÉTIQUE")
print("=" * 80 + "\n")

# Créer un dashboard avec 4 sous-graphiques
fig6 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Prix moyen au m² par arrondissement',
        'RFR moyen par foyer',
        'Années de RFR pour un T2',
        'Ratio Prix/Revenu'
    ),
    specs=[[{'type': 'bar'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'bar'}]]
)

# Subplot 1: Prix moyen au m²
df_plot = df_merged.sort_values('prix_m2_moyen', ascending=False)
fig6.add_trace(
    go.Bar(
        x=df_plot['arrondissement'].astype(str) + 'e',
        y=df_plot['prix_m2_moyen'],
        marker_color='#3498db',
        name='Prix/m²'
    ),
    row=1, col=1
)

# Subplot 2: RFR moyen
df_plot2 = df_merged.sort_values('rfr_moyen_par_foyer', ascending=False)
fig6.add_trace(
    go.Bar(
        x=df_plot2['arrondissement'].astype(str) + 'e',
        y=df_plot2['rfr_moyen_par_foyer'],
        marker_color='#2ecc71',
        name='RFR moyen'
    ),
    row=1, col=2
)

# Subplot 3: Années pour T2
fig6.add_trace(
    go.Bar(
        x=df_t2_sorted['arrondissement'].astype(str) + 'e',
        y=df_t2_sorted['annees_rfr_pour_t2'],
        marker_color='#e74c3c',
        name='Années RFR'
    ),
    row=2, col=1
)

# Subplot 4: Ratio Prix/Revenu
fig6.add_trace(
    go.Bar(
        x=df_ratio['arrondissement'].astype(str) + 'e',
        y=df_ratio['ratio_prix_revenu'],
        marker_color='#f39c12',
        name='Ratio'
    ),
    row=2, col=2
)

fig6.update_layout(
    title_text="dashboard d'accessibilité immobilière à Paris",
    showlegend=False,
    template="plotly_white",
    height=900
)

output_file6 = OUTPUT_DIR/ "dashboard_accessibilite.html"
fig6.write_html(output_file6)
print(f"Graphique sauvegardé: {output_file6}")

print(f"\n6 visualisations générées dans: {OUTPUT_DIR}")
print("\n1. annees_rfr_pour_t2.html")
print("2. correlation_rfr_prix_m2.html")
print("3. evolution_interactive_prix_rfr.html")
print("4. ratio_prix_revenu.html")
print("5. heatmap_evolution_prix.html")
print("6. dashboard_accessibilite.html")