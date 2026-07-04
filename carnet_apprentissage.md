# Carnet d'apprentissage — Claude & IA
> Mis à jour après chaque session de travail
 
---
 
## Arbre de décision — quel outil pour quel besoin
*Se construit au fil des sessions, au fur et à mesure des choix faits dans les 3 projets*
 
```
Besoin détecté
  │
  ├── Automatiser une séquence de plusieurs actions enchaînées ?
  │     → Agent IA
  │         │
  │         ├── Définir le HARNAIS :
  │         │     - Quels outils l'agent peut utiliser ?
  │         │     - Quelles règles il doit respecter ?
  │         │     - Quelle est sa mission ?
  │         │
  │         └── Concevoir la LOOP :
  │               Observer → Réfléchir → Agir → Observer → ...
  │               (= while(1) + machine à états en embarqué)
  │
  ├── Règle fixe, réutilisable, apprise une fois pour toutes ?
  │     → Skill
  │
  ├── Connecter un outil/service externe (Gmail, Calendar...) ?
  │     → MCP / OAuth
  │
  ├── Simple traitement ponctuel (résumé, transcription...) ?
  │     → Appel API direct (SDK Anthropic)
  │
  └── Logique système bas niveau (surveillance fichiers, audio...) ?
        → Script Python/Bash natif (inotify, PyAudio...)
```
 
**Exemples concrets dans les projets :**
 
| Projet | Harnais | Loop |
|---|---|---|
| Projet 2 — Rangement fichiers | Outils : inotify + FS · Règles : jamais lire sans permission · Mission : surveiller ~/Téléchargements | Nouveau fichier ? → Demander permission → Lire → Proposer nom → Attendre confirmation → Ranger → Logger |
| Projet 3 — Pipeline cours | Outils : PyAudio + Whisper + API · Règles : supprimer audio après, valider avant rangement · Mission : traiter un enregistrement | OFF appuyé ? → Transcrire → Résumer → Proposer nom → Attendre confirmation → Ranger → Supprimer audio |
 
*Niveau de complexité ici : loops courtes et linéaires — un seul agent, pas d'orchestration multi-agents (ça viendra dans de futurs projets)*
 
*(À affiner et complexifier au fil des sessions avec des cas réels)*
 
---
 
## Recueil d'exemples commentés
*Chaque brique technique des 3 projets, avec le raisonnement qui a mené au choix*
 
| Brique | Choix fait | Pourquoi |
|---|---|---|
| *À remplir au fil des sessions* | | |
 
---
 
## Glossaire cumulatif
*Se remplit au fil des sessions*
 
| Terme | Définition simple |
|---|---|
| **Token** | Unité de base de découpage du texte pour un LLM — souvent un mot courant entier, ou un fragment pour un mot plus rare. C'est l'unité qui sert de base à la facturation de l'API et à la limite de context window. |
| **Context window** | Quantité maximale de tokens qu'un LLM peut "voir" en même temps (message actuel + historique + documents attachés). Au-delà, les informations les plus anciennes sortent de la vue du modèle. |
| LLM | *À définir en session 0* |
| **Prompt** | Le texte envoyé à Claude pour formuler une demande. Un bon prompt précise le contexte et le format attendu, donne des exemples (positifs/négatifs), et peut demander un raisonnement étape par étape pour les tâches complexes. |
| API REST | *À définir en session 0* |
| Agent IA | *À définir en session 0* |
| Skill | *À définir en session 0* |
| MCP | *À définir en session 0* |
| Claude Code | *À définir en session 0* |
| Whisper | *À définir en session 0* |
| OAuth | *À définir en session 0* |
| **Harnais (agent)** | La structure qui encadre un agent IA — ses instructions, ses outils disponibles, ses règles de sécurité. Comme un harnais d'escalade : il ne t'empêche pas d'agir mais définit le cadre sécurisé dans lequel l'agent opère. |
| **Loop (agent)** | La boucle d'exécution d'un agent : observer → réfléchir → agir → observer le résultat → réfléchir à nouveau → etc. Exactement comme une boucle de contrôle en embarqué. Le harnais définit le cadre, la loop est ce qui tourne dedans. |
| **Clé API** | Chaîne secrète qui identifie et authentifie l'utilisateur auprès d'un service (ex: API Anthropic). Quiconque la possède peut faire des appels à ta place et à tes frais — à traiter comme un mot de passe. |
| **Fichier `.env`** | Fichier texte local contenant les variables d'environnement (clés API, config) sous forme `NOM=valeur`, chargé au runtime par le programme. Sépare la config sensible du code source — jamais versionné dans Git. |
| **`.gitignore`** | Fichier listant les motifs de fichiers que Git doit ignorer (jamais suivis, jamais commités). Protège notamment contre le versionnement accidentel de secrets comme le `.env`. |
| **Repo Git local** | Dossier versionné sur ta propre machine, contenant l'historique complet des commits (`.git/`). |
| **Repo distant (GitHub)** | Copie hébergée en ligne du même historique, reliée au repo local via un `remote`. Ne se synchronise jamais automatiquement — il faut `push`/`pull` explicitement. |
| **Personal Access Token (PAT)** | Jeton secret qui remplace le mot de passe du compte GitHub pour les opérations en ligne de commande. Même principe qu'une clé API. |
| **Commit** | Point de restauration horodaté de l'historique Git, identifié par un hash unique. |
| **Staging (`git add`)** | Zone d'attente intermédiaire où on choisit précisément ce qui ira dans le prochain commit. |
 
