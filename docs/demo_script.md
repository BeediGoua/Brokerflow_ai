# Demo Script

This script outlines how to demonstrate the BrokerFlow AI project to an interviewer or recruiter.  It covers data generation, training, inference via API and the Streamlit interface.

## 1. Setup Environment

```bash
# Clone the repository and enter the directory
git clone <repo_url>
cd brokerflow-ai

# Install dependencies
make setup
```

## 2. Generate Synthetic Data

Use the provided script to create synthetic applications and documents:

```bash
python -m src.data.generate_synthetic_cases
```

This populates `data/synthetic/applications.csv`, `documents.csv` and `reviews.csv`.

## 3. Train Models

Train both the baseline logistic regression and the candidate LightGBM models:

```bash
make train
```

The models will be saved under `models/` and logs printed to the console.

## 4. Run the API

Start the FastAPI server:

```bash
make run
```

Navigate to `http://127.0.0.1:8000/docs` to explore the interactive API documentation.  Test the `/v1/score` endpoint by posting a JSON object representing an application.

## 5. Launch the Streamlit Demo

Open another terminal and run:

```bash
streamlit run src/ui/app.py
```

Use the sidebar to navigate to:

- **Upload / Enter Application** – Manually enter or paste application data and see the result.
- **Case Result Explorer** – Browse pre‑generated cases and inspect the predictions.
- **Batch Dashboard** – Upload a CSV of multiple applications to see aggregate statistics and individual scores.

## 6. Explainability

Show how the model explains its decisions:

- On the case pages, the “Top Factors” list shows which engineered features contributed most to the risk score.
- The model card describes how global feature importance is computed.

## 7. Agent Evaluation (Optional)

Discuss how you might evaluate the note parser and reviewer agents using `src/eval/evaluate_agents.py` with a small annotated dataset.

## 8. Limitations & Future Work

Conclude by mentioning:

- Data is synthetic; real underwriting decisions require regulatory compliance.
- The rules and agent logic are simplified for demonstration.
- Future work could include adding OCR, a transformer‑based note parser and active learning for continuous improvement.