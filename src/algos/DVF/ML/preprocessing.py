import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
from src.config import paths

INPUT_PATH = paths.data.DVF.geocodes.cleaned/"dvf_paris_2020-2025-exploitables-clean.csv"
OUTPUT_DIR = paths.models.path

def load_data(filepath):
    print(f"Chargement: {filepath.name}")
    df = pd.read_csv(filepath, sep=';', dtype=str, low_memory=False)

    # Conversions numériques
    cols_num = ['valeur_fonciere', 'surface_reelle_bati', 'surface_terrain',
                'nombre_pieces_principales', 'latitude', 'longitude']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Surface composite
    df['surface_m2_retenue'] = df['surface_reelle_bati'].fillna(df['surface_terrain'])

    # Prix au m²
    df['prix_m2'] = df.apply(
        lambda row: row['valeur_fonciere'] / row['surface_m2_retenue']
        if pd.notna(row['valeur_fonciere']) and pd.notna(row['surface_m2_retenue']) and row['surface_m2_retenue'] > 0
        else None,
        axis=1
    )

    # Arrondissement & Date
    df['code_arrondissement'] = df['code_commune'].astype(str).str[-2:].astype(int)
    df['date_mutation'] = pd.to_datetime(df['date_mutation'], errors='coerce')
    df['annee'] = df['date_mutation'].dt.year
    df['mois'] = df['date_mutation'].dt.month

    return df


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points GPS"""
    R = 6371  # Rayon terre en km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def feature_engineering(df):
    print("Feature engineering...")
    df_fe = df.copy()
    df_fe['log_surface_m2'] = np.log1p(df_fe['surface_m2_retenue'])
    df_fe['dist_center'] = haversine_distance(df_fe['latitude'], df_fe['longitude'], 48.853, 2.3499)
    df_fe['annee_norm'] = (df_fe['annee'] - 2020) / 5.0

    df_fe['nb_pieces_fill'] = df_fe['nombre_pieces_principales'].fillna(df_fe['nombre_pieces_principales'].median())
    #pour les pieces: on remplit les NaN avec la mediane (plutot que la moyenne) pour eviter les outliers

    arrond_dummies = pd.get_dummies(df_fe['code_arrondissement'], prefix='arrond')
    df_fe = pd.concat([df_fe, arrond_dummies], axis=1)

    #on arrete le one-Hot sur 'type_local' car 100% Appartement, on supprime aussi mois

    return df_fe


def prepare_ml_data(df_fe):
    print("Selection des features...")

    feature_cols = []

    #dummies Arrondissements
    feature_cols += [c for c in df_fe.columns if c.startswith('arrond_')]

    #features Numériques (Sans mois, Sans type)
    numeric_features = [
        'log_surface_m2',
        'dist_center',
        'annee_norm',
        'nb_pieces_fill',
        'latitude', 'longitude'
    ]
    feature_cols += numeric_features

    X = df_fe[feature_cols].copy()
    y = df_fe['prix_m2'].copy()

    mask = X.notna().all(axis=1) & y.notna()
    return X[mask], y[mask], feature_cols


def main():
    print("PREPROCESSING (appartements uniquement - sans mois - avec dist)")
    df = pd.read_csv(INPUT_PATH, sep=';')

    # Re-typage rapide si jamais
    cols = ['latitude', 'longitude', 'surface_m2_retenue', 'nombre_pieces_principales', 'prix_m2']
    for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce')

    df_fe = feature_engineering(df)
    X, y, feature_cols = prepare_ml_data(df_fe)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    #exports
    pd.DataFrame(X_train_scaled, columns=feature_cols).assign(prix_m2=y_train.values).to_csv(
        OUTPUT_DIR / 'ml_train.csv', sep=';', index=False)
    pd.DataFrame(X_test_scaled, columns=feature_cols).assign(prix_m2=y_test.values).to_csv(OUTPUT_DIR / 'ml_test.csv', sep=';', index=False)

    with open(OUTPUT_DIR / 'scaler.pkl', 'wb') as f: pickle.dump(scaler, f)
    with open(OUTPUT_DIR / 'feature_names.pkl', 'wb') as f: pickle.dump(feature_cols, f)


if __name__ == "__main__":
    main()