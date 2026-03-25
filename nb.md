Audit publication publique - BrokerFlow AI

Statut reel du repo
- Le code source critique existe bien, y compris src/models/.
- Le manque visible cote GitHub venait surtout des artefacts ignores par .gitignore.

Cause racine
- .gitignore ignorait globalement:
  - data/processed/
  - models/
  - *.pkl / *.pickle
- Donc les resultats importants (CSV/JSON/TXT) n'etaient pas visibles publiquement.

Corrections appliquees
1) .gitignore ajuste
- data/processed/ et models/ restent geres proprement.
- Les artefacts publics legers sont autorises:
  - data/processed/*.csv
  - models/*.csv
  - models/*.json
  - models/*.txt
- Les binaires lourds restent ignores:
  - models/*.pkl
  - models/*.pickle

2) Artefacts publics generes localement
- models/raw_baselines_metrics.csv
- models/challenger_metrics.csv
- models/challenger_winner.json
- models/best_threshold.txt
- models/model_coefficients.csv
- models/logreg_raw_runtime_manifest.json
- data/processed/history_features.csv
- data/processed/train_enriched.csv
- data/processed/train_features.csv
- data/processed/test_enriched.csv
- data/processed/test_features.csv

3) README complete
- Section "Artefacts publics versionnes" ajoutee.
- Section "Regeneration locale" ajoutee.

Impact
- Un visiteur externe peut voir les metriques, le winner challenger, le seuil, les tables processed et le manifeste runtime.
- Le repo reste leger car les binaires de modele ne sont pas commits.

Etape finale a faire
- Commit + push pour publier les changements sur GitHub.
