"""
Methodology – Protocole de décision et transparence.

Objectif      : expliquer comment les décisions sont prises et auditées.
Utilisateur   : compliance / audit / data scientist.
Question      : comment la décision est-elle construite ? Peut-elle être auditée ?
Décision      : valider la gouvernance avant usage étendu.

Structure :
  Tab 1 — Pipeline & Architecture  : modèle, features, choix techniques justifiés + graphviz
  Tab 2 — Protocole d'évaluation   : évaluation narrative + schéma + stress tests
  Tab 3 — Métriques & Contrôles    : métriques opérationnelles + sanity checks
  Tab 4 — Guide d'utilisation      : usages concrets par persona
"""

from pathlib import Path

import pandas as pd
import streamlit as st

_CSS_PATH = Path(__file__).parent.parent / "style.css"


def _load_css() -> None:
    if _CSS_PATH.exists():
        st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Methodology", page_icon=None, layout="wide")
    _load_css()

    st.title("Methodology — Protocole et transparence")
    st.markdown(
        "Comprendre comment chaque décision est construite, validée et auditée. "
        "Naviguez par onglet selon votre besoin."
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Pipeline & Architecture",
        "Protocole d'évaluation",
        "Métriques & Contrôles",
        "Guide d'utilisation",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — Pipeline & Architecture
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### Comment le modèle est construit")

        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("#### Étapes du pipeline")
            steps = [
                ("1", "Ingestion ZIP Zindi", "Lecture directe du ZIP sans extraction manuelle. Validation des tables attendues."),
                ("2", "Enrichissement", "Fusion démographie + historique prêts. Construction de tables enrichies train/test."),
                ("3", "Feature Engineering", "Ratios, agrégats historiques, indicateurs dérivés. Encodage et normalisation."),
                ("4", "Sélection de variables", "Filtres qualité + réduction redondance → 21 features retenues."),
                ("5", "Modèle", "LogisticRegression + CalibratedClassifierCV(cv=5, method='isotonic')."),
                ("6", "Seuil opérationnel", "Maximisation F1 sur la classe défaut → seuil = 0.2309."),
                ("7", "Export artefacts", "logreg_raw.pkl · best_threshold.txt · model_coefficients.csv"),
            ]
            for num, title, desc in steps:
                st.markdown(
                    f"""<div class="doc-box">
                        <strong>Étape {num} — {title}</strong><br/>
                        <span style="color:#6B7280; font-size:0.88rem;">{desc}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

        with col_r:
            st.markdown("#### Schéma du pipeline")
            st.graphviz_chart(
                """
                digraph pipeline {
                    rankdir=TB
                    node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=10]
                    edge [color="#9CA3AF", fontsize=9]

                    Z  [label="ZIP Zindi\\n(données brutes)", fillcolor="#EEF2FF", color="#6366F1"]
                    E  [label="Enrichissement\\n(fusion tables)", fillcolor="#F0F9FF", color="#0EA5E9"]
                    FE [label="Feature Engineering\\n(ratios, agrégats)", fillcolor="#F0FDF4", color="#22C55E"]
                    FS [label="Sélection variables\\n21 features", fillcolor="#FFF7ED", color="#F97316"]
                    M  [label="Régression logistique\\ncalibrée (isotonic)", shape=ellipse, fillcolor="#F5F3FF", color="#7C3AED"]
                    T  [label="Seuil optimal\\n0.2309 (max F1)", shape=diamond, fillcolor="#FEF9C3", color="#CA8A04"]
                    A  [label="Artefacts\\n.pkl · .txt · .csv", shape=note, fillcolor="#F9FAFB", color="#6B7280"]

                    Z -> E -> FE -> FS -> M -> T -> A
                }
                """
            )

        st.divider()

        st.markdown("#### Pourquoi la régression logistique calibrée ?")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """<div class="context-block context-client">
                    <strong>Explicabilité</strong><br/>
                    Les coefficients signés sont directement interprétables.
                    L'underwriter peut lire les facteurs de risque sans boîte noire.
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """<div class="context-block context-stakes">
                    <strong>Calibration probabiliste</strong><br/>
                    CalibratedClassifierCV garantit que les probabilités sont
                    fiables (Brier 0.1498). Un score 0.3 signifie vraiment ~30 % de risque.
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """<div class="context-block context-challenge">
                    <strong>Robustesse CV</strong><br/>
                    AUC 5-fold : 0.7012 ± 0.0203. Faible variance = modèle
                    stable, pas sur-ajusté à un seul split de données.
                </div>""",
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — Protocole d'évaluation
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### Comment on a évalué le modèle")

        st.markdown(
            """<div class="hero-box">
                <h3>Le principe : prédire ce qu'on connaît déjà</h3>
                <p>
                    On n'a pas de données futures réelles à évaluer.
                    La solution : <strong>simuler le futur sur le passé</strong>.
                    On cache une information connue, on demande au modèle de la retrouver,
                    puis on mesure à quelle distance il se trouve de la bonne réponse.
                </p>
            </div>""",
            unsafe_allow_html=True,
        )

        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("#### Les 4 étapes de l'évaluation")
            protocol_steps = [
                ("1", "Prendre un vrai dossier", "Un emprunteur avec son historique complet."),
                ("2", "Masquer la cible", "Cacher le label de défaut réel avant toute prédiction."),
                ("3", "Scorer à l'aveugle", "Faire tourner le pipeline complet sans voir le résultat réel."),
                ("4", "Vérifier la prédiction", "Comparer la décision produite avec la réalité masquée."),
            ]
            for num, title, desc in protocol_steps:
                st.markdown(
                    f"""<div class="doc-box">
                        <strong>Étape {num} : {title}</strong><br/>
                        <span style="color:#6B7280; font-size:0.88rem;">{desc}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("#### Stress tests appliqués")
            st.markdown(
                """<div class="check-ok"><strong>Cross-validation 5-fold stratifiée</strong> — AUC 0.7012 ± 0.0203</div>
                <div class="check-ok"><strong>Deux seuils testés</strong> — 0.50 naïif vs 0.2309 optimal</div>
                <div class="check-ok"><strong>Contrainte métier</strong> — évaluation sur tous les dossiers disponibles</div>""",
                unsafe_allow_html=True,
            )

        with col_r:
            st.markdown("#### Schéma du protocole")
            st.graphviz_chart(
                """
                digraph eval {
                    rankdir=TB
                    node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=10]
                    edge [color="#9CA3AF", fontsize=9]

                    D  [label="Dossier réel\\n(label connu)", fillcolor="#EEF2FF", color="#6366F1"]
                    M  [label="Masquer le label\\n(défaut réel caché)", fillcolor="#FEF3C7", color="#D97706"]
                    I  [label="Input modèle\\n(features uniquement)", fillcolor="#F0F9FF", color="#0EA5E9"]
                    P  [label="Pipeline scoring\\n(calibré + seuil)", shape=ellipse, fillcolor="#F0FDF4", color="#22C55E"]
                    R  [label="Recommandation\\nAPPROVE / REVIEW / DECLINE", fillcolor="#FFF7ED", color="#F97316"]
                    V  [label="Vérification\\n→ correcte ?", shape=diamond, fillcolor="#F5F3FF", color="#7C3AED"]
                    OK [label="Correct\nou vrai négatif", fillcolor="#DCFCE7", color="#16A34A"]
                    KO [label="Erreur\n(FP ou FN)", fillcolor="#FEE2E2", color="#DC2626"]

                    D -> M -> I -> P -> R -> V
                    V -> OK [label="label = prédiction"]
                    V -> KO [label="label ≠ prédiction"]
                }
                """
            )

        st.divider()

        st.markdown("#### Résultat de l'arbitrage : pourquoi le seuil 0.2309 ?")
        arbitrage_df = pd.DataFrame(
            [
                {"Seuil": "0.50 (naïf)", "Accuracy": "79.4%", "Precision": "63.2%", "Recall": "12.6%", "F1": "21.0%", "Défauts manqués": "87%"},
                {"Seuil": "0.2309 (optimal)", "Accuracy": "75.3%", "Precision": "44.3%", "Recall": "53.2%", "F1": "48.3%", "Défauts manqués": "47%"},
            ]
        ).set_index("Seuil")
        st.dataframe(arbitrage_df, use_container_width=True)
        st.markdown(
            """<div class="context-block context-stakes">
                <strong>Décision</strong> : le seuil 0.2309 est retenu car il réduit les défauts manqués de 87 % à 47 %,
                au prix d'une légère baisse d'accuracy (−4 pts). En contexte underwriting,
                <em>manquer un défaut est plus coûteux que traiter un faux positif en revue</em>.
            </div>""",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — Métriques & Contrôles
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### Métriques opérationnelles et contrôles d'audit")

        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("#### Métriques retenues et leur usage")
            metrics_df = pd.DataFrame(
                [
                    {
                        "Métrique": "ROC AUC",
                        "Valeur": "0.7277",
                        "Usage": "Discrimination globale — indépendant du seuil",
                    },
                    {
                        "Métrique": "Brier Score",
                        "Valeur": "0.1498",
                        "Usage": "Calibration probabiliste — fiabilité des scores",
                    },
                    {
                        "Métrique": "CV AUC (5-fold)",
                        "Valeur": "0.7012 ±0.0203",
                        "Usage": "Robustesse — stabilité hors-sample",
                    },
                    {
                        "Métrique": "Recall (défaut)",
                        "Valeur": "53.2% @ seuil optimal",
                        "Usage": "Détection des risques — KPI prioritaire métier",
                    },
                    {
                        "Métrique": "F1 (défaut)",
                        "Valeur": "48.3% @ seuil optimal",
                        "Usage": "Compromis precision/recall — performance globale",
                    },
                ]
            ).set_index("Métrique")
            st.dataframe(metrics_df, use_container_width=True)

            st.markdown(
                """<div class="context-block context-client" style="margin-top:0.5rem;">
                    <strong>KPI prioritaire métier :</strong> le <strong>Recall</strong> sur la classe défaut.
                    En underwriting, un défaut non détecté coûte plus cher qu'une revue manuelle supplémentaire.
                </div>""",
                unsafe_allow_html=True,
            )

        with col_r:
            st.markdown("#### Sanity checks — Contrôles d'audit")
            st.markdown(
                """<div class="check-ok">
                    <strong>Anti-cheat</strong><br/>
                    <span style="font-size:0.87rem;">
                    Le label de défaut est exclu de toutes les features.
                    Vérifié : aucune fuite de variable cible dans le pipeline.
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                """<div class="check-ok">
                    <strong>Biais de popularité</strong><br/>
                    <span style="font-size:0.87rem;">
                    Le modèle ne répond pas simplement "toujours non-défaut" (classe majoritaire).
                    Recall 53 % sur la classe défaut confirme la détection active des risques.
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                """<div class="check-warn">
                    <strong>Drift temporel</strong><br/>
                    <span style="font-size:0.87rem;">
                    Le seuil est calibré sur une population figée.
                    Une recalibration périodique est nécessaire si le profil des emprunteurs évolue.
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                """<div class="check-warn">
                    <strong>Biais population</strong><br/>
                    <span style="font-size:0.87rem;">
                    Données issues d'une compétition Zindi (Nigeria).
                    Biais de sélection possibles — à valider sur une population réelle cible.
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                """<div class="check-block">
                    <strong>Règles V2 heuristiques</strong><br/>
                    <span style="font-size:0.87rem;">
                    La politique de décision n'est pas issue d'un moteur réglementaire validé.
                    Validation compliance obligatoire avant usage production réglementé.
                    </span>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown("#### Taxonomie des alertes")
        alert_df = pd.DataFrame(
            [
                {"Code": "INCOMPLETE_DATA",   "Sévérité": "low",    "Source": "completeness", "Condition": "Champs critiques manquants"},
                {"Code": "INCOME_INSTABILITY","Sévérité": "medium", "Source": "income",       "Condition": "income_stability_score < 0.4"},
                {"Code": "HIGH_DEBT_RATIO",   "Sévérité": "high",   "Source": "debt",         "Condition": "existing_debt / monthly_income > ratio seuil"},
                {"Code": "PRIOR_DEFAULT",     "Sévérité": "high",   "Source": "history",      "Condition": "has_prior_default = True"},
                {"Code": "SUSPICIOUS_NOTE",   "Sévérité": "medium", "Source": "nlp",          "Condition": "Note libre : mots-clés négatifs détectés"},
            ]
        )
        st.dataframe(alert_df, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — Guide d'utilisation
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### Comment utiliser BrokerFlow AI selon votre rôle")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                """<div class="context-block context-client">
                    <strong>Underwriter — Audit individuel</strong>
                </div>""",
                unsafe_allow_html=True,
            )
            for step in [
                "Aller sur **Upload Case** ou **Case Result**",
                "Saisir les données du dossier",
                "Lire la recommandation et les alertes",
                "Si **APPROVE** → valider directement",
                "Si **REVIEW** → vérifier les alertes et décider",
                "Si **DECLINE** → expliquer le refus avec les motifs générés",
            ]:
                st.markdown(f"- {step}")

            st.markdown(
                """<div class="doc-box" style="margin-top:0.5rem;">
                    <strong>Ce que le système fournit :</strong><br/>
                    Score · Classe · Motifs · Alertes classifiées · Résumé agent
                </div>""",
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """<div class="context-block context-challenge">
                    <strong>Risk Manager — Calibration du seuil</strong>
                </div>""",
                unsafe_allow_html=True,
            )
            for step in [
                "Aller sur **Threshold Simulator**",
                "Ajuster le seuil avec le slider",
                "Observer l'impact sur Recall / Precision / F1",
                "Analyser la distribution APPROVE / DECLINE",
                "Comparer avec les seuils de référence (0.50 vs 0.2309)",
                "Décider d'un seuil adapté à la politique risk",
            ]:
                st.markdown(f"- {step}")

            st.markdown(
                """<div class="doc-box" style="margin-top:0.5rem;">
                    <strong>Règle de lecture :</strong><br/>
                    Seuil bas = plus de détection, plus de revues · Seuil haut = moins de revues, plus de défauts manqués
                </div>""",
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                """<div class="context-block context-stakes">
                    <strong>Data Scientist — Validation & Benchmark</strong>
                </div>""",
                unsafe_allow_html=True,
            )
            for step in [
                "Aller sur **Model Performance**",
                "Vérifier les métriques du modèle principal",
                "Comparer la courbe seuil vs métriques",
                "Lancer `make challenge` pour le benchmark challengers",
                "Lire `models/challenger_metrics.csv` + `winner.json`",
                "Utiliser le notebook 09 pour la comparaison interactive",
            ]:
                st.markdown(f"- {step}")

            st.markdown(
                """<div class="doc-box" style="margin-top:0.5rem;">
                    <strong>Commandes clés :</strong><br/>
                    <code>make train-demo</code> · <code>make challenge</code> · notebook 09
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown("#### Quand ne pas faire confiance au système")
        st.markdown(
            """<div class="context-block context-constraints">
                <strong>Cas où la décision humaine prime toujours :</strong>
                <ul style="margin:0.5rem 0 0 1.1rem; line-height:1.8;">
                    <li>Dossier avec complétude <strong>low</strong> — trop de données manquantes</li>
                    <li>Score très proche du seuil (±0.02) — zone d'incertitude</li>
                    <li>Population hors distribution d'entraînement (autres pays, profils inédits)</li>
                    <li>Tout cas <strong>REVIEW</strong> — l'underwriter est le décideur final</li>
                </ul>
            </div>""",
            unsafe_allow_html=True,
        )

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                """<div class="doc-box">
                    <strong>Notebooks de référence</strong><br/>
                    <code>notebooks/04_feature_engineering.ipynb</code><br/>
                    <code>notebooks/05_model_baselines.ipynb</code><br/>
                    <code>notebooks/06_calibration_explainability.ipynb</code><br/>
                    <code>notebooks/09_champion_challenger_comparison.ipynb</code>
                </div>""",
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                """<div class="doc-box">
                    <strong>Documentation associée</strong><br/>
                    <code>evaluation.md</code> — protocole complet<br/>
                    <code>docs/model_card.md</code> — état des modèles<br/>
                    <code>docs/architecture.md</code> — flux applicatif<br/>
                    <code>docs/data_dictionary.md</code> — variables
                </div>""",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
