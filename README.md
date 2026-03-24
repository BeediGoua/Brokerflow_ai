# BrokerFlow AI - Underwriting Copilot

BrokerFlow AI est un projet de scoring crédit orienté décision underwriting.
Le but n'est pas seulement de prédire un risque, mais d'aider un analyste à choisir une action claire et justifiable.

## 1. Problem

Problème concret:

1. Les décisions de crédit peuvent être incohérentes quand le risque est évalué uniquement à l'intuition.
2. Les souscripteurs ont besoin d'une recommandation explicable, pas d'une simple probabilité.

Utilisateur cible:

1. Analyste crédit / underwriter junior.

## 2. Why it matters

Si le problème n'est pas traité:

1. Les défauts non détectés augmentent le coût du risque.
2. Les bons dossiers rejetés réduisent la croissance.
3. Les décisions peu traçables limitent la confiance métier.

La valeur métier recherchée est donc double: mieux détecter le risque et mieux justifier la décision.

## 3. Solution

Pipeline simple et lisible:

1. Ingestion des données brutes Zindi depuis ZIP.
2. Feature engineering et sélection de variables.
3. Entraînement d'un modèle logistique calibré.
4. Optimisation d'un seuil opérationnel.
5. Politique de décision V2: score + seuil + complétude + sévérité d'alertes.

**Vue d'ensemble pipeline:**

```
Données brutes (CSV) → Feature Engineering → Modèle logistique
                                                     ↓
                                            Score risque (0-1)
                                                     ↓
                                        Seuil optimal + Règles V2
                                                     ↓
                                   Recommandation (APPROVE/REVIEW/DECLINE)
```

Comparaison modèles (simple):

1. Benchmark baseline vs challengers avec trois options:
	- `baseline_logreg`
	- `lightgbm`
	- `stacking_logreg_lgbm`
2. Calibration homogène et comparaison business orientée détection du risque.
3. Export du gagnant et des métriques dans `models/challenger_metrics.csv` et `models/challenger_winner.json`.

## 4. Results

Mesures issues de `models/raw_baselines_metrics.csv` (modèle `logreg_business_calibrated`):

| Mesure | Valeur |
|---|---:|
| ROC AUC | 0.7277 |
| Brier score | 0.1498 |
| CV AUC mean ± std | 0.7012 ± 0.0203 |
| Nombre de features | 21 |
| Seuil optimal F1 | 0.2309 |
| F1 à 0.50 | 0.2105 |
| F1 au seuil optimal | 0.4833 |
| Recall à 0.50 | 0.1263 |
| Recall au seuil optimal | 0.5316 |

Lecture métier:

1. Le modèle discrimine correctement le risque (AUC ~0.73).
2. Le seuil optimisé améliore fortement la détection des dossiers risqués.

## 5. Decision

Décision retenue:

1. Utiliser la régression logistique calibrée comme moteur principal.
2. Utiliser le seuil `0.2309` (plutôt que `0.50`).
3. Convertir le score en action via la politique V2.

Pourquoi:

1. Meilleur compromis explicabilité/performance pour l'underwriting.
2. Gain important en rappel et F1 versus le seuil naïf.
3. Décision auditée via `decision_reason_codes`, `decision_alert_severity`, `decision_completeness_bucket`.

**Flux décisionnel V2:**

```
Score calibré
    ↓
Score < 0.2309?
    ├─ Oui → APPROVE (risque faible)
    └─ Non (score ≥ 0.2309)
        ↓
        Alertes structurées?
        ├─ Oui → REVIEW (risque modéré + signaux)
        └─ Non → DECLINE (risque élevé)
        
Chaque décision inclut:
- reason_codes (motifs explicites)
- alert_severity (criticité des alertes)
- completeness_bucket (qualité des données)
```

## Trade-offs et contraintes

Trade-off principal (seuil):

1. Seuil `0.50`: meilleure accuracy brute, mais sous-détection forte des défauts.
2. Seuil `0.2309`: accuracy plus basse, mais détection du risque nettement meilleure.

Contraintes opérationnelles actuelles:

1. Compatibilité: maintien temporaire de `/v1/score`.
2. Gouvernance: règles V2 encore heuristiques (validation compliance incomplète).
3. Maintenance: nécessité de recalibrer périodiquement le seuil selon drift.

