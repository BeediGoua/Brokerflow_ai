"""
BrokerFlow AI – Executive Summary & Hub de navigation.

Présente l'identité produit, les KPIs système, le contexte stratégique,
l'opposition problème/solution et guide vers chaque page par usage.
"""

from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).parent / "style.css"


def _load_css() -> None:
    if _CSS_PATH.exists():
        st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="BrokerFlow AI", page_icon=None, layout="wide")
    _load_css()

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 0.5rem 0;">
            <h1 style="font-size:2.4rem; font-weight:800; margin:0; color:#111827;">
                BrokerFlow AI
            </h1>
            <p style="font-size:1.1rem; color:#6B7280; margin:0.4rem 0 0 0; font-weight:500;">
                Credit Decision Engine — Next-Generation Underwriting Copilot
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── KPI SYSTEM PERFORMANCE ────────────────────────────────────────────────
    st.markdown("### Suivi des performances système")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Baseline F1 (seuil 0.50)", "0.21", help="F1 sans optimisation de seuil — point de départ")
    c2.metric("Expert System F1", "0.48", "+129%", help="F1 avec seuil optimal 0.2309")
    c3.metric("ROC AUC", "0.7277", help="Discrimination globale du modèle calibré")
    c4.metric("Brier Score", "0.1498", help="Qualité de calibration probabiliste (plus bas = mieux)")
    c5.metric("CV AUC Stability", "0.70 ±0.02", help="StratifiedKFold 5-fold — robustesse mesurée")

    st.divider()

    # ── HERO BOX ──────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-box">
            <h3>De l'intuition au jugement structuré</h3>
            <p>
                BrokerFlow AI remplace le <strong>jugement non documenté</strong> par une
                <strong>recommandation calibrée et auditable</strong>.
                Le moteur transforme un score de risque brut en action concrète —
                <strong>APPROVE / REVIEW / DECLINE</strong> — avec traçabilité complète :
                motifs explicites, alertes classifiées par sévérité, seuil utilisé
                et niveau de complétude du dossier.
            </p>
            <p style="margin:0;">
                L'underwriter reste le décideur final. L'outil l'aide à justifier sa décision,
                pas à la remplacer.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── CONTEXT BLOCKS ────────────────────────────────────────────────────────
    st.markdown("### Contexte & Valeur stratégique")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            <div class="context-block context-client">
                <strong>Utilisateur cible</strong><br/>
                Analyste crédit / underwriter junior dans un établissement financier ou
                de microfinance. Besoin d'une recommandation <em>explicable</em> sur chaque
                dossier, pas d'une probabilité brute isolée.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="context-block context-stakes">
                <strong>Valeur métier</strong><br/>
                Réduire les défauts non détectés · Limiter les bons dossiers rejetés ·
                Tracer chaque décision pour auditabilité compliance · Standardiser
                le niveau de recommandation entre underwriters.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="context-block context-challenge">
                <strong>Défi principal</strong><br/>
                Classe défaut très minoritaire (≈15 %) · Données tabulaires hétérogènes ·
                Seuil naïf (0.50) qui manque 87 % des défauts ·
                Décisions actuellement peu documentées et difficiles à auditer.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="context-block context-constraints">
                <strong>Contraintes connues</strong><br/>
                Démonstrateur technique — non certifié production réglementée ·
                Règles V2 encore heuristiques · Recalibration périodique du seuil
                nécessaire · Données issues d'une compétition Zindi (biais possibles).
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── PROBLEM vs SOLUTION ───────────────────────────────────────────────────
    st.markdown("### Approche opérationnelle")
    p_col, s_col = st.columns(2)
    with p_col:
        st.markdown(
            """
            <div class="context-block context-challenge">
                <strong>Problème — Décision à l'intuition</strong>
                <ul style="margin:0.5rem 0 0 1.1rem; padding:0; line-height:1.8;">
                    <li>Risques manqués coûteux : recall 12 % avec seuil naïf</li>
                    <li>Décisions non documentées, difficiles à auditer</li>
                    <li>Incohérences entre underwriters sur profils similaires</li>
                    <li>Données mal exploitées — aucun signal agrégé</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s_col:
        st.markdown(
            """
            <div class="context-block context-stakes">
                <strong>Solution — Intelligence calibrée</strong>
                <ul style="margin:0.5rem 0 0 1.1rem; padding:0; line-height:1.8;">
                    <li>Seuil optimal → recall 53 % (+321 % vs seuil naïf)</li>
                    <li>Chaque décision tracée : motifs + alertes + audit metadata</li>
                    <li>Revue manuelle systématique sur cas ambigus (REVIEW)</li>
                    <li>Scores actionnables avec niveau de confiance explicite</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── NAVIGATION HUB ────────────────────────────────────────────────────────
    st.markdown("### Outils & Modules — Choisir votre usage")
    n1, n2, n3, n4 = st.columns(4)

    with n1:
        st.markdown(
            """
            <div class="nav-card">
                <div class="nav-card-icon">01</div>
                <div class="nav-card-title">Scorer un dossier</div>
                <div class="nav-card-desc">
                    Saisir les données d'un emprunteur et obtenir immédiatement
                    une recommandation avec alertes, motifs et résumé agent.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ouvrir — Scorer", use_container_width=True, key="btn_upload"):
            st.switch_page("pages/1_upload_case.py")

    with n2:
        st.markdown(
            """
            <div class="nav-card">
                <div class="nav-card-icon">02</div>
                <div class="nav-card-title">Explorer les données</div>
                <div class="nav-card-desc">
                    Visualiser les distributions du portefeuille, les variables
                    discriminantes, les défauts et les facteurs de risque.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ouvrir — Explorer", use_container_width=True, key="btn_explorer"):
            st.switch_page("pages/4_data_explorer.py")

    with n3:
        st.markdown(
            """
            <div class="nav-card">
                <div class="nav-card-icon">03</div>
                <div class="nav-card-title">Simuler un seuil</div>
                <div class="nav-card-desc">
                    Ajuster le seuil de décision et visualiser l'impact sur recall,
                    precision, F1 et la distribution des décisions APPROVE / DECLINE.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ouvrir — Simuler", use_container_width=True, key="btn_threshold"):
            st.switch_page("pages/5_threshold_simulator.py")

    with n4:
        st.markdown(
            """
            <div class="nav-card">
                <div class="nav-card-icon">04</div>
                <div class="nav-card-title">Lire la méthode</div>
                <div class="nav-card-desc">
                    Comprendre le pipeline, la politique de décision V2,
                    le protocole d'évaluation, les sanity checks et les limites.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Lire — Méthodologie", use_container_width=True, key="btn_method"):
            st.switch_page("pages/7_methodology.py")

    st.divider()

    # ── DECISION FLOW ─────────────────────────────────────────────────────────
    st.markdown("### Flux décisionnel — Politique V2")
    st.graphviz_chart(
        """
        digraph decision {
            rankdir=TB
            node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=11]
            edge [fontsize=10, color="#9CA3AF"]

            A  [label="Données brutes\\n(dossier emprunteur)",       fillcolor="#EEF2FF", color="#6366F1"]
            B  [label="Feature Engineering\\n21 variables sélectionnées", fillcolor="#F0F9FF", color="#0EA5E9"]
            C  [label="Modèle logistique calibré\\nCalibratedClassifierCV", shape=ellipse, fillcolor="#F0FDF4", color="#22C55E"]
            D  [label="Score risque (0 → 1)",                        fillcolor="#FAFAF9", color="#78716C"]
            E  [label="Seuil 0.2309 + Alertes\\nPolitique V2",       shape=diamond, fillcolor="#FFF7ED", color="#F97316"]
            F  [label="APPROVE\nscore < 0.23",                  fillcolor="#DCFCE7", color="#16A34A"]
            G  [label="REVIEW\nscore >= 0.23  alerte LOW",      fillcolor="#FEF9C3", color="#CA8A04"]
            H  [label="DECLINE\nalerte >= MEDIUM",               fillcolor="#FEE2E2", color="#DC2626"]
            I  [label="Audit metadata\\nreason_codes · severity\\ncompleteness · threshold", shape=note, fillcolor="#F5F3FF", color="#7C3AED"]

            A -> B -> C -> D -> E
            E -> F  [label="score < seuil"]
            E -> G  [label="score ≥ seuil\\nalerte LOW"]
            E -> H  [label="score ≥ seuil\\nalerte ≥ MEDIUM"]
            F -> I
            G -> I
            H -> I
        }
        """
    )

    st.caption(
        "BrokerFlow AI est un démonstrateur technique. "
        "L'underwriter reste le décideur final sur tous les cas REVIEW."
    )


if __name__ == "__main__":
    main()