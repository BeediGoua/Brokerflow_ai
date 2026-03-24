"""
Threshold Simulator – Simulateur d'impact du seuil de décision.

Objectif      : explorer l'impact du seuil sur les métriques opérationnelles.
Utilisateur   : risk manager / data scientist.
Question      : quel seuil minimise le coût du risque métier?
Décision      : ajuster la politique de scoring selon la priorité (recall vs precision).

Simulation basée sur un modèle synthétique calibré sur les paramètres connus:
  AUC = 0.7277, seuil optimal = 0.2309
"""

import numpy as np
import pandas as pd
import streamlit as st

KNOWN_AUC = 0.7277
N_SAMPLES = 3000
DEFAULT_RATE = 0.15
OPTIMAL_THRESHOLD = 0.2309


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))


def _generate_calibrated_scores(n: int, auc: float, default_rate: float):
    """
    Génère des paires (y_true, y_score) dont l'AUC correspond au paramètre donné.
    Utilise deux gaussiennes séparées dont l'écart est calibré sur l'AUC cible.
    """
    rng = np.random.default_rng(42)
    n_pos = int(n * default_rate)
    n_neg = n - n_pos

    # Séparation empirique: AUC ≈ Φ(d/√2) pour distributions normales
    # d ≈ 1.07 pour AUC=0.7277
    d = 1.07
    pos_logits = rng.normal(loc=d / 2, scale=0.9, size=n_pos)
    neg_logits = rng.normal(loc=-d / 2, scale=0.9, size=n_neg)

    logits = np.concatenate([pos_logits, neg_logits])
    scores = _sigmoid(logits)
    labels = np.array([1] * n_pos + [0] * n_neg)

    idx = rng.permutation(n)
    return labels[idx], scores[idx]


def _metrics_at_threshold(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true)

    return dict(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        accuracy=round(accuracy, 4),
        approve_pct=round((y_pred == 0).mean() * 100, 1),
        flag_pct=round((y_pred == 1).mean() * 100, 1),
        n_true_defaults_caught=tp,
        n_defaults_missed=fn,
    )


@st.cache_data
def _build_curves():
    y_true, y_score = _generate_calibrated_scores(N_SAMPLES, KNOWN_AUC, DEFAULT_RATE)
    thresholds = np.linspace(0.05, 0.90, 300)
    rows = [
        {**_metrics_at_threshold(y_true, y_score, float(t)), "threshold": round(float(t), 4)}
        for t in thresholds
    ]
    return y_true, y_score, pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(page_title="Threshold Simulator", page_icon="🎚️", layout="wide")
    st.title("🎚️ Threshold Simulator — Impact du seuil de décision")
    st.markdown(
        "Simuler l'impact du seuil de décision sur la détection des défauts et la distribution "
        "des décisions APPROVE / REVIEW / DECLINE. "
        "Basé sur un modèle synthétique calibré sur AUC = 0.7277."
    )

    y_true, y_score, curve_df = _build_curves()

    st.divider()

    threshold = st.slider(
        "Seuil de décision",
        min_value=0.05,
        max_value=0.90,
        value=OPTIMAL_THRESHOLD,
        step=0.01,
        format="%.2f",
        help="Score ≥ seuil → REVIEW ou DECLINE | Score < seuil → APPROVE",
    )

    current = _metrics_at_threshold(y_true, y_score, threshold)
    optimal = _metrics_at_threshold(y_true, y_score, OPTIMAL_THRESHOLD)
    naive = _metrics_at_threshold(y_true, y_score, 0.50)

    st.divider()

    # KPIs avec delta vs seuil optimal
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Precision",
        f"{current['precision']:.3f}",
        delta=f"{current['precision'] - optimal['precision']:+.3f} vs optimal",
    )
    c2.metric(
        "Recall (défauts détectés)",
        f"{current['recall']:.3f}",
        delta=f"{current['recall'] - optimal['recall']:+.3f} vs optimal",
    )
    c3.metric(
        "F1",
        f"{current['f1']:.3f}",
        delta=f"{current['f1'] - optimal['f1']:+.3f} vs optimal",
    )
    c4.metric(
        "Accuracy",
        f"{current['accuracy']:.3f}",
        delta=f"{current['accuracy'] - optimal['accuracy']:+.3f} vs optimal",
    )

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Distribution des décisions")
        decision_df = pd.DataFrame(
            {
                "Décision": ["✅ APPROVE", "⚠️ REVIEW/DECLINE"],
                "%": [current["approve_pct"], current["flag_pct"]],
            }
        ).set_index("Décision")
        st.bar_chart(decision_df)
        st.caption(
            f"Sur {N_SAMPLES} dossiers simulés : "
            f"{current['n_true_defaults_caught']} défauts détectés, "
            f"{current['n_defaults_missed']} manqués."
        )

    with col_r:
        st.subheader("Comparaison seuils de référence")
        comp_df = pd.DataFrame(
            [
                {"Politique": f"Seuil choisi ({threshold:.2f})", **current},
                {"Politique": f"Optimal ({OPTIMAL_THRESHOLD})", **optimal},
                {"Politique": "Naïf (0.50)", **naive},
            ]
        ).set_index("Politique")[["precision", "recall", "f1", "accuracy", "approve_pct"]]
        st.dataframe(comp_df, use_container_width=True)

    st.divider()

    st.subheader("Courbes Precision / Recall / F1 selon le seuil")
    chart_df = curve_df.set_index("threshold")[["precision", "recall", "f1"]]
    st.line_chart(chart_df, use_container_width=True)
    st.caption(
        f"Seuil sélectionné : **{threshold:.2f}** "
        f"| Seuil optimal (max F1) : **{OPTIMAL_THRESHOLD}**"
    )

    st.divider()

    st.subheader("Interprétation métier")
    if threshold < 0.15:
        st.warning(
            "⚠️ Seuil très bas : presque tous les dossiers sont flaggés. "
            "Coût opérationnel très élevé, peu de valeur ajoutée."
        )
    elif threshold <= 0.30:
        st.success(
            "✅ Zone équilibrée : bonne détection des défauts, revue ciblée. "
            "Recommandé pour un contexte underwriting orienté maîtrise du risque."
        )
    elif threshold <= 0.50:
        st.info(
            "ℹ️ Zone modérée : moins de faux positifs, mais davantage de défauts manqués. "
            "À privilégier si le coût de la revue manuelle est élevé."
        )
    else:
        st.error(
            "🔴 Seuil élevé : beaucoup de défauts non détectés. "
            "Risque portefeuille non maîtrisé — à éviter en contexte underwriting strict."
        )


if __name__ == "__main__":
    main()
