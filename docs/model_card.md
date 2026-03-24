# Model Card

Cette model card décrit l'état actuel des modèles disponibles dans BrokerFlow AI.

## 1) Modèle principal de l'analyse réelle

### Identité

- Type: régression logistique calibrée (probabilités calibrées)
- Artefact principal: `models/logreg_raw.pkl`
- Seuil opérationnel recommandé: `models/best_threshold.txt`

### Données d'entraînement

- Source: tables brutes Zindi (ZIP compétition)
- Tables dérivées: `data/processed/train_enriched.csv` et `data/processed/train_features.csv`
- Cible: défaut observé dans les tables train performance

### Sélection de variables

Pipeline appliqué dans `notebooks/05_model_baselines.ipynb`:

1. Filtre de valeurs manquantes.
2. Filtre de variance quasi nulle.
3. Réduction de redondance par corrélation.
4. Screening information value/KS selon disponibilité.
5. Sélection finale régularisée (L1) avec contraintes de lisibilité métier.

Rapports sauvegardés:

- `models/feature_selection_report.csv`
- `models/selected_features.csv`
- `models/model_coefficients.csv`

### Évaluation

- Métriques de base stockées dans `models/raw_baselines_metrics.csv`
- Vérification calibration et comportement par segment dans `notebooks/06_calibration_explainability.ipynb`
- Seuil optimisé par compromis précision/rappel (pas uniquement 0.50)

### Interprétabilité

- Interprétation globale via coefficients standardisés.
- Analyse segmentée de calibration pour détecter dérives ou biais de calibration.

### Limites

1. Modèle linéaire: interactions non linéaires moins bien captées.
2. Dépendance à la qualité des features dérivées du schéma brut.
3. Performance sensible aux shifts de population (drift temporel).

## 2) Modèles historiques conservés

Ces modèles existent pour compatibilité runtime API/UI actuelle:

- `models/baseline_logreg.pkl`
- `models/candidate_lgbm.pkl`

Ils restent utiles pour la démo applicative existante, mais ne représentent pas le flux analytique réel le plus avancé.