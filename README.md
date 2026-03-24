# BrokerFlow AI – Underwriting Copilot

BrokerFlow AI is a portfolio‑grade project that demonstrates how to turn a classic credit risk problem into a complete decision‑support application for underwriters.  Rather than simply training a model on a competition dataset, this project combines a synthetic dataset, a robust ML pipeline, simple business rules, useful AI agents and a small web interface to create an end‑to‑end copilot for risk analysts.

## Problem Statement

Underwriters and brokers spend a significant amount of time reading through loan applications, checking whether all required information has been provided, estimating the risk of default and writing a short summary for their manager.  The goal of this project is to help them make decisions more quickly and consistently.  Given structured applicant data (age, income, employment status, loan amount, etc.), a short free‑text note and information about which documents were supplied, the system must:

1. **Compute a risk score** (0 – 1) and derive a risk class (Low/Medium/High).
2. **Detect missing or inconsistent information** between the structured data and the applicant’s note.
3. **Produce an explanation** showing the top factors influencing the score.
4. **Recommend an action** (ACCEPTABLE, REVIEW, REQUEST_DOCUMENTS or ESCALATE) based on the score, completeness and inconsistencies.
5. **Generate a short summary** for the broker outlining the reasoning.

The machine does not replace the human decision – it prepares and structures the information so that the underwriter can focus on judgement rather than data collection.

## Demo

The repository includes a simple API built with FastAPI and a demonstration UI built with Streamlit.  To run the demo locally:

```bash
make setup        # install Python dependencies
python -m src.data.generate_synthetic_cases  # generate synthetic datasets under data/synthetic
make train        # train baseline and candidate models on the synthetic data
make run          # start the FastAPI server on http://127.0.0.1:8000
streamlit run src/ui/app.py  # launch the Streamlit demo
```

Screenshots and example inputs/outputs can be found in `data/artifacts/sample_inputs` and `data/artifacts/sample_outputs` once you have run the generation and training scripts.

## Project Architecture

The project follows a modular architecture with clear separation of concerns:

| Layer        | Responsibility                                                                                  |
|-------------|--------------------------------------------------------------------------------------------------|
| **Data intake**    | Loading CSV/JSON input, generating synthetic data for demos and validating schemas.          |
| **Data quality**   | Checking types, ranges and completeness; reporting missing values and obvious incoherences. |
| **Feature engineering** | Creating meaningful ratios and indicators from the raw fields and computing a completeness score. |
| **Scoring ML**     | Training baseline (logistic regression) and candidate (LightGBM) models on the synthetic data. |
| **Explainability** | Summarising global and local feature importances with SHAP and formatting human‑readable explanations. |
| **Business rules** | Applying simple rules on top of the model output to recommend the next action for the broker. |
| **Agents**         | Using lightweight NLP to parse the free‑text note, find inconsistencies and compose a final summary. |
| **Delivery**       | Serving predictions through a FastAPI endpoint and a Streamlit interface for human consumption. |

A detailed architecture diagram can be found in `docs/architecture.md`.

## Data

The repository does **not** redistribute any competition data.  Instead, we approximate the structure and distributions of typical credit‑risk challenges (like Zindi’s *Loan Default Prediction* and *AI4EAC Finance*) with synthetic data generated on the fly.  The script `src/data/generate_synthetic_cases.py` creates three CSV files:

- `applications.csv` – the main table of loan applications with demographic, financial and historical variables.
- `documents.csv` – simulated document metadata (type, whether provided, extraction confidence, etc.).
- `reviews.csv` – placeholder for human review logs (initially empty).

Each column is documented in `docs/data_dictionary.md`.  To respect the licences of real datasets, you should never push proprietary CSV files to GitHub.

## Modelling

Two models are provided:

1. **Logistic Regression** – A simple, easily explainable baseline that uses engineered features only.  The coefficients of this model are useful for sanity checks and quick calibration.
2. **LightGBM** – A gradient boosting tree model that captures non‑linear patterns in the tabular features.  SHAP values are used to interpret its output.

Models are saved to the `models/` directory in pickle format.  The training scripts are located in `src/models/train_baseline.py` and `src/models/train_lgbm.py`.

## Agents

Three simple AI agents supplement the model:

1. **Note Parser** – Extracts key phrases from the free‑text note (e.g. mentions of urgent need or missing documents) and turns them into a structured dictionary.
2. **Reviewer** – Cross‑checks the parsed note against the structured fields and supplied documents to flag inconsistencies and missing information.
3. **Summary Writer** – Combines the score, top factors, rules and alerts into a short human‑readable summary.

An optional `qa_judge` can be implemented in `src/eval/evaluate_agents.py` to measure precision and recall of the agents on a small annotated set.

## Evaluation

The `src/models/evaluate.py` script provides basic ML metrics: ROC‑AUC, PR‑AUC, accuracy, precision, recall, F1 and Brier score.  The test suite under `tests/` contains checks for data validation, feature engineering, business rules, model predictions and API behaviour.

## Limitations

- The datasets are synthetic and do not reflect real credit portfolios.  They are intended solely for demonstration.
- Business rules are deliberately simple; a real underwriting system would require domain expert input and regulatory compliance.
- Agents use keyword‑based NLP which cannot handle complex language.  You can improve this by substituting a transformer model if resources permit.
- The UI is a lightweight Streamlit prototype.  For production, you would implement proper authentication, logging and error handling.

## Reproducing the Project

To reproduce the results locally:

1. Clone this repository.
2. Install Python 3.8+ and run `make setup` to install dependencies.
3. Generate the synthetic datasets with `python -m src.data.generate_synthetic_cases`.
4. Train the models using `make train`.
5. Run the tests using `make tests` to ensure everything works end‑to‑end.
6. Start the FastAPI server (`make run`) and optionally the Streamlit UI.

We recommend using a virtual environment to isolate the dependencies.  Note that you need `shap` and `lightgbm` installed to compute explanations for the advanced model.