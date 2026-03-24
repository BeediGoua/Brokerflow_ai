"""
Methodology – Protocole de décision et transparence.

Objectif      : expliquer comment les décisions sont prises et auditées.
Utilisateur   : compliance / audit / data scientist.
Question      : comment la décision est-elle construite ? Peut-elle être auditée ?
Décision      : valider la gouvernance avant usage étendu.
"""

import pandas as pd
import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Methodology", page_icon="📖", layout="wide")
    st.title("📖 Methodology — Protocole et transparence")
    st.markdown(
        "Décrire le pipeline de modélisation, la politique de décision V2 "
        "et le protocole de validation quantitative."
    )

    # ── 1) Pipeline ───────────────────────────────────────────────────────────
    st.subheader("1) Pipeline de modélisation")
    st.code(
        "1. Ingestion ZIP Zindi → tables brutes (sans extraction manuelle)\n"
        "2. Enrichissement : fusion démographie + historique prêts\n"
        "3. Feature engineering : ratios, agrégats historiques, indicateurs dérivés\n"
        "4. Sélection variables : filtres qualité + réduction redondance → 21 features\n"
        "5. Modèle : LogisticRegression + CalibratedClassifierCV(cv=5, method='isotonic')\n"
        "6. Seuil opérationnel : maximisation F1(classe défaut) → 0.2309\n"
        "7. Export artefacts : logreg_raw.pkl, best_threshold.txt, model_coefficients.csv",
        language="text",
    )

    st.divider()

    # ── 2) Politique de décision V2 ───────────────────────────────────────────
    st.subheader("2) Politique de décision V2")
    st.code(
        "Entrées :\n"
        "  score_calibré   ← modèle logistique calibré\n"
        "  seuil           ← best_threshold.txt (0.2309)\n"
        "  completeness    ← ratio champs renseignés (low / medium / high)\n"
        "  alertes         ← liste {code, sévérité, source, confidence}\n\n"
        "Règles :\n"
        "  si score < seuil                                → APPROVE\n"
        "  si score ≥ seuil ET max(alertes.sévérité) ≤ LOW  → REVIEW\n"
        "  si score ≥ seuil ET max(alertes.sévérité) ≥ MEDIUM → DECLINE\n\n"
        "Métadonnées d'audit (dans chaque réponse /v2/score) :\n"
        "  decision_reason_codes\n"
        "  decision_alert_severity\n"
        "  decision_completeness_bucket\n"
        "  decision_threshold",
        language="text",
    )

    st.divider()

    # ── 3) Taxonomie des alertes ──────────────────────────────────────────────
    st.subheader("3) Taxonomie des alertes structurées")
    alert_df = pd.DataFrame(
        [
            {
                "Code": "INCOMPLETE_DATA",
                "Sévérité": "low",
                "Source": "completeness",
                "Description": "Données manquantes sur champs critiques",
            },
            {
                "Code": "INCOME_INSTABILITY",
                "Sévérité": "medium",
                "Source": "income",
                "Description": "Score de stabilité revenu faible",
            },
            {
                "Code": "HIGH_DEBT_RATIO",
                "Sévérité": "high",
                "Source": "debt",
                "Description": "Ratio dette / revenu élevé",
            },
            {
                "Code": "PRIOR_DEFAULT",
                "Sévérité": "high",
                "Source": "history",
                "Description": "Défaut antérieur détecté dans l'historique",
            },
            {
                "Code": "SUSPICIOUS_NOTE",
                "Sévérité": "medium",
                "Source": "nlp",
                "Description": "Note libre : indicateurs négatifs détectés",
            },
        ]
    )
    st.dataframe(alert_df, use_container_width=True)

    st.divider()

    # ── 4) Protocole de validation ─────────────────────────────────────────────
    st.subheader("4) Protocole de validation quantitative")
    valid_df = pd.DataFrame(
        [
            {"Étape": "Discrimination", "Méthode": "ROC AUC", "Résultat": "0.7277"},
            {"Étape": "Calibration probabiliste", "Méthode": "Brier Score", "Résultat": "0.1498"},
            {
                "Étape": "Stabilité CV",
                "Méthode": "StratifiedKFold 5-fold",
                "Résultat": "0.7012 ± 0.0203",
            },
            {
                "Étape": "Seuil opérationnel",
                "Méthode": "Maximisation F1 classe défaut",
                "Résultat": "0.2309",
            },
            {
                "Étape": "Benchmark challenger",
                "Méthode": "business_score composite (recall + F1 + brier)",
                "Résultat": "stacking_logreg_lgbm",
            },
        ]
    ).set_index("Étape")
    st.dataframe(valid_df, use_container_width=True)

    st.divider()

    # ── 5) Endpoints API ──────────────────────────────────────────────────────
    st.subheader("5) Endpoints API disponibles")
    endpoints_df = pd.DataFrame(
        [
            {
                "Route": "POST /v1/score",
                "Statut": "compat",
                "Description": "Route de compatibilité (à déprécier)",
            },
            {
                "Route": "POST /v2/score",
                "Statut": "cible",
                "Description": "Route calibrée + métadonnées d'audit complètes",
            },
            {
                "Route": "POST /v1/review-detailed",
                "Statut": "stable",
                "Description": "Taxonomie d'alertes structurées détaillée",
            },
        ]
    ).set_index("Route")
    st.dataframe(endpoints_df, use_container_width=True)

    st.divider()

    # ── 6) Limitations ────────────────────────────────────────────────────────
    st.subheader("6) Limitations et gouvernance")
    st.markdown(
        "1. `/v1/score` maintenu pour compatibilité — plan de dépréciation nécessaire.\n"
        "2. Règles V2 heuristiques — validation compliance réglementaire non effectuée.\n"
        "3. Ce projet est un **démonstrateur technique** — non certifié pour usage production réglementé.\n"
        "4. L'underwriter reste le **décideur final** sur tous les cas `REVIEW`."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(
            "**Notebooks de référence :**\n"
            "- `notebooks/04_feature_engineering.ipynb`\n"
            "- `notebooks/05_model_baselines.ipynb`\n"
            "- `notebooks/06_calibration_explainability.ipynb`\n"
            "- `notebooks/09_champion_challenger_comparison.ipynb`"
        )
    with col_b:
        st.info(
            "**Documentation :**\n"
            "- `evaluation.md`\n"
            "- `docs/model_card.md`\n"
            "- `docs/architecture.md`\n"
            "- `docs/data_dictionary.md`"
        )


if __name__ == "__main__":
    main()
