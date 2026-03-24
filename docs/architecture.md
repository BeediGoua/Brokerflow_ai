# Architecture

Ce document résume l'architecture actuelle de BrokerFlow AI et la coexistence de deux parcours (analytique réel et runtime démo).

## Vue d'ensemble

Le projet comporte deux couches complémentaires:

1. Couche analytique notebook sur données Zindi brutes.
2. Couche applicative API/UI historique pour démonstration rapide.

## Composants principaux

1. Data intake
	- Chargement des données brutes compétition via `src/data/raw_competition.py`.
	- Génération de données synthétiques via `src/data/generate_synthetic_cases.py`.

2. Prétraitement et features
	- Prétraitements tabulaires communs: `src/data/preprocess.py`.
	- Features métier et ratios: `src/features/build_features.py`.
	- Score de complétude: `src/features/completeness.py`.

3. Entraînement modèles
	- Pipeline historique code-first: `src/models/train_baseline.py`, `src/models/train_lgbm.py`.
	- Pipeline principal réel notebook-first: `notebooks/05_model_baselines.ipynb`.

4. Inférence et explication
	- Runtime API unifié calibré via `src/models/raw_runtime_loader.py`.
	- Exposition scoring via `src/api/routes/scoring.py` (v1 compat) et `src/api/routes/scoring_real.py` (v2).
	- Analyse explicative avancée via `notebooks/06_calibration_explainability.ipynb`.

5. Règles et agents
	- Recommandation métier legacy + V2: `src/rules/recommendation.py`.
	- Politique V2 score/seuil/complétude/alertes: `src/rules/business_rules.py`.
	- Taxonomie d'alertes structurées: `src/rules/consistency_checks.py` + `src/agents/reviewer.py`.
	- Agents note/review/summary: `src/agents/`.

6. Exposition
	- API FastAPI: `src/api/`.
	- UI Streamlit: `src/ui/`.

## Flux A - Analytique réel (notebooks)

1. Lire le ZIP Zindi à la racine du repo.
2. Construire les tables enrichies/features (`data/processed/`).
3. Sélectionner les variables et entraîner un modèle calibré.
4. Sauvegarder les artefacts de décision dans `models/`.
5. Contrôler calibration, seuil et stabilité par segment.

Artefacts clés:

- `models/logreg_raw.pkl`
- `models/best_threshold.txt`
- `models/raw_baselines_metrics.csv`
- `models/model_coefficients.csv`

## Flux B - Application démo (API/UI)

1. Générer données synthétiques.
2. Entraîner baseline + candidate via Makefile.
3. Servir le scoring via FastAPI et Streamlit.
4. Appliquer règles métier et génération de résumé.

## Flux C - API calibrée v2

1. Charger les artefacts calibrés (`logreg_raw` + seuil).
2. Adapter le payload API vers les features sélectionnées.
3. Scorer avec probabilités calibrées.
4. Appliquer la politique métier V2.
5. Retourner décision + métadonnées d'audit (reason codes, sévérité, bucket, seuil).

## Flux D - Review détaillée

1. Parser la note et croiser avec les champs structurés/documents.
2. Générer des alertes typées (code, sévérité, source, confidence).
3. Exposer les alertes via `POST /v1/review-detailed`.

## Décision d'architecture actuelle

L'écart entre flux analytique et flux applicatif est réduit: API et UI utilisent désormais le runtime calibré. La dette principale restante concerne la gouvernance métier/compliance de la policy.

## Prochaine convergence

Objectif cible: brancher API/UI sur l'artefact calibré principal et son seuil optimisé, puis harmoniser tests et monitoring autour de ce flux unique.