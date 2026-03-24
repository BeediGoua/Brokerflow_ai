# Architecture

This document provides an overview of the major components in the BrokerFlow AI project and how they interact.

## Layers

1. **Data Intake** – Handles loading of CSV/JSON inputs as well as generating synthetic data via `src/data/generate_synthetic_cases.py`.
2. **Preprocessing** – Casts columns to appropriate dtypes and imputes missing values (`src/data/preprocess.py`).
3. **Feature Engineering** – Derives new variables such as ratios and buckets (`src/features/build_features.py`) and computes a completeness score (`src/features/completeness.py`).
4. **Model Training** – Trains baseline (logistic regression) and candidate (LightGBM) models (`src/models/train_baseline.py`, `src/models/train_lgbm.py`).  Models and preprocessors are saved into the `models/` directory.
5. **Prediction & Explainability** – Loads saved models to produce scores (`src/models/predict.py`) and computes contributions for explanation (`src/explain/feature_importance.py`, `src/explain/local_explanations.py`).
6. **Business Rules** – Applies simple rules to derive the recommended action based on the score, completeness and detected alerts (`src/rules/business_rules.py`).
7. **Agents** – Parses the free‑text note (`src/agents/note_parser.py`), reviews inconsistencies (`src/agents/reviewer.py`) and writes a summary (`src/agents/summary_writer.py`).
8. **API & UI** – Serves predictions via FastAPI (`src/api/`) and offers a Streamlit front‑end (`src/ui/`).

## Flow

1. **Generate or load data** – Use the synthetic generator or load external CSV files under `data/raw/`.
2. **Preprocess and engineer features** – Clean and enrich the data.
3. **Train models** – Fit the baseline and candidate models and save them.
4. **Score new applications** – The API accepts application data, runs the pipeline, obtains the risk score, applies business rules and returns the summary.
5. **Review** – The reviewer agent flags any inconsistencies or missing documents.

The design emphasises separation of concerns and testability.  Each module has a clear responsibility and can be unit tested in isolation.