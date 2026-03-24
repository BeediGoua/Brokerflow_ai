# Template Streamlit Decision App - Réutilisable

## Principes fondamentaux

### 1. Arborescence idéale

```
my_decision_project/
├── README.md                          # Align: problem → pages → install
├── requirements.txt
├── Makefile
├── src/
│   ├── __init__.py
│   ├── config/settings.py             # Config centralisée
│   ├── models/                        # Modèles, runtime, loading
│   ├── rules/                         # Logique métier, policies
│   ├── data/                          # Ingestion, processing
│   └── utils/                         # Helpers partagés
├── data/
│   ├── raw/                           # Données sources
│   ├── processed/                     # Features, train/test
│   └── artifacts/                     # Models, preprocessors
├── notebooks/                         # Analytique, prototypes
├── app/
│   ├── app.py                         # STREAMLIT ROUTER (début)
│   ├── pages/
│   │   ├── 01_executive_summary.py    # Home: pitch + KPIs
│   │   ├── 02_data_explorer.py        # Business insights
│   │   ├── 03_case_reviewer.py        # Opérationnel: 1 cas
│   │   ├── 04_simulator.py            # What-if
│   │   ├── 05_model_perf.py           # Validation technique
│   │   └── 06_methodology.py          # Traçabilité
│   └── utils/
│       ├── ui_components.py           # Boutons, logs, mise en forme
│       └── session_state.py           # Cache Streamlit
├── tests/                             # Tests unitaires
└── .gitignore
```

### 2. Page Home = Vente + Contexte (JAMAIS techno d'abord)

**Structure standardisée:**

```
01_executive_summary.py
├── Title + subtitle
├── KPI cards (3-4 métriques principales)
├── Section 1: Business Problem (lisible par manager)
├── Section 2: Value Delivered (ROI, risque réduit, etc.)
├── Section 3: How to Use (3 appels à action vers autres pages)
└── Footer: Contact + doc links
```

**Code template:**

```python
import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

st.title("🎯 Decision Engine - Executive Summary")
st.write("Help [Underwriter] make better credit decisions with ML + rules.")

# KPI row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Default Rate Detected", "92%", "+18% vs naive")
col2.metric("Review Time Saved", "3 min/case", "per analyst")
col3.metric("Model AUC", "0.73", "validated")
col4.metric("Policies Active", "3", "baseline/v2/sim")

st.divider()

# Business problem
st.subheader("The Problem")
st.write("Underwriters struggle with inconsistent risk scoring...")

st.subheader("The Solution")
st.write("Calibrated ML model + decision rules + structured alerts")

st.divider()

# Navigation
st.subheader("Get Started")
st.info("""
📊 **[Data Explorer →](02_data_explorer)** Understand market trends  
🔍 **[Case Reviewer →](03_case_reviewer)** Score your first application  
⚙️ **[Simulator →](04_simulator)** Test threshold changes
""")
```

### 3. Page Operationnel = 1 cas concret

**Structure:**

```
03_case_reviewer.py
├── Input: client ID ou upload CSV
├── Fetch: applicant data
├── Score: avec model runtime
├── Apply: business rules V2
├── Output:
│   ├── Decision (APPROVE/REVIEW/DECLINE)
│   ├── Confidence + threshold used
│   ├── Reason codes (explainability)
│   ├── Alerts (structured taxonomy)
│   └── Audit trail (who, when, model version)
```

### 4. Page Simulator = Décision-support

**Idée:** slider seuil → recalcul → nouvelles métriques

```python
threshold = st.slider("Risk Threshold", 0.0, 1.0, 0.5)
# Re-apply business rules avec ce seuil
# Afficher: impact sur approval rate, recall, precision
```

### 5. Page Performance = Crédibilité technique

**Contenu type:**

```
05_model_perf.py
├── CV scores (mean ± std)
├── Calibration curve
├── Feature importance (top 10)
├── ROC + confusion matrix
├── Comparison table: baseline vs challengers
├── Limitations + bias section
```

### 6. Page Méthodologie = Gouvernance

**Contenu type:**

```
06_methodology.py
├── Policy definition (V1, V2, etc.)
├── Feature selection protocol
├── Threshold optimization method
├── Alert taxonomy
├── Limitations & known risks
├── Recalibration schedule
```

---

## Checklist avant de lancer

### Code
- [ ] Toutes les pages import `src.*` centralisument
- [ ] Session state utilisé pour cache calculs lourds
- [ ] Pas de hardcoding: tout via settings.py
- [ ] Logs structurés pour audit

### Documentation
- [ ] README dit: problem → pages → install → quickstart
- [ ] Chaque page a 1 phrase d'objectif dans le docstring
- [ ] README liste le rôle utilisateur pour chaque page
- [ ] 1 schéma: "qui → quelle page → quelle décision"

### Alignment
- [ ] Noms pages = table of contents README
- [ ] app.py router = liste complète des pages
- [ ] Si page existe, elle est dans README + docs
- [ ] Ordre pages = ordre logique (Home → insights → opera → test → validation → method)

---

## Améliorations par rapport version 1

| Avant | Après |
|-------|-------|
| "5 modules" mais 6 pages | Compter exactement + documenter |
| README oublie 1 page | Template force exhaustivité |
| Home parle technique | Home = pitch + KPIs business |
| Pas de simulator | Page dédiée what-if |
| Pas de clarity user | Chaque page a 1 utilisateur cible explicite |
| Pas d'audit trail | Case reviewer loggue décisions |

---

## Prochaines étapes

1. Adapter BrokerFlow AI selon ce template
2. Créer 6 pages Streamlit alignées
3. Updater README avec page map
4. Valider alignment README + pages
5. Copier ce template dans docs/ comme référence pour tous les futurs projets
