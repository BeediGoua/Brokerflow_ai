# Strategie d'evaluation des agents (BrokerFlow AI)

## 1. Objectif de ce document

Ce document explique la strategie d'evaluation des agents underwriting (note_parser, reviewer, summary_writer), les choix de design, la construction du dataset, et pourquoi nous avons commence avec 8 cas puis vise 30-50 cas.

Le but est d'avoir une evaluation:
1. credible pour un projet junior tres solide,
2. simple a expliquer en entretien,
3. reproductible localement.

## 2. Ce que l'on evalue exactement

Dans BrokerFlow AI, il y a 3 couches distinctes:
1. couche modele risque (ML tabulaire, calibree),
2. couche agents (texte, alertes, resume),
3. couche politique de decision (regles explicites).

Nous n'evaluons pas ces couches avec le meme dataset ni les memes metriques.

### 2.1 Evaluation modele risque

Deja couverte dans:
1. evaluation.md
2. docs/model_card.md

Jeu de donnees: tables processeds issues du challenge Zindi.
Metriques principales: ROC AUC, Brier, precision/recall/F1 selon seuil.

### 2.2 Evaluation agents

Couverte par:
1. data/agent_eval_cases.json
2. src/eval/evaluate_agents.py

Ici on evalue des sorties de type NLP/agent:
1. extraction de signaux dans la note,
2. generation d'alertes structurees,
3. coherence du resume final.

## 3. Pourquoi on ne peut pas utiliser uniquement le dataset modele brut

Question centrale: "est-ce qu'on utilise les vraies donnees brutes du modele pour evaluer les agents ?"

Reponse courte: pas directement pour tout.

Raison:
1. les jeux tabulaires processeds ne contiennent pas de free_text_note exploitable pour l'evaluation agent,
2. ils ne contiennent pas non plus une verite terrain pour expected_alerts_codes,
3. il n'existe pas de label natif "bonne alerte reviewer" ou "bon resume underwriting" dans ces fichiers.

Donc:
1. on utilise le dataset reel pour evaluer le modele risque,
2. on construit un benchmark annote dedie pour evaluer les agents.

Ce choix est standard en pratique: on separe prediction de risque (tabulaire) et evaluation de comportements agent (NLP + logique metier).

## 4. Construction du dataset agent

Fichier courant: data/agent_eval_cases.json

Chaque cas contient:
1. un payload application complet,
2. une note texte (free_text_note),
3. une liste de documents,
4. des attentes annotees:
   - expected_risk_signals
   - expected_alerts_codes
   - expected_recommendation

Le dataset initial couvre volontairement des profils differents:
1. dossier propre (eviter faux positifs),
2. urgence + retards,
3. contradictions note vs structure,
4. piece critique manquante,
5. negation contradictoire,
6. signal risque texte isole,
7. cas neutre,
8. cas mixte severe.

## 5. Pourquoi commencer avec 8 cas

8 cas est un choix MVP, pas un objectif final.

Justification:
1. valider rapidement le pipeline de bout en bout,
2. debloquer les tests unitaires/integration sans overengineering,
3. detecter vite les erreurs de schema, prompt, mapping et fallback,
4. garder un cout de maintenance faible au debut.

C'est suffisant pour:
1. verifier que les metriques tournent,
2. verifier que les cas critiques metier existent,
3. fournir une base demonstrable.

Ce n'est pas suffisant pour:
1. estimer une performance robuste en production,
2. conclure sur la generalisation.

## 6. Pourquoi viser 30-50 cas ensuite

Objectif recommande pour un projet portfolio serieux: 30-50 cas annotees de qualite.

Pourquoi cette plage:
1. assez de diversite pour couvrir les familles d'erreurs,
2. encore gerable manuellement par une petite equipe,
3. bonne taille pour suivre des regressions entre versions de prompts/modeles,
4. compatible avec un cycle rapide d'amelioration.

Repartition conseillee:
1. 40% cas standards (distribution metier normale),
2. 40% cas "hard" (contradictions fines, negations, documents partiels),
3. 20% cas adversariaux (ambiguite, formulations pieges, bruit lexical).

Oui, cette repartition vise explicitement les synonymes et les contextes ambigus.

