"""
BrokerFlow AI – Page d'accueil / Executive Summary.

Présente le problème métier, les KPIs clés et guide le lecteur
vers la page adaptée à son profil (analyste, underwriter, compliance).
"""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="BrokerFlow AI",
        page_icon="🏦",
        layout="wide",
    )

    st.title("🏦 BrokerFlow AI — Underwriting Copilot")
    st.markdown(
        "> **Objectif** : aider un underwriter junior à structurer une décision crédit "
        "claire, explicable et auditable — sans remplacer le jugement humain."
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Problème")
        st.markdown(
            "1. Les décisions crédit peuvent être incohérentes quand le risque est évalué à l'intuition.\n"
            "2. Les souscripteurs ont besoin d'une recommandation **explicable**, pas d'une probabilité brute."
        )
    with col2:
        st.subheader("Solution")
        st.markdown(
            "1. Score calibré → seuil optimal → **APPROVE / REVIEW / DECLINE**\n"
            "2. Chaque décision inclut motifs, alertes classifiées et métadonnées d'audit."
        )

    st.divider()

    st.subheader("📊 Résultats clés — modèle calibré, données Zindi")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ROC AUC", "0.7277", help="Discrimination globale du modèle calibré")
    c2.metric("Brier Score", "0.1498", help="Qualité de calibration probabiliste")
    c3.metric("Seuil optimal", "0.2309", help="Seuil maximisant F1 sur la classe défaut")
    c4.metric("F1 @ seuil 0.50", "0.21", "seuil naïf", delta_color="off")
    c5.metric("F1 @ seuil optimal", "0.48", "+129%")

    st.divider()

    st.subheader("🗺️ Navigation — par profil")
    ca, cb, cc = st.columns(3)
    with ca:
        st.info(
            "**🔍 Analyste / Manager**\n\n"
            "→ **Data Explorer** : distributions du portefeuille, facteurs de risque\n\n"
            "→ **Model Performance** : métriques, comparaison modèles"
        )
    with cb:
        st.success(
            "**📋 Underwriter (usage opérationnel)**\n\n"
            "→ **Upload Case** : scorer un dossier, obtenir une recommandation\n\n"
            "→ **Batch Dashboard** : traiter un CSV de dossiers"
        )
    with cc:
        st.warning(
            "**📐 Risk Manager / Compliance**\n\n"
            "→ **Threshold Simulator** : simuler l'impact du seuil\n\n"
            "→ **Methodology** : protocole V2, alertes, limites"
        )

    st.divider()

    st.subheader("🔧 Flux décisionnel")
    st.code(
        "Données brutes ─► Feature Engineering (21 variables)\n"
        "                              │\n"
        "              Régression logistique calibrée\n"
        "                              │\n"
        "                    Score risque (0–1)\n"
        "                              │\n"
        "      Seuil 0.2309 ◄──── Politique V2 ────► Alertes structurées\n"
        "            │                                       │\n"
        "     score < 0.23           ambiguité / alerte  score élevé + alerte HIGH\n"
        "         │                        │                       │\n"
        "      APPROVE                  REVIEW                 DECLINE\n",
        language="text",
    )

    st.caption(
        "BrokerFlow AI est un démonstrateur technique. "
        "L'underwriter reste le décideur final sur tous les cas REVIEW."
    )


if __name__ == "__main__":
    main()