"""
    Entrainement modeles ML pour prediction prix immobiliers
    - Regression lineaire (prediction prix_m2)
    - Regression logistique (classification cher/bon marche)
    - Evaluation et visualisations
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import seaborn as sns
from src.config import paths
from sklearn.ensemble import RandomForestRegressor

ML_DIR = paths.models.path
OUTPUT_DIR = paths.models.path



def load_data():
    """Charge donnees preparees"""
    print("Chargement donnees ML...")

    X_train = pd.read_csv(ML_DIR/ 'ml_train.csv', sep=';')
    X_test = pd.read_csv(ML_DIR/ 'ml_test.csv', sep=';')

    y_train = X_train['prix_m2'].values
    y_test = X_test['prix_m2'].values

    X_train = X_train.drop('prix_m2', axis=1).values
    X_test = X_test.drop('prix_m2', axis=1).values

    with open(ML_DIR/ 'feature_names.pkl', 'rb') as f:
        feature_names = pickle.load(f)

    print("OK - {} samples train, {} samples test\n".format(len(X_train), len(X_test)))

    return X_train, X_test, y_train, y_test, feature_names


def train_model_principal(X_train, X_test, y_train, y_test, feature_names):
    """Random Forest pour prediction prix_m2 (Remplace la Reg Linéaire)"""
    print("RANDOM FOREST - Prediction Prix/m²")

    print("Entrainement ")
    # n_estimators=100 : nombre d'arbres
    # n_jobs=-1 : utilise tous les processeurs
    # max_depth=15 : limite la profondeur pour éviter le sur-apprentissage (overfitting)
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=20,  # On remonte de 12 à 20 (le modèle peut apprendre plus de nuances)
        min_samples_split=10,  # On descend de 15 à 10
        min_samples_leaf=3,  # On descend de 5 à 3 (on accepte des groupes un peu plus petits)
        max_features='sqrt',  # 'sqrt' est souvent meilleur que 0.5 pour la diversité
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("OK\n")

    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # Métriques train
    r2_train = r2_score(y_train, y_train_pred)
    mae_train = mean_absolute_error(y_train, y_train_pred)
    rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))

    # Métriques test
    r2_test = r2_score(y_test, y_test_pred)
    mae_test = mean_absolute_error(y_test, y_test_pred)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))

    print("RESULTATS RANDOM FOREST")
    print("\nTrain:")
    print("  R²: {:.4f}".format(r2_train))
    print("  MAE: {:.2f}€/m²".format(mae_train))

    print("\nTest:")
    print("  R²: {:.4f}".format(r2_test))
    print("  MAE: {:.2f}€/m²".format(mae_test))
    print("  RMSE: {:.2f}€/m²".format(rmse_test))

    # Top features (Spécifique Random Forest)
    print("\nImportance des features:")
    importances = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False).head(10)

    for idx, row in importances.iterrows():
        print("  {}: {:.4f}".format(row['feature'], row['importance']))

    # Visualisation (Graphique Scatter)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Scatter plot train (avec échantillonnage pour lisibilité si gros dataset)
    axes[0].scatter(y_train, y_train_pred, alpha=0.3, s=5, label='Train')
    axes[0].plot([y_train.min(), y_train.max()], [y_train.min(), y_train.max()], 'r--', lw=2)
    axes[0].set_title(f'Train - R²: {r2_train:.4f}')

    # Scatter plot test
    axes[1].scatter(y_test, y_test_pred, alpha=0.3, s=5, color='orange', label='Test')
    axes[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    axes[1].set_title(f'Test - R²: {r2_test:.4f}')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regression_rf.png', dpi=150)  # Nouveau nom de fichier
    plt.close()

    # Sauvegarde modele (Attention au nom de fichier, il faut update le predictor aussi)
    # Pour ne pas casser le predictor tout de suite, on peut le sauver sous le nom "linear"
    # OU mieux : mettre à jour le predictor.
    # Ici je garde le nom "linear" pour que votre IHM continue de marcher sans modif code,
    # MAIS c'est techniquement un Random Forest maintenant.
    with open(OUTPUT_DIR / 'model_linear_regression.pkl', 'wb') as f:
        pickle.dump(model, f)

    return model, r2_test, mae_test

# def linear_regression(X_train, X_test, y_train, y_test, feature_names):
#     """Regression lineaire pour prediction prix_m2"""
#     print("REGRESSION LINEAIRE - Prediction Prix/m²")
#
#     print("Entrainement")
#     model = LinearRegression()
#     model.fit(X_train, y_train)
#     print("OK\n")
#
#     # Predictions
#     y_train_pred = model.predict(X_train)
#     y_test_pred = model.predict(X_test)
#
#     # Métriques train
#     r2_train = r2_score(y_train, y_train_pred)
#     mae_train = mean_absolute_error(y_train, y_train_pred)
#     rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))
#
#     # Métriques test
#     r2_test = r2_score(y_test, y_test_pred)
#     mae_test = mean_absolute_error(y_test, y_test_pred)
#     rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
#
#     print("RESULTATS REGRESSION LINEAIRE")
#     print("\nTrain:")
#     print("  R²: {:.4f}".format(r2_train))
#     print("  MAE: {:.2f}€/m²".format(mae_train))
#     print("  RMSE: {:.2f}€/m²".format(rmse_train))
#
#     print("\nTest:")
#     print("  R²: {:.4f}".format(r2_test))
#     print("  MAE: {:.2f}€/m²".format(mae_test))
#     print("  RMSE: {:.2f}€/m²".format(rmse_test))
#
#     # Top features
#     print("\nFeatures les plus importantes (coefficients absolus):")
#     feature_importance = pd.DataFrame({
#         'feature': feature_names,
#         'coeff': np.abs(model.coef_)
#     }).sort_values('coeff', ascending=False).head(10)
#
#     for idx, row in feature_importance.iterrows():
#         print("  {}: {:.4f}".format(row['feature'], row['coeff']))
#
#     # Visualisation
#     fig, axes = plt.subplots(1, 2, figsize=(14, 5))
#
#     # Scatter plot train
#     axes[0].scatter(y_train, y_train_pred, alpha=0.5, s=10, label='Train')
#     axes[0].plot([y_train.min(), y_train.max()], [y_train.min(), y_train.max()], 'r--', lw=2, label='Parfait')
#     axes[0].set_xlabel('Valeur reelle (€/m²)')
#     axes[0].set_ylabel('Prediction (€/m²)')
#     axes[0].set_title('Train - R²: {:.4f}'.format(r2_train))
#     axes[0].legend()
#     axes[0].grid(True, alpha=0.3)
#
#     # Scatter plot test
#     axes[1].scatter(y_test, y_test_pred, alpha=0.5, s=10, label='Test', color='orange')
#     axes[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Parfait')
#     axes[1].set_xlabel('Valeur reelle (€/m²)')
#     axes[1].set_ylabel('Prediction (€/m²)')
#     axes[1].set_title('Test - R²: {:.4f}'.format(r2_test))
#     axes[1].legend()
#     axes[1].grid(True, alpha=0.3)
#
#     plt.tight_layout()
#     plt.savefig(OUTPUT_DIR/ 'regression_lineaire.png', dpi=150)
#     plt.close()
#
#     # Sauvegarde modele
#     with open(OUTPUT_DIR /'model_linear_regression.pkl', 'wb') as f:
#         pickle.dump(model, f)
#
#     return model, r2_test, mae_test


def logistic_regression(X_train, X_test, y_train, y_test, feature_names):
    """Regression logistique pour classification cher/bon marche"""
    print("REGRESSION LOGISTIQUE - Classification Cher/Bon marche")

    # Créer target binaire (mediane comme seuil)
    y_train_binary = (y_train > np.median(y_train)).astype(int)
    y_test_binary = (y_test > np.median(y_test)).astype(int)

    seuil = np.median(y_train)
    print("Seuil de classification: {:.0f}€/m²".format(seuil))
    print("Classe 0 (bon marche): < {:.0f}€/m²".format(seuil))
    print("Classe 1 (cher): >= {:.0f}€/m²\n".format(seuil))

    print("Entrainement")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train_binary)
    print("OK\n")

    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1]

    # Métriques
    acc_train = accuracy_score(y_train_binary, y_train_pred)
    acc_test = accuracy_score(y_test_binary, y_test_pred)
    precision = precision_score(y_test_binary, y_test_pred)
    recall = recall_score(y_test_binary, y_test_pred)
    f1 = f1_score(y_test_binary, y_test_pred)
    roc_auc = roc_auc_score(y_test_binary, y_test_proba)

    print("RESULTATS REGRESSION LOGISTIQUE")
    print("\nAccuracy:")
    print("  Train: {:.4f}".format(acc_train))
    print("  Test: {:.4f}".format(acc_test))

    print("\nMetriques Test:")
    print("  Precision: {:.4f}".format(precision))
    print("  Recall: {:.4f}".format(recall))
    print("  F1-Score: {:.4f}".format(f1))
    print("  ROC-AUC: {:.4f}".format(roc_auc))

    # Matrice de confusion
    cm = confusion_matrix(y_test_binary, y_test_pred)
    print("\nMatrice de confusion:")
    print("  TN: {}, FP: {}".format(cm[0, 0], cm[0, 1]))
    print("  FN: {}, TP: {}".format(cm[1, 0], cm[1, 1]))

    # Visualisation
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Matrice de confusion
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
                xticklabels=['Bon marche', 'Cher'], yticklabels=['Bon marche', 'Cher'])
    axes[0].set_xlabel('Prediction')
    axes[0].set_ylabel('Reel')
    axes[0].set_title('Matrice de confusion')

    # Distribution probabilites
    axes[1].hist(y_test_proba[y_test_binary == 0], bins=30, alpha=0.6, label='Bon marche (reel)')
    axes[1].hist(y_test_proba[y_test_binary == 1], bins=30, alpha=0.6, label='Cher (reel)')
    axes[1].set_xlabel('Probabilite classe "Cher"')
    axes[1].set_ylabel('Frequence')
    axes[1].set_title('Distribution probabilites - Test')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/ 'regression_logistique.png', dpi=150)
    plt.close()

    # Sauvegarde modele
    with open(OUTPUT_DIR/ 'model_logistic_regression.pkl', 'wb') as f:
        pickle.dump(model, f)

    return model, acc_test, roc_auc


def export_results(r2_linear, mae_linear, acc_logistic, roc_auc_logistic):
    """Exporte résumé résultats"""
    print("EXPORT RESULTATS")

    results = {
        'Linear Regression': {
            'R² Test': r2_linear,
            'MAE Test': mae_linear
        },
        'Logistic Regression': {
            'Accuracy Test': acc_logistic,
            'ROC-AUC': roc_auc_logistic
        }
    }

    with open(OUTPUT_DIR/ 'resultats_ml.txt', 'w') as f:
        f.write("RESULTATS MODELES ML - DVFGeo\n")

        f.write("REGRESSION LINEAIRE (Prediction prix/m²)\n")
        f.write("R² Test: {:.4f}\n".format(r2_linear))
        f.write("MAE Test: {:.2f}€/m²\n\n".format(mae_linear))

        f.write("REGRESSION LOGISTIQUE (Classification cher/bon marche)\n")
        f.write("Accuracy Test: {:.4f}\n".format(acc_logistic))
        f.write("ROC-AUC: {:.4f}\n".format(roc_auc_logistic))

    print("resultats_ml.txt: sauvegarde resultats")


def main():
    print("ENTRAINEMENT MODELES ML - DVFGeo")

    # Charger données
    X_train, X_test, y_train, y_test, feature_names = load_data()

    # Regression lineaire
   #model_lr, r2_linear, mae_linear = linear_regression(X_train, X_test, y_train, y_test, feature_names)
    #random forest
    model_lr, r2_linear, mae_linear = train_model_principal(X_train, X_test, y_train, y_test, feature_names)

    # Regression logistique
    model_log, acc_logistic, roc_auc = logistic_regression(X_train, X_test, y_train, y_test, feature_names)

    # Export resultats
    export_results(r2_linear, mae_linear, acc_logistic, roc_auc)

    print("ENTRAINEMENT FIFNI")
    print("\nFichiers generes dans: {}".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()