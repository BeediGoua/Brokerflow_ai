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

### Couche décision métier (API v2)

La recommandation ne repose pas uniquement sur la classe de risque. La politique V2 combine:

1. score calibré,
2. seuil opérationnel,
3. complétude du dossier,
4. sévérité des alertes.

La réponse API v2 expose des champs d'audit:

- `decision_reason_codes`
- `decision_alert_severity`
- `decision_completeness_bucket`
- `decision_threshold`

La réponse de scoring expose aussi des alertes structurées (`alerts_structured`) avec:

1. `code`
2. `severity`
3. `source`
4. `confidence`

### Interprétabilité

- Interprétation globale via coefficients standardisés.
- Analyse segmentée de calibration pour détecter dérives ou biais de calibration.

### Limites

1. Modèle linéaire: interactions non linéaires moins bien captées.
2. Dépendance à la qualité des features dérivées du schéma brut.
3. Performance sensible aux shifts de population (drift temporel).
4. Politique métier V2 encore heuristique (pas d'arbre de décision réglementaire validé métier/compliance).

## 2) Modèles historiques conservés

Ces modèles existent pour compatibilité runtime API/UI actuelle:

- `models/baseline_logreg.pkl`
- `models/candidate_lgbm.pkl`

Ils restent utiles pour la démo applicative existante, mais ne représentent pas le flux analytique réel le plus avancé.

Note: le runtime de scoring applicatif est désormais aligné sur l'artefact calibré principal; ces artefacts historiques sont surtout conservés pour rétro-compatibilité et comparaison.

## 3) Baseline vs challengers benchmark

Un benchmark additionnel est disponible pour challenger le modèle de référence:

1. `baseline_logreg` (référence)
2. `lightgbm`
3. `stacking_logreg_lgbm` (stacking)

Script:

- `python -m src.models.train_challenger`

Artefacts de benchmark:

- `models/challenger_metrics.csv`
- `models/challenger_winner.json`
- `models/baseline_logreg_calibrated.pkl`
- `models/lightgbm_calibrated.pkl`
- `models/stacking_logreg_lgbm_calibrated.pkl`