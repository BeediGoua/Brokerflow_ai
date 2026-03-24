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

1. `/v1/score`: chaîne baseline historique (compatibilité démo).
2. `/v2/score`: chaîne calibrée alignée sur les artefacts du flux réel (`logreg_raw`).

La route v2 utilise:

1. `src/models/raw_runtime_feature_adapter.py` pour mapper le payload API vers les features du modèle réel.
2. `src/models/raw_runtime_loader.py` pour charger le runtime calibré.
3. `src/api/routes/scoring_real.py` pour servir le scoring unifié côté modèle.

L'interface Streamlit reste encore branchée sur la logique historique tant que la migration UI complète n'est pas finalisée.

Chaîne baseline historique (toujours disponible):

1. Score via `src/models/predict.py`.
2. Règles via `src/rules/recommendation.py`.
3. Agents texte (parse, review, summary) pour enrichir la décision.

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

1. La convergence modèle est en place via `/v2/score`, mais `/v1/score` et certaines pages UI utilisent encore la chaîne historique.
2. Les règles métier restent simplifiées pour un contexte portfolio.
3. Les agents NLP sont majoritairement heuristiques (keywords), non LLM-native.
4. Le projet reste un démonstrateur technique et non un système de décision réglementaire prêt production.

## Documentation associée

- `docs/raw_dataset_integration.md`: intégration données Zindi.
- `docs/data_dictionary.md`: dictionnaire des variables et proxies.
- `docs/model_card.md`: état actuel des modèles et artefacts.
- `docs/architecture.md`: architecture logique et flux.
- `docs/demo_script.md`: script de démonstration réaliste.