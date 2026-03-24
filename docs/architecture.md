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
	- Runtime API actuel via `src/models/predict.py` (baseline historique).
	- Analyse explicative avancée via `notebooks/06_calibration_explainability.ipynb`.

5. Règles et agents
	- Recommandation métier: `src/rules/recommendation.py`.
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

## Décision d'architecture actuelle

L'écart entre Flux A (réel) et Flux B (runtime) est temporairement accepté pour préserver la continuité de la démo applicative tout en faisant progresser la crédibilité data science.

## Prochaine convergence

Objectif cible: brancher API/UI sur l'artefact calibré principal et son seuil optimisé, puis harmoniser tests et monitoring autour de ce flux unique.