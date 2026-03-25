# Guide de test Gradio (mode broker)

Ce guide explique comment tester BrokerFlow AI avec l'interface Gradio, comme un broker, et comment lire les resultats.

## Objectif

L'interface Gradio permet de:

1. charger un dossier JSON
2. scorer un dossier unique
3. lancer une suite de cas broker predefinis
4. visualiser la decision, le score et les alertes

Elle utilise le `TestClient` FastAPI en interne: pas besoin de lancer `uvicorn` pour tester.

## Prerequis

1. dependances installees (`make setup`)
2. environnement Python du projet actif

## Lancement

### Option A - Linux/macOS (avec make)

```bash
make run-gradio
```

### Option B - Windows PowerShell (sans make)

```powershell
./.venv/Scripts/python.exe -m src.ui.gradio_app
```


Si le venv est deja active:

```powershell
python -m src.ui.gradio_app
```

Puis ouvrir:

- `http://127.0.0.1:7860`

## Ce que tu vois dans l'UI

## 1) Endpoint

Choix entre:

- `/v1/score`
- `/v2/score`

Conseil: utiliser `/v2/score` pour la policy runtime la plus recente.

## 2) Broker test case

Cas predefinis:

- `clean_profile`
- `urgent_missing_docs`
- `employment_contradiction`
- `negation_history`
- `ambiguous_context`

Bouton `Load broker case`:

- remplit automatiquement le JSON dossier avec un scenario realiste

## 3) Application Payload JSON

- zone editable pour modifier manuellement un dossier
- utile pour tester des variantes (revenu, docs manquants, note libre, etc.)

## 4) Score payload

Quand tu cliques `Score payload`, tu obtiens:

- `Status`: succes/erreur
- `Quick Result Summary`:
  - recommendation
  - risk_score
  - risk_class
  - nombre d'alertes
- `Raw API Output`:
  - JSON complet de sortie API

## 5) Run full broker suite

Execute tous les cas broker en batch.

Tu obtiens:

- `Suite Status`
- `Broker Suite Results` (tableau):
  - `case`
  - `recommendation`
  - `risk_score`
  - `alerts_count`
  - `severity`
- `Broker Suite Raw Outputs`: JSON complet par cas

## Comment interpreter les resultats

## Dossier individuel

Verifier rapidement:

1. coherence entre `risk_score` et `recommendation`
2. presence d'alertes attendues (`alerts`, `alerts_structured`)
3. alignement du `summary` avec la recommendation
4. champs de decision (`decision_reason_codes`, `decision_alert_severity`, `decision_threshold`)

## Suite broker

Verifier globalement:

1. `clean_profile` ne doit pas escalader sans raison
2. `urgent_missing_docs` doit remonter des alertes documentaires
3. `employment_contradiction` doit detecter l'incoherence emploi/note
4. `negation_history` doit detecter la contradiction historique de paiement
5. `ambiguous_context` doit produire un signal d'ambiguite

## Checklist de validation rapide

1. L'UI s'ouvre sur `127.0.0.1:7860`
2. `Load broker case` remplit bien le JSON
3. `Score payload` renvoie un statut `Scoring completed.`
4. Le JSON brut contient `recommendation` et `risk_score`
5. `Run full broker suite` remplit le tableau batch

## Erreurs frequentes

## Erreur JSON

Symptome:

- `Invalid JSON input`

Action:

- verifier virgules, guillemets, accolades dans le payload

## Erreur de schema API (422)

Symptome:

- `Request failed (422)`

Action:

- verifier champs obligatoires du dossier (`application_id`, `customer_id`, `snapshot_date`, etc.)

## Pas de Gradio

Symptome:

- import gradio impossible

Action:

Linux/macOS:

```bash
make setup
```

Windows PowerShell:

```powershell
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

ou reinstall:

```bash
pip install gradio>=4.44.0
```

## Fichiers lies

- `src/ui/gradio_app.py`
- `README.md`
- `src/api/main.py`
- `src/api/routes/scoring.py`
