# AgregationDonnees

Analyse et modélisation du marché immobilier parisien à partir des données DVF géocodées (data.gouv.fr).

Ce projet agrège les données de ventes effectuées, les nettoie, les analyse, et entraîne des modèles ML pour estimer les prix immobiliers.

## Architecture générale

```
DVF brutes (data.gouv.fr)
    ↓
[1] Scrapping d'annonces
    ↓
[2] Exploitation ventes effectuées
    ├─ Agrégation & nettoyage
    ├─ Visualisations
    └─ Modèles ML
    ↓
[3] API de prédiction pour annonces
```

---

## 1. Scrapping d'annonces

À compléter.

---

## 2. Exploitation ventes effectuées

### 2.1 Agrégation et bornage sur Paris

**Objectif:** Fusionner les fichiers DVF par année et département, filtrer sur Paris, séparer exploitable/inexploitable.

**Fichiers source:** `datas/downloaded/geocodes/2020_75.csv` → `2025_75.csv`

**Scripts:**
- `algos/DVF/agregateur_primaire.py` - Fusionne les DVF brutes, filtre Paris
- `algos/DVF/clean.py` - Nettoie, calcule prix_m2, détecte aberrantes hautes

**Résumé traitement:**
```
DVF brutes (419K lignes)
    ↓ Filtre Paris (code_commune 75XXX)
Données Paris (221K lignes)
    ↓ Sépare par qualité
├─ Exploitables: 191K lignes (valeur + surface + coordonnées)
└─ Aberrantes hautes: 30K lignes (outliers > 36,846€/m²)
```

**Sorties:**
- `dvfgeo_paris_2020-2025-exploitables-clean.csv` - Données nettoyées (191K lignes)
- `dvfgeo_paris_2020-2025-aberrantes-haute.csv` - Outliers détectés (30K lignes)

### 2.2 Création exports CSV complémentaires

**Objectif:** Générer des CSVs agrégés pour visualisations et ML.

**Script:** `algos/visualisations/tableau_prep.py`

**Sorties:**
- `dvfgeo_tableau_arrondissements.csv` (20 lignes) - Agrégation par arrondissement
- `dvfgeo_tableau_temporel.csv` (120 lignes) - Agrégation année × arrondissement
- `dvfgeo_tableau_type_local.csv` (~80 lignes) - Agrégation type × arrondissement
- `dvfgeo_tableau_detail.csv` (191K lignes) - Données complètes pour drill-down

### 2.3 Visualisation matplotlib

**Objectif:** Générer graphiques PNG pour analyses rapides.

**Script:** `algos/visualisations/dvfgeo_visualisations.py`

**Graphiques produits:**
- `serie_temporelle.png` - Evolution prix/m² par arrondissement (2020-2025)
- `classement_arrondissements.png` - Ranking prix moyen
- `distribution_prix.png` - Histogramme et box plot
- `heatmap_type_arrondissement.png` - Matrice prix par type × arrondissement
- `volume_transactions.png` - Nombre de ventes par arrondissement

### 2.4 Visualisation HTML Folium

**Objectif:** Carte interactive avec heatmap des arrondissements.

**Script:** `algos/visualisations/dvfgeo_carte_folium.py`

**Sortie:** `carte_paris_heatmap.html` (ouverture navigateur)

**Contenu:**
- 20 cercles colorés (un par arrondissement)
- Couleur = prix_m2 (vert bas prix → rouge haut prix)
- Tooltips interactifs avec stats détaillées
- Légende et contrôles

### 2.5 Prétraitement et régressions

**Objectif:** Préparer données pour ML, entraîner régression linéaire et logistique.

**Scripts:**
- `algos/ml/dvfgeo_ml_preprocessing.py` - Feature engineering, normalisation, train/test split
- `algos/ml/dvfgeo_ml_models.py` - Entraînement modèles et évaluations

**Étapes:**

#### Prétraitement
- Feature engineering (log transformations, normalisation temporelle/spatiale, one-hot encoding)
- Standardisation (StandardScaler)
- Train/Test split (70/30)

**Sorties:**
- `ml_train.csv` - Données train (134K lignes)
- `ml_test.csv` - Données test (57K lignes)
- `scaler.pkl` - Normaliseur (chargé lors prédictions)
- `feature_names.pkl` - Noms features

#### Régression linéaire
**Objectif:** Prédire prix_m2

**Résultats (test):**
- R² ~0.40-0.50 (40-50% variance expliquée)
- MAE ~3000-4000€/m² (erreur moyenne)

**Sortie:** `model_linear_regression.pkl`

#### Régression logistique
**Objectif:** Classer bien comme "cher" ou "bon marché" (seuil = médiane prix_m2)

