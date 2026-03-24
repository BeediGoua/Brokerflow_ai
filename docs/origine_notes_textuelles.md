# Origine des notes textuelles synthetiques

Ce document explique d'ou viennent les notes textuelles du projet, pourquoi elles ont ete ajoutees, et comment les presenter de maniere honnete et credible.

## 1. Point de depart

Contexte: le projet s'appuie sur le dataset Zindi Loan Default Prediction.

Dans la donnee d'origine, on retrouve surtout:

- des variables demographiques
- le pret courant
- l'historique des prets precedents

La donnee de depart est donc structuree. Il n'y a pas de texte libre du type:

- email client
- commentaire analyste
- note courtier
- motif redige en langage naturel

Point cle: le texte n'existait pas deja dans la data.

## 2. Pourquoi ajouter du texte

Le projet ne cherche pas seulement a predire un risque de defaut. Il vise aussi a construire un underwriting copilot capable de:

- revoir un dossier
- detecter des incoherences
- generer une synthese
- tester des agents

Pour tester des agents, une couche textuelle est necessaire. Un agent de parsing ou de summarization n'a pas beaucoup d'interet si toutes les donnees sont purement numeriques.

Le texte a donc ete ajoute pour simuler le type de commentaires ou de contexte qu'un analyste ou un client pourrait reellement laisser dans un dossier.

## 3. Le texte n'a pas ete invente au hasard

Les phrases n'ont pas ete ecrites aleatoirement pour remplir une colonne. Elles ont ete generees selon trois principes:

1. s'appuyer sur les variables reelles de la data
2. utiliser des signaux underwriting plausibles
3. produire un texte utile pour les agents du projet

## 4. Base 1: traduction des signaux structures

Les donnees structurees contiennent deja des signaux importants. L'idee est de les transformer en phrases courtes et lisibles.

Exemple:

- si un client presente plusieurs retards ou un historique degrade, on peut generer: multiple late payments, recent default
- si le client semble plus stable, on peut generer: previous loans paid, stable job, steady income

La logique est la suivante:

1. lire les variables structurees
2. reperer les signaux metier importants
3. les reformuler en petites phrases

Le texte est donc une traduction simple du signal metier, pas une invention deconnectee du dossier.

## 5. Base 2: utilisation de signaux underwriting realistes

Dans un vrai dossier de credit, on retrouve souvent des themes comme:

- besoin urgent
- stabilite du revenu
- documents manquants
- emploi stable
- retards passes
- besoin d'approbation rapide

Le projet reutilise donc des expressions plausibles comme:

- urgent need
- missing documents
- needs fast approval
- stable job
- steady income

Ces phrases ne cherchent pas a faire du texte litteraire. Elles servent a representer des themes concrets d'analyse de dossier:

- situation financiere
- urgence
- qualite du dossier
- stabilite
- risque

Le texte ajoute est fonctionnel et oriente produit.

## 6. Base 3: soutien aux agents

Les agents du projet ont besoin de texte pour etre utiles.

Exemples:

- Agent 1, Note Parser: repere l'urgence, l'instabilite, les mentions de documents et les signaux de risque
- Agent 2, Reviewer: compare ce que dit le texte avec ce que disent les donnees structurees
- Agent 3, Summary Writer: produit une synthese lisible a partir du score, des facteurs, des alertes et du contexte texte

Le texte a donc ete ajoute pour servir a des usages precis:

- parser
- comparer
- resumer

Il soutient la logique produit au lieu de servir de simple decoration.

## 7. Pourquoi inclure des mentions comme Booking.com

Dans la vraie vie, un texte client n'est pas toujours propre ni uniquement financier. Il peut contenir du bruit ou du contexte annexe.

Des phrases comme:

- travel booking via Booking.com
- hotel booked on Booking.com

servent a tester la robustesse du parser sur un texte plus realiste.

L'objectif est double:

1. reconnaitre qu'il existe un contexte externe
2. ne pas confondre ce contexte avec un signal principal de risque

Booking.com est donc surtout un element de test pour verifier qu'un parser NLP reste robuste face a un texte mixte.

## 8. Methode simple et reproductible

La construction des notes textuelles repose sur une methode legere.

### Etape 1

Definir une petite liste de phrases candidates, par exemple:

- urgent need
- steady income
- previous loans paid
- missing documents
- multiple late payments
- recent default
- stable job
- needs fast approval
- travel booking via Booking.com

### Etape 2

Pour chaque dossier, choisir quelques phrases pertinentes, en general 1 a 3, afin de donner du contexte sans surcharger la note.

### Etape 3

Assembler ces phrases dans la variable free_text_note.

Exemples:

- urgent need; multiple late payments
- stable job; previous loans paid
- travel booking via Booking.com; needs fast approval

### Etape 4

Les agents exploitent ensuite cette note:

- le parser extrait des signaux
- le reviewer compare avec les donnees structurees
- le summary writer genere une synthese lisible

Techniquement, on reste sur une approche simple:

- une liste de motifs
- un assemblage controle
- une exploitation par les agents

## 9. Pourquoi cette approche reste credible

Le texte n'est pas observe dans la vraie data, mais l'approche reste credible pour trois raisons:

1. le caractere synthetique est annonce clairement
2. le contenu reste coherent avec le probleme metier
3. le texte sert a tester une vraie brique produit

La bonne formulation est donc la suivante:

> Le dataset Zindi ne contient pas de texte. Nous avons ajoute une couche textuelle synthetique, basee sur les signaux structures et sur des scenarios underwriting plausibles, afin de tester les agents et la logique de revue.

## 10. Ce qu'il ne faut pas dire

Il ne faut pas affirmer que:

- les notes existaient deja
- ce sont de vraies notes client
- le dataset contenait deja des commentaires

Ce serait faux.

Il faut dire que:

- le texte a ete cree
- il est synthetique
- il est inspire des variables reelles et du besoin produit

## 11. Resume simple

Le texte:

- n'existait pas dans la data Zindi
- a ete cree volontairement
- a ete construit a partir de signaux reels du dataset
- utilise des themes underwriting plausibles
- sert a tester les agents et la synthese
- inclut parfois du contexte externe comme Booking.com pour tester la robustesse NLP

## 12. Version entretien

Formulation courte et forte:

> Le dataset d'origine etait uniquement tabulaire. Comme je voulais construire un copilot underwriting avec une couche agents, j'ai ajoute des notes textuelles synthetiques. Je les ai generees a partir des signaux presents dans la data, comme l'historique de retards, la stabilite ou le besoin d'urgence, afin d'avoir un texte coherent avec le dossier. J'ai aussi injecte quelques elements de contexte non financiers, comme Booking.com, pour tester la robustesse du parser face a un texte plus realiste.
