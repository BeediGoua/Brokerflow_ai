# Strategie Agents pour BrokerFlow AI (Ollama + smolagents + requests)



---

## 1. Objectif produit dans notre cas

BrokerFlow AI est un copilote underwriting.

Le systeme doit aider un broker a:
1. comprendre rapidement le niveau de risque d'un dossier,
2. detecter les incoherences du dossier,
3. identifier les pieces manquantes,
4. recevoir une recommandation claire et justifiee.

Important: les agents ne remplacent pas le modele de risque. Ils ajoutent du contexte et de la clarte autour de la sortie du modele.

---

## 3. Principe d'architecture

Nous separons les responsabilites en trois couches:

1. Couche risque deterministe
- feature engineering,
- modele ML calibre,
- politique de seuil.

2. Couche agents
- parser la note texte,
- verifier la coherence entre donnees, note et documents,
- produire un resume lisible.

3. Couche decision
- combiner score modele + completude + alertes,
- sortir une recommandation (`ACCEPTABLE`, `REVIEW`, `REQUEST_DOCUMENTS`, `ESCALATE`).

Pourquoi ce design est solide:
- le modele reste auditable et stable,
- les sorties des agents sont utiles mais bornees,
- la politique de decision reste explicite et testable.

### Hierarchie de verite (explicite)

En cas de conflit entre signaux, l'ordre de confiance est strict:
1. donnees structurees validees,
2. politique deterministe et regles metier dures,
3. completude documentaire et checks documents,
4. signaux texte issus du parser LLM,
5. resume narratif.

Interpretation:
- les signaux texte peuvent enrichir, mais ne peuvent pas ecraser les faits structures valides,
- le resume est uniquement une couche de presentation, sans autorite de decision.

---

## 4. Choix techniques et pourquoi

### Ollama (runtime LLM local)
Pourquoi:
- inference locale,
- faible cout infra,
- pas de dependance API externe,
- demos reproductibles en entretien.

Modele leger recommande pour ce projet:
- `qwen2.5:3b-instruct` (defaut)

Alternatives:
- `phi3:mini`
- `llama3.2:3b`
- `gemma2:2b`

### smolagents (orchestration)
Pourquoi:
- decomposition claire des roles agents,
- orchestration legere,
- evolution plus simple qu'un unique prompt monolithique.

Note de perimetre importante:
- smolagents est utilise pour du routage/orchestration legere, pas pour du planning autonome complexe.

### requests (client HTTP)
Pourquoi:
- appels API simples et explicites,
- controle facile des timeouts/retries,
- logging et debug faciles.

---

## 5. Catalogue d'agents pour ce projet

Nous gardons exactement 3 agents coeur dans le MVP actuel.

## 5.1 Agent A: note_parser

But:
- transformer `free_text_note` en signaux structures.

Entree:
- texte brut de la note.

Contrat de sortie (format cible):
```json
{
  "risk_signals": ["late_payments", "urgent_need"],
  "document_signals": ["missing_documents"],
  "stability_signals": ["stable_job"],
  "context_tags": ["travel", "seasonal_income"],
  "ambiguities": []
}
```

Ce qu'il doit faire:
- detecter des indices textuels clairs,
- normaliser le wording en labels controles,
- retourner du JSON uniquement.

Ce qu'il ne doit pas faire:
- predire le risque global,
- inventer des faits,
- ecraser la sortie du modele.

Valeur metier:
- convertit du texte non structure en evidence exploitable par le systeme.

## 5.2 Agent B: reviewer

But:
- croiser les donnees structurees, les signaux texte et l'etat documentaire.

Entree:
- champs application,
- sortie note_parser,
- liste des documents et leurs statuts.

Contrat de sortie:
```json
[
  {
    "code": "DOC_REQUIRED_MISSING",
    "severity": "high",
    "message": "Missing required document: income_proof",
    "source": "documents",
    "confidence": 0.95
  }
]
```

Ce qu'il doit faire:
- detecter les contradictions,
- detecter les pieces critiques manquantes,
- produire des alertes concises, tracables et actionnables.

Ce qu'il ne doit pas faire:
- recalculer le score de risque,
- rendre directement la decision finale d'underwriting,
- produire des alertes vagues ou non actionnables.

