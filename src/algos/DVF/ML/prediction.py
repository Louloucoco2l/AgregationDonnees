"""
    Entrainement modeles ML pour prediction prix immobiliers (VERSION OPTIMISÉE)
    - Modele Principal : Histogram Gradient Boosting (remplace la Reg Linéaire/Random Forest)
    - Classification : Regression Logistique (Classification cher/bon marche)
    - Evaluation et visualisations
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from src.config import paths

ML_DIR = paths.models.path
OUTPUT_DIR = paths.models.path


def load_data():
    """Charge les données préparées par preprocessing.py"""
    print("Chargement donnees ML...")

    try:
        X_train = pd.read_csv(ML_DIR / 'ml_train.csv', sep=';')
        X_test = pd.read_csv(ML_DIR / 'ml_test.csv', sep=';')
    except FileNotFoundError:
        print("ERREUR: Fichiers ml_train.csv ou ml_test.csv introuvables.")
        print("Veuillez lancer preprocessing.py d'abord.")
        exit(1)

    y_train = X_train['prix_m2'].values
    y_test = X_test['prix_m2'].values

    # Suppression de la cible dans les features
    X_train = X_train.drop('prix_m2', axis=1)
    X_test = X_test.drop('prix_m2', axis=1)

    # Récupération des noms de colonnes pour l'interprétabilité
    feature_names = X_train.columns.tolist()

    print("OK - {} samples train, {} samples test".format(len(X_train), len(X_test)))
    print(f"Features ({len(feature_names)}): {feature_names}\n")

    return X_train, X_test, y_train, y_test, feature_names


def train_model_principal(X_train, X_test, y_train, y_test, feature_names):
    """
    Entraîne un modèle Gradient Boosting (HGBR).
    Plus robuste aux outliers et capable de capturer les non-linéarités complexes.
    """
    print("MODELE PRINCIPAL (HistGradientBoosting) - Prediction Prix/m²")

    print("Entrainement en cours")

    #boite noire un peu
    model = HistGradientBoostingRegressor(
        max_iter=1000,
        learning_rate=0.05,  #vitesse modérée pour la stabilité
        max_leaf_nodes=63,  # Compromis 31 trop simple, 127 trop complexe
        max_depth=None,
        min_samples_leaf=20,  #plus de points necessaires pour valider un prix
        l2_regularization=0.5,  #un peu de frein pour éviter le par-cœur
        early_stopping=True,
        random_state=42,
        verbose=0
    )

    model.fit(X_train, y_train)
    print("OK\n")

    #prédictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    #métriques
    r2_train = r2_score(y_train, y_train_pred)
    r2_test = r2_score(y_test, y_test_pred)
    mae_test = mean_absolute_error(y_test, y_test_pred)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))

    print("RESULTATS BOOSTING")
    print(f"\nTrain R²: {r2_train:.4f}")
    print(f"Test  R²: {r2_test:.4f}")
    print(f"Test MAE: {mae_test:.2f}€/m²")
    print(f"Test RMSE: {rmse_test:.2f}€/m²")

    # HGBR n'a pas de .feature_importances_ direct fiable, on utilise la permutation
    print("\nCalcul de l'importance des features (Permutation)...")
    result = permutation_importance(
        model, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1
    )

    importances = pd.DataFrame({
        'feature': feature_names,
        'importance': result.importances_mean,
        'std': result.importances_std
    }).sort_values('importance', ascending=False).head(15)

    #creer le texte pour l export txt
    importance_text = "\nTOP 15 FEATURES IMPORTATNTES :\n"
    print(importance_text)
    for idx, row in importances.iterrows():
        line = f"  {row['feature']:<25}: {row['importance']:.4f} (±{row['std']:.4f})"
        print(line)
        importance_text += line + "\n"

    #Visualisation
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    #plot Train
    axes[0].scatter(y_train, y_train_pred, alpha=0.1, s=2, color='#3498db', label='Train')
    axes[0].plot([y_train.min(), y_train.max()], [y_train.min(), y_train.max()], 'r--', lw=2, label='Idéal')
    axes[0].set_xlabel('Prix Réel (€/m²)')
    axes[0].set_ylabel('Prix Prédit (€/m²)')
    axes[0].set_title(f'Train - R²: {r2_train:.3f}')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    #plot Test
    axes[1].scatter(y_test, y_test_pred, alpha=0.15, s=3, color='#e67e22', label='Test')
    axes[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Idéal')
    axes[1].set_xlabel('Prix Réel (€/m²)')
    axes[1].set_ylabel('Prix Prédit (€/m²)')
    axes[1].set_title(f'Test - R²: {r2_test:.3f} | MAE: {mae_test:.0f}€')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regression_lineaire.png', dpi=150) # On garde le nom générique pour l'affichage
    plt.close()

    #sauvegarde sous le nom 'model_linear_regression.pkl' pour que le dashboard actuel fonctionne sans modification, même si c'est plus le bon nom
    with open(OUTPUT_DIR / 'model_linear_regression.pkl', 'wb') as f:
        pickle.dump(model, f)
        print("\nModèle sauvegardé sous 'model_linear_regression.pkl'")

    return model, r2_test, mae_test, importance_text


def logistic_regression(X_train, X_test, y_train, y_test, feature_names):
    """Regression logistique pour classification cher/bon marche"""
    print("\nREGRESSION LOGISTIQUE - Classification Cher/Bon marche")

    # Créer target binaire (médiane comme seuil)
    seuil = np.median(y_train)
    y_train_binary = (y_train > seuil).astype(int)
    y_test_binary = (y_test > seuil).astype(int)

    print(f"Seuil de classification: {seuil:.0f}€/m²")
    print(f"Classe 0 (bon marche): < {seuil:.0f}€/m²")
    print(f"Classe 1 (cher): >= {seuil:.0f}€/m²")

    print("Entrainement...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train_binary)
    print("OK\n")

    # Predictions
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]

    # Métriques
    acc_test = accuracy_score(y_test_binary, y_test_pred)
    roc_auc = roc_auc_score(y_test_binary, y_test_proba)

    print("RESULTATS CLASSIFICATION")
    print(f"Accuracy Test: {acc_test:.4f}")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"F1-Score: {f1_score(y_test_binary, y_test_pred):.4f}")

    # Matrice de confusion
    cm = confusion_matrix(y_test_binary, y_test_pred)

    # Visualisation
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
                xticklabels=['Bon marche', 'Cher'], yticklabels=['Bon marche', 'Cher'])
    axes[0].set_title('Matrice de confusion')

    axes[1].hist(y_test_proba[y_test_binary == 0], bins=30, alpha=0.6, label='Réel: Bon marche')
    axes[1].hist(y_test_proba[y_test_binary == 1], bins=30, alpha=0.6, label='Réel: Cher')
    axes[1].set_xlabel('Probabilité prédite "Cher"')
    axes[1].legend()
    axes[1].set_title('Distribution des probabilités')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regression_logistique.png', dpi=150)
    plt.close()

    # Sauvegarde
    with open(OUTPUT_DIR / 'model_logistic_regression.pkl', 'wb') as f:
        pickle.dump(model, f)

    return model, acc_test, roc_auc


def export_results(r2, mae, acc, roc_auc, importance_text=""):
    """Exporte résumé résultats"""
    print("\nEXPORT RESULTATS")

    with open(OUTPUT_DIR / 'resultats_ml.txt', 'w', encoding='utf-8') as f:
        f.write("RESULTATS MODELES ML - DVFGeo (Gradient Boosting)\n")
        f.write("===============================================\n\n")

        f.write("ESTIMATION PRIX (HistGradientBoostingRegressor)\n")
        f.write(f"R² Test: {r2:.4f}\n")
        f.write(f"MAE Test: {mae:.2f}€/m²\n")

        f.write(importance_text)
        f.write("\n")

        f.write("CLASSIFICATION (LogisticRegression)\n")
        f.write(f"Accuracy Test: {acc:.4f}\n")
        f.write(f"ROC-AUC: {roc_auc:.4f}\n")

    print(f"Sauvegardé dans {OUTPUT_DIR / 'resultats_ml.txt'}")


def main():
    print("ENTRAINEMENT MODELES ML DVFGeo")

    X_train, X_test, y_train, y_test, feature_names = load_data()

    model_boost, r2_val, mae_val, importance_text = train_model_principal(X_train, X_test, y_train, y_test, feature_names)

    model_log, acc_val, roc_val = logistic_regression(
        X_train, X_test, y_train, y_test, feature_names
    )

    export_results(r2_val, mae_val, acc_val, roc_val, importance_text)

    print("\nfini d attendre")


if __name__ == "__main__":
    main()

