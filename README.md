# AgregationDonnees - Analyse du Marche Immobilier Parisien

Plateforme d'analyse et de prediction du marche immobilier parisien combinant :
- **Ventes effectuees** (DVF geocodees - data.gouv.fr)
- **Revenus fiscaux** (IRCOM - DGFiP)
- **Annonces immobilières** (scraping multi-sources)

Le projet agrège, nettoie, analyse et modelise ces donnees pour fournir des insights sur l'accessibilite immobilière et des predictions de prix via Machine Learning.



## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│ SOURCES DE DONNeES │
├─────────────────────────────────────────────────────────────────┤
│ DVF Geocodees IRCOM Fiscales Annonces Scrappees │
│ (data.gouv.fr) (DGFiP) (Multi-sites) │
│ 2020-2025 2020-2023 Temps reel │
│ ~419K lignes ~640 lignes Variable │
└──────────┬────────────────────┬────────────────────┬────────────┘
│ │ │
▼ ▼ ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ NETTOYAGE │ │ NETTOYAGE │ │ NETTOYAGE │
│ & FILTRAGE │ │ & AGReGATION│ │ & FUSION │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
│ │ │
▼ ▼ ▼
┌──────────────────────────────────────────────────────┐
│ DONNeES NETTOYeES │
├──────────────────────────────────────────────────────┤
│ 191K ventes │ 640 tranches RFR │ Annonces │
│ exploitables │ par arrondissement│ geolocalisees│
└──────┬──────────────────┬──────────────────┬─────────┘
│ │ │
▼ ▼ ▼
┌──────────────────────────────────────────────────────┐
│ ANALYSES & VISUALISATIONS │
├──────────────────────────────────────────────────────┤
│ • evolution temporelle prix/m² │
│ • Heatmaps arrondissements │
│ • Correlations prix/revenus │
│ • Accessibilite immobilière (annees de RFR) │
└──────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────┐
│ MODÈLES MACHINE LEARNING │
├──────────────────────────────────────────────────────┤
│ • Gradient Boosting (prediction prix/m²) │
│ • R² = 0.27 | MAE = 2079.86€/m² │
│ • Regression Logistique (classification cher/bon marché) │
│ • ROC-AUC = 0.7690 | Accuracy 0.7024 │
└──────────────────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────────────────┐
│ DASHBOARD STREAMLIT │
├──────────────────────────────────────────────────────┤
│ • Exploration interactive des donnees │
│ • Predictions ML en temps reel │
│ • Analyses croisees │
└──────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Cloner le repo
git clone https://github.com/Louloucoco2l/AgregationDonnees.git
cd AgregationDonnees

# Installer les dependances
pip install -r requirements.txt

# Lancer le dashboard
streamlit run src/dashboard/app.py