Valeur metier:
- c'est la valeur copilot principale pour les underwriters.

## 5.3 Agent C: summary_writer

But:
- convertir une sortie technique en explication lisible pour un underwriter.

Entree:
- score, classe, top facteurs, alertes, recommandation finale.

Sortie:
- resume narratif court pour UI/API broker.

Ce qu'il doit faire:
- expliquer le niveau de risque,
- mettre en avant les facteurs principaux,
- mentionner les blocages majeurs,
- rester aligne avec la decision finale.

Discipline de sortie:
- summary_writer peut compresser/prioriser des faits existants, mais ne doit jamais enrichir avec de nouveaux faits.

Ce qu'il ne doit pas faire:
- contredire la policy,
- introduire des assertions non supportees,
- changer la recommandation.

Valeur metier:
- communication de decision plus rapide et plus fiable.

---

## 6. Flux bout-en-bout dans notre cas underwriting

1. L'API recoit le payload application.
2. Le modele calcule score calibre et classe de risque.
3. note_parser extrait les signaux texte.
4. reviewer genere des alertes structurees.
5. la policy combine score + completude + severite alertes.
6. summary_writer produit la rationale lisible.
7. l'API retourne le payload final de decision.

Le payload final inclut:
- `risk_score`
- `risk_class`
- `top_factors`
- `alerts`
- `alerts_structured`
- `recommendation`
- `decision_reason_codes`
- `summary`

### Politique de gestion des conflits

Quand des evidences se contredisent:
1. la policy dure et les donnees structurees validees prevalent sur le texte,
2. des trous documentaires severes peuvent degrader la recommandation meme avec un score modere,
3. les alertes texte seules et faible confiance restent informatives sauf corroboration,
4. les alertes de contradiction augmentent la pression de revue sans recalculer le score modele.

Guide de severite:
- low: incoherence informative sans blocage immediat,
- medium: incoherence materielle necessitant revue manuelle,
- high: contradiction severe ou piece critique manquante necessitant escalation.

### Taxonomie d'alertes

Les namespaces d'alertes sont explicites et stables:
- `RISK_*`: signaux comportementaux/credit lies au risque,
- `DOC_*`: piece requise manquante ou invalide,
- `INC_*`: contradiction entre sources,
- `AMB_*`: ambiguite ou manque de clarte dans les evidences textuelles.

---

## 7. Garde-fous operationnels (obligatoires)

Pour chaque appel LLM:
- timeout: 8-12s
- retry: max 1-2 tentatives
- temperature basse (0.1 a 0.3)
- instruction JSON stricte
- validation de schema avant usage
- fallback deterministe si sortie invalide

Politique de fallback:
- si parser echoue -> structure vide de signaux
- si reviewer echoue -> checks deterministes minimaux
- si summary echoue -> template de resume fixe
- si Ollama indisponible -> continuer avec modele + policy deterministe uniquement

Pourquoi:
- garde l'API stable,
- evite que le bruit LLM casse le scoring,
- ameliore la fiabilite sous charge.

Exigence de fiabilite forte:
- le systeme doit rester fonctionnel meme avec zero disponibilite agent.

---

## 8. Regles de prompting

Principes de system prompt:
- role etroit et explicite,
- aucune autorite cachee de decision,
- sortie JSON uniquement quand requise,
- taxonomie de severite fixe (`low`, `medium`, `high`),
- taxonomie de codes d'alerte fixe.

Versioning des prompts:
- garder des versions explicites (`v1`, `v2`) en code/config,
- logger la version de prompt avec les metadonnees de reponse.

Contrat de versioning:
- `note_parser_prompt_vX`
- `reviewer_prompt_vX`
- `summary_prompt_vX`
- `alert_taxonomy_vX`

Pourquoi:
- reproductibilite,
- debug plus simple,
- suivi d'experiences propre.

### Politique anti-hallucination

Regles non negociables:
- toute assertion LLM non supportee doit etre rejetee ou ignoree,
- l'omission est preferee a la fabrication,
- les agents ne peuvent pas introduire de nouveaux faits absents des entrees,
- toute sortie hors schema ou hors contraintes d'evidence declenche retry/fallback.

