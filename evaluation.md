# Evaluation - BrokerFlow AI

Ce document formalise l'évaluation du pipeline réel orienté underwriting.

## 1) Dataset et périmètre

Source:

1. ZIP Zindi: `data-science-nigeria-challenge-1-loan-default-prediction20250307-26022-im3qg9.zip`

Tables dérivées:

1. `data/processed/train_enriched.csv`
2. `data/processed/train_features.csv`

Cible:

1. Défaut observé dans les tables de performance train.

## 2) Protocole d'évaluation

1. Sélection de variables avec filtres de qualité + réduction de redondance.
2. Modèle principal: régression logistique calibrée.
3. Validation croisée reportée via `cv_auc_mean` et `cv_auc_std`.
4. Comparaison de deux politiques de décision:
   - seuil standard 0.50
   - seuil optimisé F1 (`0.2309`)

## 3) Métriques retenues

1. ROC AUC: discrimination globale.
2. Brier score: qualité de calibration probabiliste.
3. Precision / Recall / F1: performance opérationnelle selon seuil.
4. Accuracy: stabilité globale de classification.

## 4) Résultats chiffrés

Source chiffrée: `models/raw_baselines_metrics.csv`

| Politique | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Seuil 0.50 | 0.7941 | 0.6316 | 0.1263 | 0.2105 |
| Seuil 0.2309 | 0.7529 | 0.4430 | 0.5316 | 0.4833 |

Mesures globales du modèle:

1. ROC AUC: 0.7277
2. Brier score: 0.1498
3. CV AUC mean ± std: 0.7012 ± 0.0203
4. Nombre de variables retenues: 21

## 5) Comparaison et arbitrage

Arbitrage principal:

1. Le seuil 0.50 préserve mieux l'accuracy brute mais manque beaucoup de défauts (recall faible).
2. Le seuil 0.2309 réduit l'accuracy globale mais améliore fortement la détection du risque (recall et F1).

Décision métier retenue:

1. Conserver le seuil 0.2309 pour un contexte underwriting orienté maîtrise du risque.

Scénarios de politique (lecture décisionnelle):

1. Politique stricte (proche seuil 0.50): moins de dossiers bloqués en revue, mais plus de défauts manqués.
2. Politique équilibrée (seuil 0.2309 + V2): plus de détection de risque, avec revue manuelle sur les cas sensibles.

Choix retenu:

1. Politique équilibrée, car elle protège mieux le portefeuille sans retirer la décision humaine.

## 6) Biais et limites

1. Biais de sélection potentiels liés à la population de la compétition.
2. Sensibilité au drift temporel et aux changements de comportement clients.
3. Règles de décision V2 encore heuristiques.
4. Taxonomie d'alertes à renforcer avec validation compliance.

## 7) Monitoring recommandé

1. Suivi mensuel des distributions de score (drift).
2. Suivi du recall des défauts observés par segment.
3. Suivi du taux de revue manuelle et du taux de décision renversée.

## 8) Baseline vs challengers

Un benchmark complémentaire est disponible via:

```bash
python -m src.models.train_challenger
```

Modèles comparés:

1. `baseline_logreg` (logistique calibrée)
2. `lightgbm` (gradient boosting calibré)
3. `stacking_logreg_lgbm` (stacking calibré)

Sorties générées:

1. `models/challenger_metrics.csv`
2. `models/challenger_winner.json`
3. `models/baseline_logreg_calibrated.pkl`
4. `models/lightgbm_calibrated.pkl`
5. `models/stacking_logreg_lgbm_calibrated.pkl`

Règle de sélection par défaut:

1. Priorité à la détection du risque (`recall@best`, `f1@best`) avec calibration prise en compte (`brier`).

## 9) Conclusion

Le pipeline actuel est cohérent pour une démonstration métier sérieuse:

1. Modèle calibré explicable.
2. Seuil opérationnel justifié par les métriques.
3. Décision enrichie par des règles V2 et des alertes structurées.
4. Underwriter maintenu comme décideur final sur les cas en revue.

La prochaine étape prioritaire est la validation métier/compliance des règles et des alertes avant toute ambition production.
