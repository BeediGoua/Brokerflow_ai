# Model Card

This model card describes the two machine learning models used in BrokerFlow AI.

## Baseline – Logistic Regression

- **Purpose:** Serve as a simple, interpretable baseline for default prediction.
- **Data:** Trained on synthetic data with engineered features and a completeness score.
- **Features:** Ratios (debt/income, requested/income), instalment proxy, bucketed years in job and account tenure, late payment rate, recent credit activity, income stability score and counts of prior loans and late payments.
- **Metrics:** Achieves ROC‑AUC around 0.80 on synthetic test data.  Precision, recall and F1 are reported during training.
- **Interpretability:** Coefficients indicate whether each feature increases or decreases the risk.  Contributions are computed by multiplying standardised features by the coefficients.
- **Limitations:** Linear decision boundary cannot capture complex interactions.  Sensitive to feature scaling.

## Candidate – LightGBM

- **Purpose:** Provide a more powerful non‑linear model that captures interactions between features.
- **Data:** Same synthetic dataset as the baseline.  Features are not scaled.
- **Parameters:** 200 estimators, learning rate 0.05, default depth.
- **Metrics:** Achieves higher AUC than the baseline on synthetic data (>0.85).  Precision, recall and F1 are reported during training.
- **Interpretability:** SHAP values are used to explain predictions locally and globally.  See `src/explain/local_explanations.py`.
- **Limitations:** Harder to interpret than the logistic model.  Overfitting can occur if trained on small real datasets.