Securite de decision:
- la recommandation finale ne peut jamais etre modifiee par du texte libre non valide.

---

## 9. Plan qualite et evaluation

Les agents sont evalues sur un mini-benchmark annote (30-50 cas).

Metriques:
- taux de validite JSON,
- precision/rappel des alertes vs attendus,
- coherence du summary avec la recommandation,
- latence p50 et p95,
- taux de fallback.

Cibles d'acceptation pour qualite portfolio:
- validite JSON >= 99%
- precision reviewer >= 0.80 sur jeu annote
- latence p95 cible < 2.5s par appel agent (ideal), acceptable < 5s selon hardware
- aucune contradiction policy dans le summary

### Composition du set d'evaluation (obligatoire)

Les 30-50 cas annotes doivent inclure:
- dossiers simples et propres,
- dossiers contradictoires (mismatch structure vs note),
- dossiers avec pieces critiques manquantes,
- notes bruites ou contexte non pertinent,
- ambiguite de formulation et cas de negation,
- pieges de faux positifs pour extraction mots-cles,
- cas mixtes pour robustesse de ranking de severite.

### Contrat de logging d'execution agent

Chaque execution agent doit enregistrer:
- request id,
- nom de l'agent,
- nom du modele,
- version du prompt,
- latence,
- sortie brute,
- statut de validation schema,
- fallback utilise (oui/non) et raison.

Cela garantit auditabilite et post-mortem exploitables.

---

## 10.

1. Separation claire des responsabilites
- le modele predit, les agents expliquent/verifient.

2. Couche policy deterministe
- logique de recommandation explicite, comportement auditable.

3. Stack legere et pragmatique
- Ollama + petit modele + appels HTTP simples.

4. Culture fiabilite
- retries, timeouts, validation, fallbacks.

5. Qualite mesuree
- benchmark et metriques, pas seulement des captures de demo.

6. Posture risque controlee
- politique de contradiction explicite + rejet des hallucinations.

---

## 11. 

Phase 1: fondations
1. Ajouter un client Ollama avec `requests`.
2. Ajouter les settings modele/config.
3. Ajouter des validateurs de schemas JSON.

Phase 2: upgrade agents
1. Faire evoluer `note_parser` vers une sortie categorisee.
2. Etendre les regles reviewer et la taxonomie d'alertes.
3. Garder summary writer concis et deterministe.

Phase 3: integration API
1. Injecter les metadonnees documentaires dans les routes review/scoring.
2. Cablage complet des fallbacks.
3. Ajouter le logging statut agent + timings.

Phase 4: evaluation
1. Construire les cas annotes.
2. Ajouter un script d'evaluation.
3. Publier les metriques dans la doc.

Phase 5: preuve comparative
1. Ajouter un pipeline baseline deterministe sans LLM.
2. Comparer baseline vs mode assiste LLM.
3. Publier le delta before/after (qualite, coherence, latence, taux fallback).

---

## 12. Non-objectifs

Nous ne cherchons pas a:
- laisser le LLM prendre seul la decision credit,
- entrainer un grand modele de langage custom,
- maximiser la creativite des resumes.

Nous cherchons a:
- livrer une assistance underwriting robuste,
- garder un comportement explicable,
- rester legers et maintenables.

### Pourquoi pas du underwriting LLM-only

Nous evitons volontairement le decisioning LLM-only car cela degrade:
- l'auditabilite,
- le determinisme,
- la reproductibilite sur les edge-cases,
- la gouvernance et le controle du risque metier.

Le LLM est un assistant autour de la decision, pas le moteur de decision.

### Compromis de design (explicites)

Compromis assumes dans ce projet:
- interpretabilite priorisee sur autonomie maximale,
- controle deterministe priorise sur generation ouverte,
- efficacite cout local priorisee sur capacite modele maximale,
- robustesse des fallbacks priorisee sur richesse de features.

---

## 13. Positionnement final

Dans BrokerFlow AI, les agents sont des assistants autour du scoring risque, pas des remplacements du scoring.

Ce design est volontairement simple, fiable et orientee production:
- ML calibre pour la probabilite,
- policy reglee pour la recommandation,
- agents legers pour extraction de contexte, checks de coherence et explication lisible.