**Résultats (test):**
- Accuracy ~70-75%
- ROC-AUC ~0.75-0.80

**Sortie:** `model_logistic_regression.pkl`

**Visualisations:**
- `regression_lineaire.png` - Scatter pred vs réel
- `regression_logistique.png` - Matrice confusion, distribution probabilités

---

## 3. Utilisation prédiction pour estimation prix

### Installation

```bash
pip install scikit-learn pandas numpy folium matplotlib seaborn
```

### Utilisation API

```python
from algos.ml.prediction_api import PredictionAPI

# Initialiser
api = PredictionAPI()

# Estimer une annonce
estimation = api.estimate_annonce(
    surface=65,
    arrondissement=11,
    type_local='Appartement',
    nombre_pieces=2,
    annee=2025,
    mois=1
)

print(estimation)
# {
#     'prix_m2_estime': 11175,
#     'prix_total_estime': 726375,
#     'prix_min': 616919,
#     'prix_max': 835831,
#     'classification': 'Bon marche',
#     'confiance_classification': 72.5,
#     'details': {...}
# }
```

### Intégration scraper

```python
from algos.ml.scraper_integration import ScraperIntegration

scraper_api = ScraperIntegration()

annonce = {
    'titre': 'Appartement 2P lumineux',
    'surface': 65,
    'adresse': '123 rue Mouffetard, 75005 Paris',
    'type': 'Appartement',
    'pieces': 2,
    'prix_annonce': 650000,
    'url': 'https://example.com/annonce1'
}

result = scraper_api.scrape_et_estimer(annonce)

# Export CSV
scraper_api.export_resultats('annonces_estimees.csv')
```

---

## Ordre d'exécution recommandé

```bash
# 1. Agrégation brute
python algos/old_dataset/agregateur_primaire.py

# 2. Nettoyage et détection outliers
python algos/old_dataset/clean.py

# 3. Analysis exploratoire
python algos/old_dataset/brouillon.py

# 4. Preparation CSV pour visualisations
python algos/visualisations/tableau_prep.py

# 5. Visualisations matplotlib
python algos/visualisations/dvfgeo_visualisations.py

# 6. Carte interactive
python algos/visualisations/dvfgeo_carte_folium.py

# 7. Prétraitement ML
python algos/ml/dvfgeo_ml_preprocessing.py

# 8. Entraînement modèles
python algos/ml/dvfgeo_ml_models.py

# 9. Utiliser API prédiction
python algos/ml/prediction_api.py
```

---

## Structure répertoires

```
AgregationDonnees/
├── datas/
│   ├── downloaded/
│   │   ├── geocodes/           # DVF brutes (2020_75.csv - 2025_75.csv)
│   │   └── cleaned/            # DVF nettoyées
│   ├── tableau/                # CSVs pour visualisations
│   ├── ml/                     # Données ML + modèles
│   │   ├── ml_train.csv
│   │   ├── ml_test.csv
│   │   ├── scaler.pkl
│   │   ├── feature_names.pkl
│   │   └── results/            # Modèles + graphiques
│   └── visualizations/         # PNG + HTML cartes
│
├── algos/
│   ├── DVF/
│   │   ├── agregateur_primaire.py
│   │   ├── clean.py
│   │   └── brouillon.py
│   ├── visualisations/
│   │   ├── tableau_prep.py
│   │   ├── dvfgeo_visualisations.py
│   │   └── dvfgeo_carte_folium.py
│   └── ml/
│       ├── dvfgeo_ml_preprocessing.py
│       ├── dvfgeo_ml_models.py
│       ├── prediction_api.py
│       └── scraper_integration.py
│
└── README.md
```

---

## Méthodologie nettoyage

**Filtres appliqués:**
- Localisation: code_commune commence par 75 ET nom_commune contient "PARIS"
- Qualité: valeur_fonciere > 0 ET surface > 0 ET coordonnées GPS valides
- Aberrantes: détection IQR strict (Q3 + 3×IQR) pour hautes valeurs uniquement
  - Seuil final: 36,846€/m² (prend max des méthodes IQR et MAD)
  - Supprime vrais outliers (ex: 95M€/m² sur 8m²), conserve biens chers légitimes

**Résultat:**
- 191K lignes exploitables (86.2%)
- 30K aberrantes supprimées (13.8%)
- Distribution prix finale cohérente (médiane 10,500€/m², écart-type 5,747€/m²)

---

## Notes

- Données DVF source: https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees
- Modèles ML: régression linéaire pour estimation prix, logistique pour classification
- API prédiction: charge modèles pre-entraînés, normalise features, retourne estimation + intervalle confiance
- Limitations: R² ~0.40-0.50 (marché immobilier très volatile, features limitées)