# Lancer le serveur API
python src/api/main.py
```

## Structure du Projet
```
AgregationDonnees/
│
├── src/                              # Code source principal
│   ├── config.py                     # Configuration chemins (système Node dynamique)
│   ├── dashboard/                    # Application Streamlit
│   │   ├── app.py                    # Page d'accueil dashboard
│   │   ├── pages/                    # Pages multi-onglets
│   │   │   ├── analyse_annonces.py
│   │   │   ├── analyse_croisee.py
│   │   │   ├── analyse_DVF.py
│   │   │   ├── analyse_fiscal.py
│   │   │   ├── explorateur_donnees.py
│   │   │   └── prediction_ML.py
│   │   ├── utils/                    # Utilitaires
│   │   │   ├── data_loader.py        # Chargement datasets (avec cache)
│   │   │   ├── ml_predictor.py       # Wrapper modèles ML
│   │   │   └── viz_helper.py         # Intégrateur visualisations
│   │   ├── algos/                    # Scripts de traitement
│   │   │    ├── DVF/
│   │   │    │   ├── aggregation nettoyage preparation/
│   │   │    │   │   ├── agregateur primaire.py    # Agrège DVF brutes → Paris
│   │   │    │   │   ├── clean.py                  # Nettoie, detecte aberrantes
│   │   │    │   │   ├── stats.py                  # Statistiques descriptives
│   │   │    │   │   └── tableau_prep.py           # Genère CSVs aperçus
│   │   │    │   ├── ML/
│   │   │    │   │   ├── preprocessing.py          # Feature engineering
│   │   │    │   │   └── prediction.py             # Entraînement modèles
│   │   │    │   └── viz/
│   │   │    │       ├── carte folium.py           # Carte interactive
│   │   │    │       └── viz matplotlib.py         # Graphiques PNG
│   │   │    │
│   │   │    ├── fiscal/
│   │   │    │   ├── IRCOM cleaner.py              # Nettoie donnees fiscales
│   │   │    │   └── viz.py                        # Visualisations IRCOM
│   │   │    │
│   │   │    ├── scrapped/
│   │   │    │   ├── clean/
│   │   │    │   │   └── annonces_cleaner.py       # Pipeline nettoyage annonces
│   │   │    │   ├── scrapper/
│   │   │    │   │   ├── multi_scraper_gui.py      # Interface scraping
│   │   │    │   │   └── scrapp*.py                # Scrapers par site
│   │   │    │   └── viz/
│   │   │    │       ├── carte folium.py           # Carte annonces
│   │   │    │       └── viz marplotlib.py         # figures PNG
│   │   │    │
│   │   │    └── viz_croisee/                      # Analyses croisees inter sources de données
│   │   │       └── viz_croisee.py                 # Correlations
│   │   │ 
│   │   │
├── datas/                            # Donnees (non versionnees)
│   ├── DVF/
│   │   ├── geocodes/
│   │   │   ├── brut/                     # DVF brutes (2020_75.csv - 2025_75.csv)
│   │   │   ├── cleaned/                  # DVF nettoyees
│   │   │   └── tableau/                  # Agregations pre-calculees
│   │   └── analysis/                     # Analyses statistiques
│   │
│   ├── fiscal/
│   │   ├── brut/                         # IRCOM brutes (2020.xlsx - 2023.xlsx)
│   │   └── cleaned/                      # IRCOM agglomérées et nettoyees
│   │
│   └── scrapped/                         # Annonces scrappees
│       ├── annonces_*_paris.csv          # Par source
│       └── annonces_paris_clean_final.csv # Fusionnees nettoyees
│
├── models/                           # Artefacts ML
│   ├── model_linear_regression.pkl       # Modèle prediction prix
│   ├── model_logistic_regression.pkl     # Modèle classification
│   ├── scaler.pkl                        # Normaliseur features
│   ├── feature_names.pkl                 # Noms colonnes
│   └── resultats_ml.txt                  # Metriques performances
│
├── plots/                            # Visualisations generees
│   ├── DVF/                              # Cartes, heatmaps DVF
│   ├── fiscal/                           # Visualisations IRCOM
│   ├── scrapped/                         # Visualisations annonces
│   └── viz_croisee/                      # Analyses croisees
│
├── docs/                             # Documentation
│   └── data_dictionary.md                # Schemas des donnees
│
├──.gitignore
├──logs_estimation.db                 # Base de donnees des estimations ML
├──requirements.txt                   # Dependances Python nécésssaires  
└── README.md                         # Ce fichier
```
# Pipelines de Donnees
## Pipeline DVF (Ventes Effectuees)
### Agregation & Filtrage     
Script : algos/DVF/aggregation nettoyage preparation/agregateur primaire.py

Entree :

datas/DVF/geocodes/brut/2020_75.csv → 2025_75.csv (6 fichiers)  
Source : data.gouv.fr - DVF geocodees   
https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees   
Lecture par chunks (50k lignes) pour optimiser memoire          

Sortie :

datas/DVF/geocodes/cleaned/dvf_paris_2020-2025.csv (~221K lignes)
Statistiques :

419K lignes brutes → 221K lignes Paris (52.7%)
Periode : 2020-2025
Departements : 75 uniquement
etape 2 : Nettoyage & Detection Aberrantes
Script : algos/DVF/aggregation nettoyage preparation/clean.py

Traitement :

### Detection aberrantes hautes (methode IQR stricte)
Q1 = df['prix_m2'].quantile(0.25)
Q3 = df['prix_m2'].quantile(0.75)
IQR = Q3 - Q1
seuil_haut = Q3 + 3 * IQR  # ~36,846 €/m²

### Separation
df_exploitables = df[df['prix_m2'] <= seuil_haut]
df_aberrantes_haute = df[df['prix_m2'] > seuil_haut]
df_aberrantes_basse = df[df['prix_m2'] < 1000]  # Prix anormalement bas
Sorties :

dvf_paris_2020-2025-exploitables-clean.csv (191K lignes - 86.2%)
dvf_paris_2020-2025-aberrantes-haute.csv (30K lignes - 13.8%)
dvf_paris_2020-2025-aberrantes-basse.csv (quelques centaines)
Statistiques finales (exploitables) :

Mediane prix/m² : 10,458 €
Moyenne prix/m² : 10,882 €
ecart-type : 5,747 €
Min : 1,000 € | Max : 36,846 €
etape 3 : Generation Tableaux Agreges
Script : algos/DVF/aggregation nettoyage preparation/tableau_prep.py

Sorties :

Fichier	Lignes	Description
dvfgeo_tableau_arrondissements.csv	20	Stats par arrondissement (prix moyen/median, nb transactions, surface moyenne, lat/lon)
dvfgeo_tableau_temporel.csv	120	evolution annee × arrondissement (2020-2025 × 20 arr)
dvfgeo_tableau_type_local.csv	~80	Stats par type de bien × arrondissement (Appartement, Maison, Local, Dependance)
dvfgeo_tableau_detail.csv	191K	Donnees complètes pour drill-down
etape 4 : Visualisations
Scripts :

algos/DVF/viz/viz matplotlib.py → Graphiques PNG
algos/DVF/viz/carte folium.py → Carte interactive HTML
Outputs :

plots/DVF/serie_temporelle.png - evolution prix/m² 2020-2025
plots/DVF/classement_arrondissements.png - Ranking prix moyen
plots/DVF/distribution_prix.png - Histogramme + box plot
plots/DVF/heatmap_type_arrondissement.png - Matrice prix par type
plots/DVF/carte_paris_heatmap.html - Carte interactive avec tooltips

## Pipeline IRCOM (Revenus Fiscaux)
### Nettoyage & Agregation
Script : algos/fiscal/IRCOM cleaner.py

Entree :

datas/fiscal/brut/2020.xlsx → 2023.xlsx (4 fichiers)
Source : DGFiP - IRCOM (Impôt sur le Revenu des Communes)
Traitement :


### Chargement multi-annees
for year in [2020, 2021, 2022, 2023]:
    df = pd.read_excel(f"datas/fiscal/brut/{year}.xlsx", skiprows=19)
    
    # Nettoyage
    df = df[
        df['dep'].notna() &
        ~df['libelle_commune'].str.contains('Total', na=False) &
        df['libelle_commune'].str.contains('Paris', case=False, na=False)
    ]
    
    # Extraction arrondissement
    df['arrondissement'] = df['code_commune'].str[-2:].astype(int)
    
    # Ajout annee
    df['annee'] = year
Sortie :

datas/fiscal/cleaned/ircom_2020-2023_paris_clean.csv (640 lignes)
Structure :

20 arrondissements × 8 tranches RFR × 4 annees = 640 lignes
Tranches RFR : 0-10k, 10-12k, 12-15k, 15-20k, 20-30k, 30-40k, 40-100k, >100k
etape 2 : Visualisations Fiscales
Script : algos/fiscal/viz.py

Outputs :

plots/fiscal/heatmap_rfr_arrondissements.html - Distribution foyers par tranche RFR
plots/fiscal/rfr_moyen_arrondissements.html - RFR moyen par arrondissement
plots/fiscal/evolution_rfr_temporelle.html - evolution 2020-2023
plots/fiscal/distribution_tranches_stacked.html - Repartition tranches (stacked bar)
plots/fiscal/ratio_inegalites_arrondissements.html - Ratio riches/pauvres

## Pipeline Annonces (Scraping)
### Scraping Multi-Sources
Scripts : algos/scrapped/scrapper/scrapp*.py

Sources :

Le Figaro Immobilier
Orpi
Century 21
Laforêt
Stephane Plaza Immobilier
Sorties brutes :

datas/scrapped/annonces_lefigaro_paris.csv
datas/scrapped/annonces_orpi_paris.csv
datas/scrapped/annonces_century21_paris.csv
datas/scrapped/annonces_laforet_paris.csv
datas/scrapped/annonces_stephane_plaza_paris.csv
etape 2 : Nettoyage & Fusion
Script : algos/scrapped/clean/annonces_cleaner.py

Traitement :

Fusion sources
df_merged = pd.concat([df_figaro, df_orpi, df_century21, df_laforet, df_plaza])

Nettoyage prix (extraction numerique)
df['prix'] = df['prix'].str.replace(r'[^\d]', '', regex=True).astype(float)

Nettoyage surface
df['surface'] = df['surface'].str.extract(r'(\d+)').astype(float)

Normalisation type
df['type'] = df['type'].str.lower().replace({
    'appart': 'Appartement',
    'maison': 'Maison',
    'studio': 'Appartement'
})

Extraction arrondissement depuis code postal
df['arrondissement'] = df['code_postal'].str[-2:].astype(int)

Calcul prix/m²
df['prix_m2'] = df['prix'] / df['surface']

Suppression doublons (même adresse + prix)
df = df.drop_duplicates(subset=['adresse', 'prix'])
Sortie :

datas/scrapped/annonces_paris_clean_final.csv

# Pipeline Analyses Croisees
Script : algos/viz_croisee/viz_croisee.py
Objectif : Croiser DVF (prix) et IRCOM (revenus) pour analyser l'accessibilite immobilière

Analyses produites :

Annees de RFR pour acheter un T2 (45m²)
python
Copy
# Calcul par arrondissement
prix_t2 = prix_m2_moyen * 45  # Surface T2 standard
annees_rfr = prix_t2 / rfr_moyen_par_foyer
Output : plots/viz_croisee/annees_rfr_pour_t2.html
Correlation RFR × Prix/m²
Scatter plot avec regression lineaire
Output : plots/viz_croisee/correlation_rfr_prix_m2.html
evolution comparative Prix vs RFR (2020-2023)
Animation temporelle (slider)
Indices base 100 en 2020
Output : plots/viz_croisee/evolution_interactive_prix_rfr.html
Heatmap evolution prix/m² 2020-2025
Pourcentage d'evolution par arrondissement
Output : plots/viz_croisee/heatmap_evolution_prix.html
Dashboard synthetique accessibilite
4 subplots : prix/m², RFR, annees T2, ratio prix/revenu
Output : plots/viz_croisee/dashboard_accessibilite.html

# Pipeline Machine Learning
## Pretraitement
Script : algos/DVF/ML/preprocessing.py

Feature Engineering :

Features temporelles
df['annee'] = pd.to_datetime(df['date_mutation']).dt.year
df['mois'] = pd.to_datetime(df['date_mutation']).dt.month

Features spatiales
df['arrondissement'] = df['code_commune'].str[-2:].astype(int)

## One-hot encoding type_local
df = pd.get_dummies(df, columns=['type_local'], prefix='type')

## Normalisation
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

Train/Test split (70/30)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
Sorties :

models/ml_train.csv (134K lignes)
models/ml_test.csv (57K lignes)
models/scaler.pkl
models/feature_names.pkl
## Entraînement Modèles
Script : algos/DVF/ML/prediction.py

Modèle 1 : Regression Lineaire (prediction prix/m²)

model = LinearRegression()
model.fit(X_train, y_train)

## evaluation
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)  # ~0.45
mae = mean_absolute_error(y_test, y_pred)  # ~3,500 €/m²
Modèle 2 : Regression Logistique (classification cher/pas cher)

Creation target binaire (seuil = mediane)
y_class = (y > y.median()).astype(int)

model = LogisticRegression()
model.fit(X_train, y_class_train)

## evaluation
accuracy = accuracy_score(y_class_test, y_pred)  # ~72%
roc_auc = roc_auc_score(y_class_test, y_proba)  # ~0.78
Sorties :

models/model_linear_regression.pkl
models/model_logistic_regression.pkl
models/resultats_ml.txt (metriques)
plots/models/regression_lineaire.png (scatter pred vs reel)
plots/models/regression_logistique.png (matrice confusion)

# Utilisation des Modèles ML

## Charger le predictor
predictor = get_predictor()

## Estimer un bien
result = predictor.estimate_complet(
    surface=65,
    arrondissement=11,
    type_local='Appartement',
    nombre_pieces=3,
    annee=2025,
    mois=6
)

print(result)
{
    'prix_m2_estime': 11175.50,
    'prix_total_estime': 726375.00,
    'prix_m2_min': 8940.40,
    'prix_m2_max': 13410.60,
    'classification': 'Bon marche',
    'probabilite_cher': 0.325,
    'probabilite_bon_marche': 0.675,
    'confiance': 67.5
}
Dashboard Streamlit

Navigue vers l'onglet Prediction ML et remplis le formulaire.

# Statistiques Cles
DVF (Ventes 2020-2025)  
Metrique	Valeur  
Lignes exploitables	191,193 
Prix/m² median	10,458 €    
Prix/m² moyen	10,882 €    
ecart-type	5,747 € 
Arrondissement le plus cher	6e (14,997 €/m²)    
Arrondissement le moins cher	19e (8,800 €/m²)    
Periode	2020-2025   
IRCOM (Revenus 2020-2023)   
Metrique	Valeur  
Lignes	640 (20 arr × 8 tranches × 4 ans)   
RFR moyen Paris	~35,000 €/foyer 
Arrondissement RFR le plus eleve	7e (~55,000 €)  
Arrondissement RFR le plus bas	19e (~22,000 €)     
Tranches RFR	8 (0-10k → >100k)   

## Modèles ML
Modèle	Metrique	Score   
Regression Lineaire	R²	0.45    
MAE	3,500 €/m²  
Regression Logistique	Accuracy	72% 
ROC-AUC	0.78    

## Ordre d'Execution Recommande
### 1. DVF : Agregation brute
python "algos/DVF/aggregation nettoyage preparation/agregateur primaire.py"

### 2. DVF : Nettoyage et detection outliers
python "algos/DVF/aggregation nettoyage preparation/clean.py"

### 3. DVF : Generation tableaux agreges
python "algos/DVF/aggregation nettoyage preparation/tableau_prep.py"

### 4. DVF : Visualisations matplotlib
python "algos/DVF/viz/viz matplotlib.py"

### 5. DVF : Carte interactive
python "algos/DVF/viz/carte folium.py"

### 6. IRCOM : Nettoyage donnees fiscales
python "algos/fiscal/IRCOM cleaner.py"

### 7. IRCOM : Visualisations
python "algos/fiscal/viz.py"

### 8. Annonces : Nettoyage et fusion
python "algos/scrapped/clean/annonces_cleaner.py"

### 9. Analyses croisees DVF × IRCOM
python "algos/viz_croisee/viz_croisee.py"

### 10. ML : Pretraitement
python "algos/DVF/ML/preprocessing.py"

### 11. ML : Entraînement modèles
python "algos/DVF/ML/prediction.py"

### 12. Lancer dashboard
streamlit run src/dashboard/app.py


# Documentation
Dictionnaire de donnees - Schemas detailles des datasets    
Architecture technique - Details implementation 
# Sources de Donnees    
DVF Geocodees : data.gouv.fr    
IRCOM : DGFiP (Direction Generale des Finances Publiques)   
Annonces : Scraping multi-sites (Le Figaro, Orpi, Century 21, Laforêt, Stephane Plaza)  

# Limitations 
Les données DVF ne contiennent pas d'informations sur état du bien, DPE, étage, exposition etc ce qui influe fortement sur le prix, d'où MAE élevée     
Donnees IRCOM 2020-2023 : Pas encore de donnees 2024 ni 2025 disponibles    
On ne dispose que de données de ventes, pas de bails de location. Il est impossible d'extrapoler les prix de vente pour obtenir les loyers en raison de l'encadrement de loyers et de l'importance du parc HLM ou autres loyers réglementés(loi Pinem et connsortes)    

GitHub : @Louloucoco2l  
Projet : AgregationDonnees
