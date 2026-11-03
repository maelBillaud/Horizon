# POC newsletter matinale (fork de Horizon)

Ce dossier se copie à la racine de ton fork public de `Thysrael/Horizon`.

## Contenu
- `data/config.newsletter.json` : IA (Gemini), flux, seuils, quotas par thème (politique gauche/centre/droite 2+2+2, sport, IA et technologies 5 chacun).
- `profiles-fr/` : 4 profils éditoriaux en français (politique-fr, sport, ia, tech). Un seul bloc de sortie : un court paragraphe de résumé, sans recherche web (économise les appels IA).
- `.github/workflows/nightly-newsletter.yml` : exécution à 02:00 UTC, publication sur la branche `gh-pages` à partir de `newsletter-site/`.
- `newsletter-site/` : site Jekyll de la revue (accueil et configuration). Les éditions du jour y sont copiées au moment de la publication.
- `tools/` : `discover_feeds.py`, `check_feeds.py`, `validate_poc.py`, `test_offline.py` (Python standard, sans installation).

## Mise en route
1. Forker `Thysrael/Horizon` depuis ton GitHub (dépôt public, lien conservé avec l'officiel), puis copier ce dossier dedans. Aucun fichier d'origine n'est écrasé : la config et les profils ont des noms propres.
2. Le workflow `daily-summary.yml` d'origine est livré désactivé (`.disabled`), tout comme `deploy-docs.yml` d'origine, qui publierait la doc du projet sur `gh-pages`.
3. Créer une clé sur https://aistudio.google.com/api-keys, puis dans Settings > Secrets and variables > Actions : secret `GOOGLE_API_KEY`. Le modèle est fixé dans `data/config.newsletter.json` (`ai.model`). Ses quotas gratuits s'affichent dans https://aistudio.google.com/rate-limit.
4. Settings > Actions > General : autoriser les workflows avec l'option « Allow actions created by GitHub » (le workflow n'utilise que `actions/checkout` et `actions/setup-python`). Après la première publication (la branche `gh-pages` est créée par le workflow), Settings > Pages : source « Deploy from a branch », branche `gh-pages`, dossier `/ (root)`.
5. En local (ou Codespaces) : trouver et valider les flux restants.
   ```
   python tools/discover_feeds.py --apply
   python tools/check_feeds.py --all --enable-ok
   python tools/validate_poc.py
   python -m unittest tools/test_offline.py
   ```
6. Tests de Horizon sur les profils : `uv run pytest tests/test_profiles.py tests/test_prompting.py -q`
7. Premier essai : `GOOGLE_API_KEY=... uv run horizon --config data/config.newsletter.json --hours 24`, puis lancer le workflow à la main (Actions > Newsletter de nuit > Run workflow).

## À vérifier au premier essai
- Le nombre d'appels IA (environ 1 par article collecté sur 24 h) et les tokens consommés, face aux quotas gratuits affichés dans AI Studio.
- Le comportement quand un quota gratuit est atteint en cours de route.
- Le flux `Ouest-France - Sport` (127 articles par jour) est désactivé pour ménager les quotas.
- Le Point, Eurosport et Anthropic n'ont pas de flux exploitable (Le Point bloque les accès automatisés).

## Monter de version de Horizon
1. Noter le commit actuel (`git rev-parse HEAD`) et travailler sur une branche de test.
2. Récupérer l'officiel : bouton « Sync fork » ou `git fetch upstream && git merge upstream/main`.
3. Lire ce qui a changé côté docs et profils : `git diff <ancien>..upstream/main -- docs/configuration.md docs/profiles.md profiles/`.
4. Relancer `python tools/validate_poc.py`, les tests `pytest` des profils et un essai `uv run horizon --config data/config.newsletter.json --hours 24`.
5. Fusionner dans la branche principale seulement si tout passe ; sinon rester sur l'ancien commit.

Le workflow `deploy-docs.yml` d'origine est désactivé : la publication de la revue passe uniquement par `gh-pages` et `newsletter-site/`, pour éviter tout conflit avec la doc du projet.
