# Demo Script

Ce script propose deux démonstrations complémentaires selon l'objectif.

## 1. Préparation

```bash
git clone <repo_url>
cd brokerflow-ai
make setup
```

## 2. Démo A - Parcours analytique réel (recommandé)

Objectif: montrer le travail crédible de data science sur les vraies données Zindi.

### Étapes

1. Vérifier la présence du ZIP Zindi à la racine du projet.
2. Exécuter les notebooks dans cet ordre:
	- `notebooks/04_feature_engineering.ipynb`
	- `notebooks/05_model_baselines.ipynb`
	- `notebooks/06_calibration_explainability.ipynb`
3. Montrer les sorties générées:
	- `data/processed/train_features.csv`
	- `models/logreg_raw.pkl`
	- `models/raw_baselines_metrics.csv`
	- `models/best_threshold.txt`
	- `models/model_coefficients.csv`

### Narratif de présentation

1. Ingestion réelle depuis ZIP sans extraction manuelle.
2. Feature engineering robuste au schéma brut.
3. Sélection de variables multicritère (missingness, variance, corrélation, L1).
4. Calibration des probabilités et choix d'un seuil opérationnel.
5. Contrôle de stabilité/calibration par segment.

## 3. Démo B - Parcours application (API/UI)

Objectif: montrer le produit de scoring interactif.

```bash
python -m src.data.generate_synthetic_cases
make train
make run
streamlit run src/ui/app.py
```

Puis:

1. Ouvrir `http://127.0.0.1:8000/docs` et tester `/v1/score`.
2. Tester ensuite `/v2/score` pour montrer la version calibrée et ses métadonnées de décision.
3. Parcourir les pages Streamlit (single case, result, batch dashboard).
4. Illustrer les alertes, la recommandation et le résumé agent.
5. Montrer `POST /v1/review-detailed` pour la taxonomie d'alertes structurées.

Points à montrer sur `/v2/score`:

1. `decision_reason_codes`
2. `decision_alert_severity`
3. `decision_completeness_bucket`
4. `decision_threshold`

## 4. Message à donner explicitement

Le projet est volontairement en mode hybride:

1. Pipeline notebook réel avancé (données Zindi + calibration).
2. API v1/v2 alignées sur le runtime calibré.
3. UI alignée sur la même logique de décision V2.

Ce choix permet de démontrer à la fois la rigueur analytique et la couche produit.

## 5. Limites et prochaines étapes

1. Déprécier progressivement `/v1/score` (compatibilité).
2. Renforcer la taxonomie d'alertes avec validation métier/compliance.
3. Renforcer l'évaluation hors temps/segment pour monitorer le drift.
4. Industrialiser la gouvernance modèle (versioning, monitoring, retrain).