## Qui décide et comment

1. Le moteur produit une recommandation (`APPROVE`, `REVIEW`, `DECLINE`) avec traçabilité.
2. L'underwriter reste le décideur final.
3. Les cas ambigus ou alertés sont orientés vers revue manuelle.

## 6. Limitations

1. La route `/v1/score` est conservée pour compatibilité et doit être dépréciée.
2. Les règles V2 restent heuristiques (pas de policy engine réglementaire complet).
3. La taxonomie d'alertes est encore légère et doit être validée côté risk/compliance.
4. Le projet est un démonstrateur technique, pas un système réglementaire production.

## 7. Architecture

Le runtime de scoring est unifié autour de l'artefact calibré:

1. Mapping features: `src/models/raw_runtime_feature_adapter.py`
2. Chargement runtime: `src/models/raw_runtime_loader.py`
3. API scoring: `/v1/score` (compat) et `/v2/score` (cible)
4. Décision métier: `src/rules/business_rules.py` (V2)
5. Alertes structurées: `src/rules/consistency_checks.py`, `POST /v1/review-detailed`

**Deux parcours coexistent:**

```
┌─────────────────────────────────────────────┐
│         PARCOURS RÉEL (Analytique)          │
├─────────────────────────────────────────────┤
│ notebooks/04 → 05 → 06                      │
│ Data Zindi → Features → Modèle calibré     │
│ ↓                                           │
│ models/logreg_raw.pkl                       │
│ models/best_threshold.txt                   │
│ Artifacts: metrics, coefficients, report   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│       PARCOURS DÉMO (Application UI)        │
├─────────────────────────────────────────────┤
│ Données synthétiques → Modèle baseline      │
│ API /v2/score ← runtime calibré             │
│ Streamlit dashboard (single case, batch)    │
│ Alertes structurées + recommandation        │
└─────────────────────────────────────────────┘

Both feed runtime_loader → same decision engine
```

**Endpoints API:**

```
POST /v1/score
  - Route de compatibilité
  - Input: features JSON
  - Output: score_0_1, prediction, alerts

POST /v2/score  
  - Route cible (calibrée)
  - Output: + decision_reason_codes, alert_severity, completeness_bucket

POST /v1/review-detailed
  - Taxonomie d'alertes structurées
```

## Impact métier à suivre

KPI recommandés:

1. Taux de défauts détectés (proxy recall classe défaut).
2. Taux de dossiers en revue manuelle (`REVIEW`).
3. Taux de décisions corrigées après revue humaine.
4. Délai moyen de décision par dossier (efficacité opérationnelle).

## Démarrage rapide

```bash
make setup
```

### Démo API/UI

```bash
python -m src.data.generate_synthetic_cases
make train
make challenge
make run
streamlit run src/ui/app.py
```

**Pages disponibles dans l'application Streamlit:**

| Page | Profil | Utilité |
|---|---|---|
| 🏦 Home | Tous | Pitch, KPIs, navigation |
| 📋 Upload Case | Underwriter | Scorer un dossier, décision immédiate |
| 🔎 Case Result | Underwriter | Explorer des cas pré-scorés |
| 📦 Batch Dashboard | Analyste | Traiter un CSV de dossiers |
| 🔍 Data Explorer | Analyste | Distributions, variables, défauts |
| 🎚️ Threshold Simulator | Risk Manager | Simuler l'impact du seuil |
| 📐 Model Performance | Data Scientist | Métriques, benchmark challengers |
| 📖 Methodology | Compliance | Protocole V2, alertes, limites |

### Parcours réel notebook

1. Vérifier le ZIP Zindi à la racine.
2. Exécuter les notebooks 04, 05, 06.
3. Vérifier les artefacts dans `data/processed/` et `models/`.
4. Construire le bundle runtime:

```bash
python -m src.models.build_raw_runtime_bundle
```

## Documentation associée

1. `evaluation.md`: protocole, métriques, biais et comparaisons.
2. `docs/raw_dataset_integration.md`
3. `docs/data_dictionary.md`
4. `docs/model_card.md`
5. `docs/architecture.md`
6. `docs/demo_script.md`
