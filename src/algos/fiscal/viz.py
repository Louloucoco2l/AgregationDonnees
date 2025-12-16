"""
Visualisations des données fiscales IRCOM
Analyse des revenus fiscaux par arrondissement et tranche de RFR
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import paths
# ============================================================================
# CONFIGURATION
# ============================================================================
INPUT_FILE = paths.data.fiscal.cleaned/"ircom_2020-2023_paris_clean.csv"
OUTPUT_DIR = paths.plots.fiscal.path


print("CHARGEMENT DES DONNÉES FISCALES")

df_ircom = pd.read_csv(INPUT_FILE, sep=';')
print(f"Données chargées: {len(df_ircom):,} lignes")
print(f"Années disponibles: {sorted(df_ircom['annee'].unique())}")
print(f"Arrondissements: {df_ircom['libelle_commune'].nunique()}")
print(f"Tranches RFR: {df_ircom['tranche_rfr'].nunique()}\n")

print("PRÉPARATION DES DONNÉES")
# Extraire le numéro d'arrondissement
df_ircom['arr_num'] = df_ircom['libelle_commune'].str.extract(r'(\d+)').astype(int)
df_ircom['arr_label'] = df_ircom['arr_num'].astype(str) + 'e'

# Calculer la part de chaque tranche par arrondissement (moyenne sur toutes les années)
df_pivot = df_ircom.groupby(['arr_label', 'tranche_rfr'])['nb_foyers_fiscaux'].sum().reset_index()

# Calculer le total par arrondissement
total_par_arr = df_pivot.groupby('arr_label')['nb_foyers_fiscaux'].sum().reset_index()
total_par_arr.columns = ['arr_label', 'total_foyers']

# Merger et calculer les pourcentages
df_pivot = df_pivot.merge(total_par_arr, on='arr_label')
df_pivot['part_pct'] = (df_pivot['nb_foyers_fiscaux'] / df_pivot['total_foyers']) * 100

# Créer la matrice pour la heatmap
heatmap_data = df_pivot.pivot(index='tranche_rfr', columns='arr_label', values='part_pct')

# Ordonner les tranches de RFR
ordre_tranches = [
    '0 à 10 000',
    '10 001 à 12 000',
    '12 001 à 15 000',
    '15 001 à 20 000',
    '20 001 à 30 000',
    '30 001 à 50 000',
    '50 001 à 100 000',
    '+ de 100 000'
]

# Ordonner les arrondissements
ordre_arr = [f"{i}e" for i in range(1, 21)]

# Réordonner la matrice
heatmap_data = heatmap_data.reindex(index=ordre_tranches, columns=ordre_arr)

print("Matrice heatmap créée")
print(f"Dimensions: {heatmap_data.shape}\n")


print("CRÉATION HEATMAP: PART DES FOYERS PAR TRANCHE ET ARRONDISSEMENT")
fig1 = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns,
    y=heatmap_data.index,
    colorscale='RdYlGn',
    text=np.round(heatmap_data.values, 1),
    texttemplate='%{text}%',
    textfont={"size": 10},
    colorbar=dict(title="Part (%)")
))

fig1.update_layout(
    title={
        'text': "Distribution des foyers fiscaux par tranche de RFR et arrondissement<br><sub>Données agrégées 2020-2023</sub>",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="Arrondissement",
    yaxis_title="Tranche de Revenu Fiscal de Référence (€)",
    height=700,
    width=1400,
    font=dict(size=12)
)

output_file_1 = OUTPUT_DIR/ "heatmap_rfr_arrondissements.html"
fig1.write_html(output_file_1)
print(f"✓ Heatmap sauvegardée: {output_file_1}\n")


print("CRÉATION: PROFIL SOCIO-ÉCONOMIQUE PAR ARRONDISSEMENT")
# Calculer le RFR moyen par arrondissement
df_rfr_arr = df_ircom.groupby('arr_label').agg({
    'nb_foyers_fiscaux': 'sum',
    'rfr_foyers_fiscaux': 'sum',
    'impot_net_total': 'sum'
}).reset_index()

df_rfr_arr['rfr_moyen_par_foyer'] = df_rfr_arr['rfr_foyers_fiscaux'] / df_rfr_arr['nb_foyers_fiscaux']
df_rfr_arr['impot_moyen_par_foyer'] = df_rfr_arr['impot_net_total'] / df_rfr_arr['nb_foyers_fiscaux']

# Trier par RFR moyen
df_rfr_arr = df_rfr_arr.sort_values('rfr_moyen_par_foyer', ascending=True)

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=df_rfr_arr['arr_label'],
    y=df_rfr_arr['rfr_moyen_par_foyer'],
    name='RFR moyen par foyer',
    marker_color='lightblue',
    text=np.round(df_rfr_arr['rfr_moyen_par_foyer'], 0),
    texttemplate='%{text:,.0f}k€',
    textposition='outside'
))

fig2.update_layout(
    title={
        'text': "Revenu Fiscal de Référence moyen par foyer et arrondissement<br><sub>Données agrégées 2020-2023</sub>",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="Arrondissement (classé par RFR croissant)",
    yaxis_title="RFR moyen par foyer (k€)",
    height=600,
    width=1400,
    showlegend=False,
    font=dict(size=12)
)

output_file_2 = OUTPUT_DIR/ "rfr_moyen_arrondissements.html"
fig2.write_html(output_file_2)
print(f"✓ Graphique RFR moyen sauvegardé: {output_file_2}\n")


print("CRÉATION: ÉVOLUTION TEMPORELLE DU RFR")
# Calculer le RFR moyen par arrondissement et année
df_evolution = df_ircom.groupby(['annee', 'arr_label']).agg({
    'nb_foyers_fiscaux': 'sum',
    'rfr_foyers_fiscaux': 'sum'
}).reset_index()

df_evolution['rfr_moyen'] = df_evolution['rfr_foyers_fiscaux'] / df_evolution['nb_foyers_fiscaux']

# Sélectionner quelques arrondissements représentatifs
arr_selection = ['7e', '8e', '16e', '18e', '19e', '20e']
df_evolution_sel = df_evolution[df_evolution['arr_label'].isin(arr_selection)]

fig3 = px.line(
    df_evolution_sel,
    x='annee',
    y='rfr_moyen',
    color='arr_label',
    markers=True,
    title="Évolution du RFR moyen par foyer (arrondissements sélectionnés)<br><sub>2020-2023</sub>",
    labels={
        'annee': 'Année',
        'rfr_moyen': 'RFR moyen par foyer (k€)',
        'arr_label': 'Arrondissement'
    }
)

fig3.update_layout(
    height=600,
    width=1200,
    font=dict(size=12),
    hovermode='x unified'
)

output_file_3 = OUTPUT_DIR/ "evolution_rfr_temporelle.html"
fig3.write_html(output_file_3)
print(f"✓ Évolution temporelle sauvegardée: {output_file_3}\n")

print("CRÉATION: DISTRIBUTION DES TRANCHES PAR ARRONDISSEMENT")
# Préparer les données pour le stacked bar chart
df_stacked = df_pivot.copy()

# Ordonner par RFR moyen croissant
ordre_arr_rfr = df_rfr_arr.sort_values('rfr_moyen_par_foyer')['arr_label'].tolist()

fig4 = go.Figure()

colors = px.colors.sequential.RdBu_r

for i, tranche in enumerate(ordre_tranches):
    df_tranche = df_stacked[df_stacked['tranche_rfr'] == tranche]
    df_tranche = df_tranche.set_index('arr_label').reindex(ordre_arr_rfr)

    fig4.add_trace(go.Bar(
        name=tranche,
        x=df_tranche.index,
        y=df_tranche['part_pct'],
        marker_color=colors[i] if i < len(colors) else colors[-1],
        text=np.round(df_tranche['part_pct'], 1),
        texttemplate='%{text}%',
        textposition='inside',
        textfont=dict(size=9)
    ))

fig4.update_layout(
    barmode='stack',
    title={
        'text': "Distribution des tranches de RFR par arrondissement<br><sub>Données agrégées 2020-2023 (classé par RFR moyen croissant)</sub>",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="Arrondissement",
    yaxis_title="Part des foyers (%)",
    height=700,
    width=1400,
    font=dict(size=11),
    legend=dict(
        title="Tranche RFR (€)",
        orientation="v",
        yanchor="middle",
        y=0.5,
        xanchor="left",
        x=1.02
    )
)

output_file_4 = OUTPUT_DIR/ "distribution_tranches_stacked.html"
fig4.write_html(output_file_4)
print(f"✓ Distribution stacked sauvegardée: {output_file_4}\n")

# ============================================================================
# VISUALISATION 5: INÉGALITÉS - RATIO HAUTS/BAS REVENUS
# ============================================================================
print("=" * 80)
print("CRÉATION: ANALYSE DES INÉGALITÉS")
print("=" * 80 + "\n")

# Calculer la part des hauts revenus (>100k) vs bas revenus (<20k)
df_inegalites = df_ircom.copy()

# Classifier les tranches
df_inegalites['categorie'] = df_inegalites['tranche_rfr'].apply(
    lambda x: 'Bas revenus (<20k)' if any(
        t in x for t in ['0 à 10 000', '10 001 à 12 000', '12 001 à 15 000', '15 001 à 20 000'])
    else ('Hauts revenus (>100k)' if '+ de 100 000' in x else 'Revenus moyens')
)

df_cat = df_inegalites.groupby(['arr_label', 'categorie'])['nb_foyers_fiscaux'].sum().reset_index()
df_cat_pivot = df_cat.pivot(index='arr_label', columns='categorie', values='nb_foyers_fiscaux').fillna(0)

# Calculer le ratio
df_cat_pivot['ratio_hauts_bas'] = df_cat_pivot['Hauts revenus (>100k)'] / df_cat_pivot['Bas revenus (<20k)']
df_cat_pivot = df_cat_pivot.sort_values('ratio_hauts_bas', ascending=False).reset_index()

fig5 = go.Figure()

fig5.add_trace(go.Bar(
    x=df_cat_pivot['arr_label'],
    y=df_cat_pivot['ratio_hauts_bas'],
    marker_color=df_cat_pivot['ratio_hauts_bas'],
    marker_colorscale='Viridis',
    text=np.round(df_cat_pivot['ratio_hauts_bas'], 2),
    texttemplate='%{text}',
    textposition='outside'
))

fig5.update_layout(
    title={
        'text': "Ratio Hauts revenus / Bas revenus par arrondissement<br><sub>Hauts: >100k€ | Bas: <20k€ (données 2020-2023)</sub>",
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title="Arrondissement (classé par ratio décroissant)",
    yaxis_title="Ratio Hauts/Bas revenus",
    height=600,
    width=1400,
    showlegend=False,
    font=dict(size=12)
)

output_file_5 = OUTPUT_DIR/ "ratio_inegalites_arrondissements.html"
fig5.write_html(output_file_5)
print(f"Analyse inégalités sauvegardée: {output_file_5}\n")

print("GÉNÉRATION TERMINÉE")

print("Fichiers générés:")
print(f"  1. {output_file_1}")
print(f"  2. {output_file_2}")
print(f"  3. {output_file_3}")
print(f"  4. {output_file_4}")
print(f"  5. {output_file_5}")
