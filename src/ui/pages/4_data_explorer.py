"""
Data Explorer – Analyse exploratoire du portefeuille.

Objectif      : visualiser les distributions de risque et les facteurs discriminants.
Utilisateur   : analyste senior / manager.
Question      : où sont concentrés les risques dans ce portefeuille?
Décision      : ajuster la politique par segment ou par variable.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_CANDIDATES = [
    Path("data/processed/train_features.csv"),
    Path("data/processed/train_enriched.csv"),
]
COEFF_PATH = Path("models/model_coefficients.csv")


def _load_data():
    for p in DATA_CANDIDATES:
        if p.exists():
            return pd.read_csv(p), str(p)
    return None, None


def main() -> None:
    st.set_page_config(page_title="Data Explorer", page_icon="🔍", layout="wide")
    st.title("🔍 Data Explorer — Analyse du portefeuille")
    st.markdown(
        "Comprendre les distributions, l'équilibre des classes et les facteurs de risque. "
        "Utilisez ce panneau pour identifier les segments les plus exposés."
    )

    df, source = _load_data()
    if df is None:
        st.warning(
            "Données réelles non trouvées (exécuter les notebooks 04 → 05 → 06). "
            "Démonstration avec données synthétiques."
        )
        from src.data.generate_synthetic_cases import generate_datasets

        df, _, _ = generate_datasets(n_samples=500)
        source = "synthétique (demo)"

    st.caption(f"Source : `{source}` — {len(df):,} lignes · {df.shape[1]} colonnes")

    # Detect target column
    target = next(
        (c for c in ["default", "target", "loan_default", "DEFAULT"] if c in df.columns),
        None,
    )

    st.divider()

    # Overview KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Dossiers", f"{len(df):,}")
    c2.metric("Variables", df.shape[1])
    if target:
        c3.metric("Taux de défaut", f"{df[target].mean():.1%}")

    st.divider()

    # Class balance
    if target:
        st.subheader("Répartition défauts / non-défauts")
        col_l, col_r = st.columns([1, 2])
        with col_l:
            counts = df[target].value_counts().rename(index={0: "Non-défaut", 1: "Défaut"})
            st.dataframe(counts.rename("Nombre").reset_index(), use_container_width=True)
        with col_r:
            st.bar_chart(counts)

    st.divider()

    # Numeric distributions
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target]
    if num_cols:
        st.subheader("Distribution d'une variable selon la classe")
        col_choice = st.selectbox("Variable", options=num_cols[:30])

        if target and target in df.columns and df[target].nunique() == 2:
            hist_data = {}
            for label, name in [(0, "Non-défaut"), (1, "Défaut")]:
                vals = df.loc[df[target] == label, col_choice].dropna()
                if len(vals) > 0:
                    bins = pd.cut(vals, bins=30).value_counts().sort_index()
                    hist_data[name] = bins
            if hist_data:
                st.area_chart(pd.DataFrame(hist_data).fillna(0))
        else:
            bin_counts = pd.cut(df[col_choice].dropna(), bins=30).value_counts().sort_index()
            st.bar_chart(bin_counts)

    st.divider()

    # Feature importance
    st.subheader("Importance des variables (coefficients modèle calibré)")
    if COEFF_PATH.exists():
        coeff_df = pd.read_csv(COEFF_PATH)
        if "feature" in coeff_df.columns and "coefficient" in coeff_df.columns:
            coeff_view = (
                coeff_df.set_index("feature")["coefficient"]
                .abs()
                .sort_values(ascending=False)
                .head(15)
                .sort_values()
            )
            st.bar_chart(coeff_view)
            with st.expander("Coefficients signés (direction de l'effet)"):
                signed = coeff_df.set_index("feature")["coefficient"].sort_values()
                st.dataframe(signed.reset_index(), use_container_width=True)
        else:
            st.dataframe(coeff_df.head(15))
    else:
        st.info(
            "Exécuter les notebooks `04 → 05 → 06` pour générer "
            "`models/model_coefficients.csv`."
        )

    st.divider()

    with st.expander("Aperçu des données brutes (50 premières lignes)"):
        st.dataframe(df.head(50), use_container_width=True)


if __name__ == "__main__":
    main()
