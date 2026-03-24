# BrokerFlow AI - Underwriting Copilot

BrokerFlow AI est un projet de scoring crédit orienté portfolio, avec deux parcours complémentaires:

1. Un parcours notebook centré sur les vraies données Zindi (ingestion ZIP, feature engineering, sélection de variables, calibration, seuil optimal).
2. Un parcours application API/UI historique pour la démonstration produit rapide (synthetic demo flow).

Le projet vise à aider un analyste crédit à structurer la décision, pas à remplacer la décision humaine.

## Objectif métier

À partir de données tabulaires d'un dossier et d'un contexte métier:

1. Estimer un score de risque de défaut (0 à 1).
2. Classer le risque (Low, Medium, High).
3. Produire une explication concise des facteurs importants.
4. Appliquer des règles métier pour recommander une action.
5. Générer un résumé lisible pour l'underwriter.

## État actuel du projet

Le repository est aujourd'hui dans un état hybride assumé:

1. Données réelles Zindi intégrées au pipeline notebook.
2. Artefacts modèles calibrés générés et sauvegardés dans `models/`.
3. API/UI encore alignées sur le flux baseline historique (synthetic + baseline model path).

## Données

Deux modes coexistent.

### 1. Mode réel (recommandé pour l'analyse ML)

Source principale:

- `data-science-nigeria-challenge-1-loan-default-prediction20250307-26022-im3qg9.zip`

Traitement via `src/data/raw_competition.py`:

1. Lecture directe du ZIP sans extraction manuelle.
2. Validation des tables attendues.
3. Fusion des tables de démographie et historique de prêts.
4. Construction de tables enrichies train/test.

Sorties dérivées actuellement présentes:

- `data/processed/train_enriched.csv`
- `data/processed/test_enriched.csv`
- `data/processed/history_features.csv`
- `data/processed/train_features.csv`
- `data/processed/test_features.csv`

### 2. Mode synthétique (démo API/UI)

Fichiers générés sous `data/synthetic/` via `src/data/generate_synthetic_cases.py`.

Ce mode est utile pour démo produit rapide et tests de bout en bout sur des schémas maîtrisés.

## Modélisation

### Pipeline notebook réel

Le flux principal réel est documenté et exécuté dans:

1. `notebooks/04_feature_engineering.ipynb`
2. `notebooks/05_model_baselines.ipynb`
3. `notebooks/06_calibration_explainability.ipynb`

Ce flux produit notamment:

- `models/logreg_raw.pkl`
- `models/best_threshold.txt`
- `models/feature_selection_report.csv`
- `models/selected_features.csv`
- `models/model_coefficients.csv`
- `models/raw_baselines_metrics.csv`

### Pipeline code historique

Le Makefile entraîne encore les modèles baseline/candidate historiques:

- `python -m src.models.train_baseline`
- `python -m src.models.train_lgbm`

Artefacts liés:

- `models/baseline_logreg.pkl`
- `models/candidate_lgbm.pkl`

## API et interface

L'API FastAPI expose maintenant deux routes de scoring:

1. `/v1/score`: route de compatibilité, désormais alignée sur le runtime calibré.
2. `/v2/score`: route cible calibrée (même moteur, mêmes règles V2, enrichie pour usage produit).

La route v2 utilise:

1. `src/models/raw_runtime_feature_adapter.py` pour mapper le payload API vers les features du modèle réel.
2. `src/models/raw_runtime_loader.py` pour charger le runtime calibré.
3. `src/api/routes/scoring_real.py` pour servir le scoring unifié côté modèle.
4. `src/rules/business_rules.py` (V2) pour une décision métier score + seuil + complétude + sévérité d'alertes.

La taxonomie d'alertes est maintenant structurée (code, sévérité, source, confidence) via:

1. `src/rules/consistency_checks.py`
2. `src/agents/reviewer.py`
3. `POST /v1/review-detailed`

La réponse `/v2/score` inclut aussi des métadonnées d'audit de décision:

1. `decision_reason_codes`
2. `decision_alert_severity`
3. `decision_completeness_bucket`
4. `decision_threshold`

Les réponses `/v1/score` et `/v2/score` incluent aussi `alerts_structured`.

L'interface Streamlit est alignée sur le runtime calibré et la décision V2.

La chaîne baseline historique reste disponible dans le code pour compatibilité, mais n'est plus le chemin recommandé en runtime.

## Démarrage rapide

```bash
make setup
```

### Démarrage mode démo API/UI

```bash
python -m src.data.generate_synthetic_cases
make train
make run
streamlit run src/ui/app.py
```

### Démarrage mode réel notebook

1. Vérifier que le ZIP Zindi est à la racine du projet.
2. Exécuter les notebooks 04, 05 puis 06.
3. Vérifier la création des artefacts dans `data/processed/` et `models/`.
4. Générer le bundle runtime unifié pour l'API v2:

```bash
python -m src.models.build_raw_runtime_bundle
```

## Limitations connues

1. La logique runtime est unifiée, mais la route `/v1/score` est maintenue pour compatibilité et doit être dépréciée à terme.
2. Les règles métier V2 sont plus cohérentes mais restent heuristiques (pas de policy engine réglementaire complet).
3. La taxonomie d'alertes est implémentée mais encore légère; elle doit être validée et enrichie avec une nomenclature métier/compliance.
4. Les agents NLP sont majoritairement heuristiques (keywords), non LLM-native.
5. Le projet reste un démonstrateur technique et non un système de décision réglementaire prêt production.

## Documentation associée

- `docs/raw_dataset_integration.md`: intégration données Zindi.
- `docs/data_dictionary.md`: dictionnaire des variables et proxies.
- `docs/model_card.md`: état actuel des modèles et artefacts.
- `docs/architecture.md`: architecture logique et flux.
- `docs/demo_script.md`: script de démonstration réaliste.