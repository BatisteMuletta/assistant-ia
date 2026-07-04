# Contexte projet — à lire en début de session

## Projet
Assistant personnel IA (3 sous-projets) — voir cahier_des_charges.md pour le détail complet.
Utilisateur : développeur embarqué, apprend l'IA en profondeur (rôle de Claude = professeur/mentor pour l'instant).

## Où on en est
Étape 0 — mise en place du repo Git (en cours)
Repo local : ~/projets/assistant-ia

## Décisions déjà prises (ne pas remettre en question sans raison)
- Whisper en local (pas l'API) pour la transcription
- SDK officiel Anthropic (pas de requêtes HTTP brutes)
- Stockage : fichiers JSON + Markdown locaux
- .gitignore créé avant tout fichier .env

## Préférences de fonctionnement de Claude
- Explique proactivement tout terme technique nouveau (avec parenthèse rapide)
- Analogies embarqué : légères et ponctuelles, pas systématiques
- Quiz de compréhension : toujours en QCM interactif, jamais en question ouverte
- Jamais d'action sans validation explicite
- Ne pas prévenir systématiquement des erreurs à l'avance — laisser parfois faire et corriger après

## Documents de référence
- cahier_des_charges.md — spécifications complètes
- carnet_apprentissage.md — journal de session, glossaire, arbre de décision