Exemples a inclure dans le lot 30-50 cas:
1. Synonymes/metaphrases ("retards", "impayes", "echeances manquees" -> late_payments).
2. Formulations attenuees ou implicites ("situation tendue", "besoin rapide", "cash-flow serre" -> urgence potentielle).
3. Negations et doubles negations ("pas de retard", "pas impossible qu'il y ait eu un incident").
4. Contradictions contextuelles (note rassurante mais champs structures risqués).
5. Ambiguite documentaire (note mentionne "dossier complet" alors qu'une piece requise est absente).

Mini-cible pratique dans 50 cas:
1. 12-15 cas avec synonymes/variantes lexicales,
2. 10-12 cas ambiguite contextuelle,
3. 8-10 cas negations/contradictions fines,
4. le reste en cas standards pour conserver la representativite metier.

## 7. Metriques choisies et pourquoi

Implementation actuelle dans src/eval/evaluate_agents.py.

### 7.1 Parser

Metriques:
1. parser_precision
2. parser_recall
3. parser_f1

Pourquoi:
1. c'est un probleme d'extraction binaire/multilabel,
2. precision/recall/F1 sont lisibles et actionnables.

### 7.2 Reviewer

Metriques:
1. alert_precision
2. alert_recall
3. alert_f1
4. json_validity_rate

Pourquoi:
1. mesurer la qualite fonctionnelle des alertes (bons codes),
2. mesurer la fiabilite format (sortie structuree valide).

### 7.3 Summary writer

Metrique:
1. summary_coherence

Definition actuelle:
1. la recommendation attendue apparait dans le resume.

Pourquoi:
1. verifier rapidement que le narratif ne contredit pas la decision.

### 7.4 Latence

Metriques:
1. latency_p50_ms
2. latency_p95_ms

Pourquoi:
1. p50 pour la tendance centrale,
2. p95 pour la queue (experience utilisateur et robustesse API).

### 7.5 Fallback

Metrique exposee actuellement:
1. fallback_rate (placeholder a 0.0)

Statut:
1. la metrique existe deja dans le contrat,
2. le comptage runtime fin doit encore etre branche (prochaine iteration).

## 8. Alignement avec bonnes pratiques externes

Les choix ci-dessus suivent des references reconnues:

1. Scikit-learn model evaluation:
   - distinguer prediction probabiliste et decision de seuil,
   - utiliser plusieurs metriques selon l'objectif metier,
   - analyser precision/recall/F1 et calibration.

2. Scikit-learn calibration:
   - Brier/log loss utiles pour probabilites,
   - calibration a evaluer explicitement pour des decisions par seuil.

3. LLM-as-judge / agent eval (syntheses de litterature):
   - privilegier sorties binaires/structurees quand possible,
   - mesurer precision/recall plutot que correlation seule,
   - garder un benchmark annote stable pour comparer les versions,
   - rester prudent: un evaluateur LLM seul ne remplace pas un protocole clair.

4. Gouvernance du risque (NIST AI RMF):
   - separer mesure, gestion et gouvernance,
   - documenter hypotheses, limites, et controles.

## 9. Limites actuelles assumees

1. Dataset agent encore petit (8 cas).
2. Annotation encore mono-source (pas encore accord inter-annotateurs).
3. summary_coherence encore simple (string-based) et non semantique.
4. fallback_rate pas encore alimente par un vrai compteur de production.

## 10. Plan d'amelioration concret (prochaine phase)

1. Etendre le benchmark a 30-50 cas avec priorite hard/adversarial.
2. Ajouter un guide d'annotation court (1 page) pour stabiliser les labels.
3. Ajouter une double annotation sur un sous-ensemble et mesurer accord (ex: Cohen kappa).
4. Instrumenter fallback_rate par agent (parser/reviewer/summary).
5. Ajouter un rapport comparatif baseline deterministic vs mode LLM active.
6. Completer un notebook de visualisation des metriques (distribution erreurs, confusion par code alerte).

## 11. Conclusion

La strategie actuelle est volontairement pragmatique:
1. evaluation modele sur donnees reelles tabulaires,
2. evaluation agents sur benchmark annote dedie,
3. separation claire prediction vs decision vs narration.

C'est une base saine pour un projet "simple, clair, defendable" en entretien.
La priorite n'est pas de grossir vite, mais de rendre l'evaluation plus robuste de maniere incrementalement testable.

## 12. References externes utiles

1. Scikit-learn, Metrics and scoring:
   https://scikit-learn.org/stable/modules/model_evaluation.html
2. Scikit-learn, Probability calibration:
   https://scikit-learn.org/stable/modules/calibration.html
3. NIST AI Risk Management Framework:
   https://www.nist.gov/itl/ai-risk-management-framework
4. Eugene Yan, Evaluating the Effectiveness of LLM-Evaluators:
   https://eugeneyan.com/writing/llm-evaluators/
