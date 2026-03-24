"""
Model Performance – Validation quantitative et benchmark challenger.

Objectif      : comparer baseline vs challengers et valider la robustesse.
Utilisateur   : data scientist / manager risk.
Question      : le modèle est-il fiable? Quel candidat est le meilleur?
Décision      : valider ou challenger le modèle en production.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

_CSS_PATH = Path(__file__).parent.parent / "style.css"


def _load_css() -> None:
    if _CSS_PATH.exists():
        st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


METRICS_PATH = Path("models/raw_baselines_metrics.csv")
CHALLENGER_CSV = Path("models/challenger_metrics.csv")
CHALLENGER_WINNER = Path("models/challenger_winner.json")


def main() -> None:
    st.set_page_config(page_title="Model Performance", page_icon=None, layout="wide")
    _load_css()
    st.title("Model Performance — Validation et benchmark")
    st.markdown(
        "Évaluer la robustesse du modèle principal et comparer "
        "baseline vs challengers (régression logistique / LightGBM / stacking)."
    )

    # ── 1) Modèle principal ──────────────────────────────────────────────────
    st.subheader("1) Modèle principal (régression logistique calibrée, données Zindi)")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ROC AUC", "0.7277")
    c2.metric("Brier Score", "0.1498")
    c3.metric("CV AUC mean", "0.7012")
    c4.metric("CV AUC std", "±0.0203")
    c5.metric("Variables retenues", "21")

    if METRICS_PATH.exists():
        with st.expander("Détail — raw_baselines_metrics.csv"):
            st.dataframe(pd.read_csv(METRICS_PATH), use_container_width=True)
    else:
        st.caption(
            "Exécuter les notebooks `04 → 05 → 06` pour générer `models/raw_baselines_metrics.csv`."
        )

    st.divider()

    # ── 2) Impact du seuil ───────────────────────────────────────────────────
    st.subheader("2) Impact du seuil de décision")
    threshold_df = pd.DataFrame(
        [
            {
                "Politique": "Seuil naïf 0.50",
                "Accuracy": 0.7941,
                "Precision": 0.6316,
                "Recall": 0.1263,
                "F1": 0.2105,
            },
            {
                "Politique": "Seuil optimal 0.2309",
                "Accuracy": 0.7529,
                "Precision": 0.4430,
                "Recall": 0.5316,
                "F1": 0.4833,
            },
        ]
    ).set_index("Politique")

    col_l, col_r = st.columns(2)
    with col_l:
        st.dataframe(threshold_df, use_container_width=True)
    with col_r:
        st.bar_chart(threshold_df[["Precision", "Recall", "F1"]])

    st.caption(
        "Le seuil 0.2309 améliore le **Recall de +321%** et le **F1 de +129%** "
        "vs le seuil naïf, au prix d'une légère baisse d'accuracy (−5 pts)."
    )

    st.divider()

    # ── 3) Benchmark challenger ───────────────────────────────────────────────
    st.subheader("3) Benchmark baseline vs challengers")

    if CHALLENGER_WINNER.exists():
        with open(CHALLENGER_WINNER) as f:
            winner = json.load(f)
        winner_name = winner.get("winner_model", "N/A")
        winner_threshold = winner.get("winner_threshold_best_f1", "N/A")
        winner_rule = winner.get("selection_rule", "N/A")
        st.success(
            f"Modèle gagnant : **{winner_name}** "
            f"| Seuil : {winner_threshold} "
            f"| Règle de sélection : {winner_rule}"
        )

    if CHALLENGER_CSV.exists():
        ch_df = pd.read_csv(CHALLENGER_CSV)
        st.dataframe(ch_df, use_container_width=True)

        # Visual comparison
        if "model" in ch_df.columns:
            plot_cols = [c for c in ["roc_auc", "f1@best", "recall@best"] if c in ch_df.columns]
            if plot_cols:
                st.bar_chart(ch_df.set_index("model")[plot_cols])
    else:
        st.info(
            "Lancer `make challenge` (ou `python -m src.models.train_challenger`) "
            "pour générer `models/challenger_metrics.csv`.\n\n"
            "**Modèles comparés :**\n"
            "- `baseline_logreg` — régression logistique calibrée\n"
            "- `lightgbm` — gradient boosting calibré\n"
            "- `stacking_logreg_lgbm` — stacking calibré"
        )

    st.divider()

    # ── 4) Limites ────────────────────────────────────────────────────────────
    st.subheader("4) Limites et biais connus")
    st.markdown(
        "1. Données issues d'une compétition nigériane : biais de sélection possibles sur la population.\n"
        "2. Sensibilité au drift temporel : recalibration périodique du seuil recommandée.\n"
        "3. Règles V2 heuristiques (pas de policy engine réglementaire complet).\n"
        "4. Taxonomie d'alertes à valider avec compliance avant usage production réglementé."
    )


if __name__ == "__main__":
    main()