C'est le bon compromis pour un portfolio junior fort: pratique, propre et techniquement defensible.

---

## 14. Alignement explicite avec le plan d'execution en 10 etapes



1. Definir un scope agentique minimal
- Garder seulement 3 agents:
  - note parser,
  - consistency reviewer,
  - summary writer.
- Aucun agent ne predit le risque: le risque reste porte par le ML tabulaire.

2. Selectionner un modele Ollama local leger
- Commencer avec un modele par defaut: qwen2.5:3b-instruct.
- Alternatives:
  - phi3:mini
  - llama3.2:3b
  - gemma2:2b
- Objectif: faible latence, memoire raisonnable, comportement stable.

3. Installer et smoke-test Ollama

```bash
ollama pull qwen2.5:3b-instruct
ollama run qwen2.5:3b-instruct "Respond in strict JSON"
```

Si cela marche, l'integration HTTP peut commencer.

4. Appeler Ollama avec requests (sans abstraction inutile)
- Construire un client Python unique avec:
  - timeout,
  - retries,
  - gestion stricte de sortie JSON.
- Endpoint typique: POST /api/chat.
- Contraintes runtime:
  - temperature basse (0.1 a 0.3),
  - contraintes de sortie JSON,
  - budget tokens limite.

5. Utiliser smolagents pour orchestrer, pas pour faire de la magie
- Responsabilites smolagents:
  - router vers le bon agent,
  - injecter system prompt + schema de sortie,
  - enchainer parser -> reviewer -> summary.
- Responsabilites application:
  - valider les sorties,
  - rejeter les sorties mal formees,
  - appliquer fallback deterministe en cas d'erreur LLM.

6. Imposer des schemas de sortie stricts
- schema note_parser: signaux booleens + tags.
- schema reviewer: liste d'alertes avec code/severity/source/confidence.
- schema summary_writer: un paragraphe concis + max 3 raisons.
- Si JSON invalide:
  - retry une fois,
  - puis fallback local deterministe.

7. Ajouter des garde-fous production
- Timeout par appel: 8 a 12 secondes.
- Retry budget: 1 a 2 tentatives.
- Comportement circuit-breaker si Ollama indisponible.
- Logging propre entree/sortie sans fuite de donnees sensibles.
- Prompt versioning (v1, v2) pour la tracabilite.

8. Construire un set d'evaluation simple mais solide
- Creer 30 a 50 cas underwriting annotes.
- Suivre:
  - taux de validite JSON,
  - precision des alertes reviewer,
  - coherence summary vs recommandation,
  - latence p50/p95.
- C'est le principal differenciateur pour la qualite portfolio.

9. Integrer progressivement dans l'API existante
- Ordre recommande:
  - remplacer note_parser actuel par version LLM + fallback,
  - garder reviewer deterministe comme source de verite,
  - utiliser summary LLM surtout pour reformulation,
  - ne jamais autoriser une decision ACCEPTABLE/ESCALATE LLM-only.

10. Preparer un storytelling portfolio fort
- Dans README/demo, montrer:
  - pourquoi un modele local leger,
  - limites connues,
  - metriques avant/apres,
  - profil cout/latence,
  - architecture et garde-fous.
- Cela demontre maturite produit et discipline engineering.

---

## 15. Baseline deterministe et evaluation comparative

Pour prouver la valeur agents, nous maintenons une baseline explicite sans LLM:
- baseline parser: keywords/regles uniquement,
- baseline reviewer: checks deterministes uniquement,
- baseline summary: template fixe uniquement.

Puis comparaison baseline vs mode assiste LLM sur le meme jeu annote:
- reduction des alertes manquees,
- impact precision,
- coherence summary,
- surcout latence/cout,
- frequence de fallback.

Regle de positionnement:
- si le mode assiste LLM n'ameliore pas des resultats mesurables, la baseline reste le mode par defaut.

---

## 16. Profil hardware de reference

Pour rendre les claims locaux reproductibles, documenter au moins une config de reference:
- modele CPU et nombre de coeurs,
- taille RAM,
- usage GPU ou non,
- temps de chargement modele,
- latence moyenne et p95 sur le benchmark.

Cela rend le claim "lightweight local" testable et defensible en entretien.
