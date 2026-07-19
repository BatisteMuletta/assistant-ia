# Contexte projet — à lire en début de session

## Projet
Assistant personnel IA (3 sous-projets) — voir cahier_des_charges.md pour le détail complet.
Utilisateur : développeur embarqué, apprend l'IA en profondeur (rôle de Claude = professeur/mentor pour l'instant).

## Où on en est
Étapes 0 à 3 terminées. Prochaine étape : 4 (briefing matin adaptatif + détection deadlines).
Repo local : ~/projets/assistant-ia

- Étape 0 : repo Git, README, contexte, carnet
- Étape 1 : squelette visuel dashboard (HTML/CSS/JS)
- Étape 2 : chat Claude, serveur local Flask, bascule Ollama/Anthropic, suivi des coûts
- Étape 3 : Calendar + Gmail via serveurs MCP, notifications notify-send

## Décisions déjà prises (ne pas remettre en question sans raison)
- Whisper en local (pas l'API) pour la transcription
- SDK officiel Anthropic (pas de requêtes HTTP brutes)
- Stockage : fichiers JSON + Markdown locaux
- .gitignore créé avant tout fichier .env
- Calendar MCP (nspady/google-calendar-mcp) : HTTP, processus Node déjà lancé sur le port 3000
- Gmail MCP (ArtyMcLabin/Gmail-MCP-Server, fork actif de GongRzhe) : stdio, processus Node lancé à la demande par gmail_mcp.py
- OAuth Gmail et Calendar partagent le même projet Google Cloud (un seul client OAuth, scopes ajoutés au fur et à mesure)
- Toute fonctionnalité IA (chat, tri urgent des mails, rédaction de réponses) passe par generer_reponse() dans ia_provider.py, qui respecte la bascule Ollama/Anthropic — jamais d'appel direct à un provider ailleurs dans le code
- gmail_watcher.py : script de surveillance à lancer manuellement pour l'instant (pas encore de démarrage auto cron/systemd)

## Préférences de fonctionnement de Claude
- Explique proactivement tout terme technique nouveau (avec parenthèse rapide)
- Analogies embarqué : légères et ponctuelles, pas systématiques
- Quiz de compréhension : toujours en QCM interactif, jamais en question ouverte
- Jamais d'action sans validation explicite
- Ne pas prévenir systématiquement des erreurs à l'avance — laisser parfois faire et corriger après

## Documents de référence
- cahier_des_charges.md — spécifications complètes
- carnet_apprentissage.md — journal de session, glossaire, arbre de décision