---
 
## Sessions
 
---
 
### Session 0 — Mise en place du repo + concepts de base ✅ Terminée
**Date :** 04/07/2026
**Durée :** —
**Étape du projet :** Étape 0 — Fichier de contexte + repo Git
 
#### Ce qu'on a construit
- Repo Git local initialisé (`~/projets/assistant-ia`)
- `.gitignore` créé en premier, avant tout fichier sensible
- `README.md`, `cahier_des_charges.md` (v4), `carnet_apprentissage.md`, `CONTEXTE.md`
- Premier commit local (root-commit)
- Repo GitHub distant créé et relié (`remote origin`), push réussi via Personal Access Token (après résolution d'un blocage DNS local)
#### Ce qu'on a appris
- Clé API = chaîne secrète qui authentifie, à traiter comme un mot de passe
- `.env` = fichier séparant la config sensible du code ; `.gitignore` = liste des fichiers jamais versionnés
- Repo **local** (sur la machine) vs repo **distant** (GitHub) : deux historiques distincts, reliés manuellement via `git remote add`
- Depuis 2021, GitHub refuse le mot de passe du compte en ligne de commande → il faut un **Personal Access Token (PAT)**, même logique qu'une clé API
- Workflow Git de base : `git status` → `git add` → `git commit` → `git remote add origin` → `git push -u origin main`
- Un fichier commité puis "supprimé" reste dans l'historique Git tant que le commit n'est pas réécrit
- Interface chat Claude.ai = aucun accès au disque local ; Claude Code / Cowork = accès réel aux fichiers
- **Token** = unité de découpage du texte, base de la facturation API et de la context window
- **Context window** = quantité maximale de tokens visibles par Claude à un instant donné (message + historique + documents)
- **Prompt** = le texte de la demande ; 3 leviers pour l'améliorer : contexte/format précis, exemples positifs/négatifs, raisonnement étape par étape demandé
#### Fonctionnalités Claude explorées
- Prompting structuré (ajustement collaboratif du cahier des charges en cours de route)
- Vérification de compréhension via QCM interactifs
#### Points importants à retenir
- Toujours créer `.gitignore` avant de créer un `.env`
- Toujours `git status` avant `git add .`
- Jamais de mot de passe en clair dans un terminal — un PAT/token à la place
- Un problème `Could not resolve host` au push est un problème réseau/DNS, pas un problème Git ou GitHub
#### Questions ouvertes pour la prochaine session
- Configurer un credential helper pour éviter de recoller le token à chaque push
- SQLite vs JSON pour le stockage (à trancher avant/à l'étape 1)
- Quand basculer vers Claude Code / Cowork pour la suite du projet
---
 
*Les sessions suivantes s'ajouteront ici au fur et à mesure*