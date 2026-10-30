# POC newsletter matinale (fork de Horizon)

Ce dossier se copie à la racine de ton fork public de `Thysrael/Horizon`.

## Contenu
- `data/config.newsletter.json` : IA, flux, seuils, quotas par thème (politique gauche/centre/droite 2+2+2, sport, IA et technologies 5 chacun).
- `profiles-fr/` : 4 profils éditoriaux en français (politique-fr, sport, ia, tech). Un seul bloc de sortie : un court paragraphe de résumé, sans recherche web (économise les appels IA).
- `.github/workflows/nightly-newsletter.yml` : exécution à 02:00 UTC, publication dans `docs/`.
- `tools/` : `discover_feeds.py`, `check_feeds.py`, `validate_poc.py`, `test_offline.py` (Python standard, sans installation).

## Mise en route
1. Forker `Thysrael/Horizon` depuis ton GitHub (dépôt public, lien conservé avec l'officiel), puis copier ce dossier dedans. Aucun fichier d'origine n'est écrasé : la config et les profils ont des noms propres.
2. Désactiver ou supprimer le workflow `daily-summary.yml` d'origine pour éviter un double lancement.
3. Dans Settings > Secrets and variables > Actions :
   - Secret `HORIZON_AI_KEY` : ta clé API ;
   - Variables `HORIZON_AI_BASE_URL` (point d'accès compatible OpenAI du fournisseur) et `HORIZON_AI_MODEL` (nom exact du modèle, à lire dans la console du fournisseur).
4. Settings > Pages : source « Deploy from a branch », branche `main`, dossier `/docs`.
5. En local (ou Codespaces) : trouver et valider les flux restants.
   ```
   python tools/discover_feeds.py --apply
   python tools/check_feeds.py --all --enable-ok
   python tools/validate_poc.py
   python -m unittest tools/test_offline.py
   ```
6. Tests de Horizon sur les profils : `uv run pytest tests/test_profiles.py tests/test_prompting.py -q`
7. Premier essai : `uv run horizon --config data/config.newsletter.json --hours 24` avec les 3 variables d'environnement, puis lancer le workflow à la main (Actions > Newsletter de nuit > Run workflow).

## À vérifier au premier essai (non confirmé par la doc)
- Le français : `ai.languages: ["fr"]` et `display_names.fr` sont-ils acceptés ? Sinon passer à `["en"]` et garder les consignes de rédaction en français des profils.
- Le nombre d'appels IA et les tokens consommés, pour le calcul des quotas gratuits.
- Le comportement quand un quota gratuit est atteint en cours de route.
- Les pages `page` de `tools/media.json` sont à corriger si une adresse répond 404.

## Monter de version de Horizon
1. Noter le commit actuel (`git rev-parse HEAD`) et travailler sur une branche de test.
2. Récupérer l'officiel : bouton « Sync fork » ou `git fetch upstream && git merge upstream/main`.
3. Lire ce qui a changé côté docs et profils : `git diff <ancien>..upstream/main -- docs/configuration.md docs/profiles.md profiles/`.
4. Relancer `python tools/validate_poc.py`, les tests `pytest` des profils et un essai `uv run horizon --config data/config.newsletter.json --hours 24`.
5. Fusionner dans la branche principale seulement si tout passe ; sinon rester sur l'ancien commit.

À vérifier au premier essai : `profiles_dir` est lu depuis la racine du dépôt (sinon adapter le chemin), et la publication dans `docs/` peut créer des conflits si l'officiel y committe aussi ses pages (dans ce cas, publier sur une branche `gh-pages` séparée).
