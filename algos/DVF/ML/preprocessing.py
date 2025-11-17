"""
    Preprocessing des donnees DVFGeo pour ML
    - Feature engineering
    - Normalisation
    - Train/Test split
    - Sauvegarde pour modeles
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import pickle

INPUT_PATH = "../../../datas/downloaded/geocodes/cleaned/dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_DIR = "../../../datas/downloaded/geocodes/ml/"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data(filepath):
    """Charge les donnees"""
    print("Chargement: " + os.path.basename(filepath))
    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversion numérique
    df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'], errors='coerce')
    df['surface_reelle_bati'] = pd.to_numeric(df['surface_reelle_bati'], errors='coerce')
    df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
    df['nombre_pieces_principales'] = pd.to_numeric(df['nombre_pieces_principales'], errors='coerce')

    # Surface composite
    df['surface'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: row['valeur_fonciere'] / row['surface']
        if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface']) and row['surface'] > 0
        else None,
        axis=1
    )

    # Arrondissement
    df['arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)

    # Date
    df['date_mutation'] = pd.to_datetime(df['date_mutation'], errors='coerce')
    df['annee'] = df['date_mutation'].dt.year
    df['mois'] = df['date_mutation'].dt.month

    print("OK - {} lignes\n".format(len(df)))
    return df


def feature_engineering(df):
    """Crée features pertinentes"""
    print("Feature engineering...")

    df_fe = df.copy()

    # Features numeriques
    df_fe['log_surface'] = np.log1p(df_fe['surface'])
    df_fe['log_valeur'] = np.log1p(df_fe['valeur_fonciere'])

    # Features temporelles
    df_fe['annee_norm'] = (df_fe['annee'] - df_fe['annee'].min()) / (df_fe['annee'].max() - df_fe['annee'].min())
    df_fe['mois_sin'] = np.sin(2 * np.pi * df_fe['mois'] / 12)
    df_fe['mois_cos'] = np.cos(2 * np.pi * df_fe['mois'] / 12)

    # Features spatiales
    df_fe['arrond_norm'] = (df_fe['arrondissement'] - 1) / 19

    # Nombre de pieces (fillna avec mediane)
    df_fe['nombre_pieces'] = df_fe['nombre_pieces_principales'].fillna(df_fe['nombre_pieces_principales'].median())

    # Nature mutation (one-hot encoding)
    nature_dummies = pd.get_dummies(df_fe['nature_mutation'].fillna('Unknown'), prefix='nature')
    df_fe = pd.concat([df_fe, nature_dummies], axis=1)

    # Type local (one-hot encoding)
    type_dummies = pd.get_dummies(df_fe['type_local'].fillna('Unknown'), prefix='type')
    df_fe = pd.concat([df_fe, type_dummies], axis=1)

    print("OK - {} features creees\n".format(len(df_fe.columns)))

    return df_fe


def prepare_ml_data(df_fe):
    """Prépare données pour ML"""
    print("Preparation donnees ML...")

    # EXCLUSION explicite des colonnes originales (non-encodees)
    exclude_cols = {'nature_mutation', 'type_local', 'nature_culture', 'nature_culture_speciale'}

    # Ajouter colonnes one-hot encodees (nature_* et type_* SAUF les originales)
    feature_cols = []
    feature_cols += [col for col in df_fe.columns
                     if col.startswith('nature_') and col not in exclude_cols]
    feature_cols += [col for col in df_fe.columns
                     if col.startswith('type_') and col not in exclude_cols]

    # Ajouter features numeriques
    numeric_features = ['log_surface', 'log_valeur', 'annee_norm', 'mois_sin', 'mois_cos', 'arrond_norm', 'nombre_pieces']
    feature_cols += numeric_features

    print("DEBUG: Colonnes selectionnees:")
    print(feature_cols)
    print()

    # Cible
    X = df_fe[feature_cols].copy()
    y = df_fe['prix_m2'].copy()

    print("DEBUG - Avant suppression NaN: {} lignes".format(len(X)))
    print("DEBUG - X contient NaN: {}".format(X.isna().sum().sum()))
    print("DEBUG - y contient NaN: {}".format(y.isna().sum()))
    print()

    # Supprimer NaN - moins strict
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask]
    y = y[mask]

    print("OK - {} lignes conservees\n".format(len(X)))
    print("Features utilisees: {}".format(len(feature_cols)))
    print()

    return X, y, feature_cols


def train_test_split_data(X, y):
    """Sépare train/test avec stratification"""
    print("Train/Test split (70/30)...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42
    )

    print("OK")
    print("Train: {} samples".format(len(X_train)))
    print("Test: {} samples\n".format(len(X_test)))

    return X_train, X_test, y_train, y_test


def normalize_data(X_train, X_test):
    """Normalise les features"""
    print("Normalisation (StandardScaler)...")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("OK\n")

    return X_train_scaled, X_test_scaled, scaler


def export_data(X_train, X_test, y_train, y_test, scaler, feature_cols):
    """Exporte données et scaler"""
    print("=" * 70)
    print("Export donnees ML")
    print("=" * 70 + "\n")

    # Export train
    train_data = pd.DataFrame(X_train, columns=feature_cols)
    train_data['prix_m2'] = y_train.values
    train_data.to_csv(os.path.join(OUTPUT_DIR, 'ml_train.csv'), sep=';', index=False)
    print("ml_train.csv: {} lignes".format(len(train_data)))

    # Export test
    test_data = pd.DataFrame(X_test, columns=feature_cols)
    test_data['prix_m2'] = y_test.values
    test_data.to_csv(os.path.join(OUTPUT_DIR, 'ml_test.csv'), sep=';', index=False)
    print("ml_test.csv: {} lignes".format(len(test_data)))

    # Export scaler
    with open(os.path.join(OUTPUT_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    print("scaler.pkl: sauvegarde du normaliseur")

    # Export feature names
    with open(os.path.join(OUTPUT_DIR, 'feature_names.pkl'), 'wb') as f:
        pickle.dump(feature_cols, f)
    print("feature_names.pkl: noms des features\n")


def main():
    if not os.path.isfile(INPUT_PATH):
        print("Erreur: {} non trouvé".format(INPUT_PATH))
        return

    print("=" * 70)
    print("PREPROCESSING ML - DVFGeo")
    print("=" * 70 + "\n")

    # Charger données
    df = load_data(INPUT_PATH)

    # Feature engineering
    df_fe = feature_engineering(df)

    # Préparer données ML
    X, y, feature_cols = prepare_ml_data(df_fe)

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split_data(X, y)

    # Normaliser
    X_train_scaled, X_test_scaled, scaler = normalize_data(X_train, X_test)

    # Export
    export_data(X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols)

    print("=" * 70)
    print("PREPROCESSING COMPLETE")
    print("=" * 70)
    print("\nFichiers generes dans: {}".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()