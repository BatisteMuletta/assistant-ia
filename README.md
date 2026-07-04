# Assistant personnel IA

Projet personnel d'apprentissage : construction d'un assistant IA (Claude) intégré à mon quotidien,
sur Ubuntu Linux, en apprenant en profondeur les briques techniques utilisées (API, agents, Skills, MCP...).

## Sous-projets

1. **Dashboard personnel intelligent** — page d'accueil Chrome centralisant Gmail, Calendrier, tâches, notes et Claude
2. **Gestionnaire de fichiers intelligent** — rangement automatique avec validation stricte et confidentialité
3. **Assistant de cours automatique** — enregistrement, transcription (Whisper local) et résumé (API Anthropic)

## Stack technique

- Python / Bash / HTML-CSS-JS
- API Anthropic (SDK officiel)
- Whisper en local (transcription)
- OAuth Google (Gmail + Calendar)
- Stockage : JSON + Markdown locaux

## Documentation

- [`cahier_des_charges.md`](./cahier_des_charges.md) — spécifications complètes du projet
- [`carnet_apprentissage.md`](./carnet_apprentissage.md) — journal d'apprentissage, session par session

## État d'avancement

🟡 Étape 0 — Mise en place du repo Git

## Contraintes clés

- Claude n'agit jamais sans validation explicite
- Toute action est loggée dans un journal d'activité
- Confidentialité stricte (aucune lecture de fichier sans permission)
