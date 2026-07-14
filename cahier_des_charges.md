# Cahier des charges — Assistant personnel IA
> Projet personnel · Ubuntu Linux (migration Windows prévue) · Claude Pro + API Anthropic
> Version 4 — 04/07/2026

---

## Profil utilisateur

| Champ | Info |
|---|---|
| Formation actuelle | Mastère Spécialisé — Ingénierie d'Affaires Industrielles pour l'International, INSA Toulouse — début septembre 2026 |
| Alternance | Catamania, Paris (Issy-les-Moulineaux) — en parallèle du mastère, à partir de septembre 2026 |
| Matières | Inconnues pour l'instant |
| Background technique | Développeur embarqué · 5 ans d'école d'ingénieur |
| Langages maîtrisés | C / C++, Python, Bash |
| Éditeur | VS Code |
| Navigateur | Chrome |
| Système actuel | Ubuntu Linux |
| Migration prévue | Windows (à venir) |
| Versioning | Un seul repo Git — créé dès l'étape 0 avec README.md |
| Moment d'usage principal | Le matin avant de commencer la journée |
| Niveau IA au démarrage | Première vraie expérience avec l'IA |
| Niveau API REST | Jamais utilisé — à découvrir |
| Niveau Git | Notions de base |

---

## Philosophie générale du projet

> **Claude ne fait rien sans demande ou validation explicite de l'utilisateur.**

Règles absolues applicables à toutes les étapes :
- Claude explique systématiquement ce qu'il est en train de faire avant de le faire
- Claude propose, suggère, attend confirmation — il n'agit jamais seul
- Une fois une action validée, Claude va jusqu'au bout sans interruption
- Toutes les actions sont loggées dans un journal d'activité
- Les parties de code complexes sont expliquées — le reste non
- Chaque fonctionnalité est testée et validée avant de passer à la suivante

### ⚠️ RÈGLE CRITIQUE — Option payante vs locale/gratuite (TOUJOURS)

**Pour CHAQUE nouvelle brique technique ajoutée au projet, Claude doit systématiquement présenter :**
1. L'option payante / cloud (API, service externe...)
2. L'alternative locale / gratuite équivalente (outil open source, exécution locale...)
3. Les compromis de chaque option (coût, confidentialité, simplicité, performance)

**Cette règle est non négociable et s'applique sans que l'utilisateur ait à la demander.** L'utilisateur choisit ensuite en connaissance de cause.

Exemples déjà identifiés à appliquer dans le projet :
| Brique | Option payante | Alternative locale/gratuite |
|---|---|---|
| Transcription audio | Whisper API (OpenAI, ~0,006$/min) | **Whisper en local** (gratuit, confidentiel, déjà choisi) |
| Résumés / tâches simples | API Anthropic à chaque appel | Ollama (Llama/Mistral en local, gratuit) — à évaluer pour les tâches simples |
| Stockage tâches/notes | — | SQLite (gratuit, local, requêtes avancées) vs JSON (plus simple) — à trancher étape 0/1 |
| Surveillance fichiers | — | inotify (Linux natif, gratuit, temps réel) déjà retenu |
| Automatisation de workflows | Développement custom | n8n / Node-RED (auto-hébergé, gratuit) — à évaluer si pertinent |

---

## Objectifs transversaux

### 1. Apprendre Claude en profondeur
Ce projet est autant un **terrain d'apprentissage** qu'un outil fonctionnel.

**Précision essentielle sur l'objectif** : il ne s'agit PAS de devenir indépendant de Claude. Claude reste le partenaire de travail sur le long terme — d'abord dans un rôle de **professeur/mentor** pendant la phase d'apprentissage de ce projet, puis dans un rôle **d'assistant** une fois les bases acquises.

**L'objectif réel d'autonomie** : être capable de faire le diagnostic soi-même — *"là j'ai besoin d'un agent IA"*, *"là il me faut une clé API pour ça"*, *"ici un Skill serait pertinent"* — c'est-à-dire savoir reconnaître quel outil/concept Claude mobiliser pour quel problème, sans forcément savoir tout exécuter seul à 100%. Une logique de chef de projet qui sait quand et pourquoi faire appel à quel outil, pas une logique de remplacement de Claude.

Profil d'apprentissage identifié :
- Motivation : **très élevée**, comprendre en profondeur prime sur juste avoir un outil qui marche
- Format d'explication efficace : schéma/diagramme visuel + exemple de code concret + analogie — combiner les trois
- Décomposition systématique en sous-étapes simples pour les concepts complexes/abstraits (agents IA, MCP...), jamais de vue d'ensemble balancée d'un coup
- Parallèles avec l'embarqué **appréciés mais légers et subtils** — une touche ponctuelle qui éclaire, pas une analogie développée systématiquement à chaque explication
- **Tout mot technique nouveau (firmware, daemon, etc.) est accompagné d'une courte parenthèse explicative au moment où il apparaît**, même si l'utilisateur ne le demande pas
- **Termes techniques nouveaux introduits en cours de route (ex : clé API, `.env`, `.gitignore`) : Claude les explique proactivement dès qu'ils apparaissent dans une explication, sans attendre que l'utilisateur pose la question**
- Quiz de vérification de compréhension bienvenus pour ancrer l'apprentissage — **affichés sous forme de vrai quiz interactif à choix (QCM)**, jamais comme une question ouverte noyée dans un paragraphe
- Erreurs/mauvais choix techniques : ne pas systématiquement prévenir avant — laisser parfois faire et corriger après, l'utilisateur apprend de ses erreurs

Approche pédagogique pratique :
- Selon la complexité : concept d'abord puis code, ou code avec explications en chemin
- Explication détaillée pour chaque concept nouveau — même si c'est long
- Claude pose des questions pour vérifier la compréhension avant d'avancer, sous forme de QCM/quiz interactif
- Claude suggère des expérimentations à chaque étape
- Code commenté en français systématiquement

Fonctionnalités Claude à explorer au fil du projet :
- Tokens et context window
- Prompting structuré
- API Anthropic (REST)
- Skills
- Agents IA
- MCP (Model Context Protocol)
- Claude Code
- Orchestration de pipelines

### 2. Exploiter le profil développeur embarqué
- Tout le projet se construit via **Claude Code** — pas d'interface no-code
- Approche bas niveau quand pertinent (scripts Python/Bash, API directes, automatisation système)
- Compréhension des mécanismes internes, pas juste "ça marche"

**Règle Claude Code — quoi expliquer, quoi générer directement :**

| Type de code | Approche |
|---|---|
| Concept nouveau, choix architectural, logique IA | ✅ On s'arrête, on explique, on discute |
| Code répétitif MAIS avec un pattern intéressant la première fois | ✅ Expliqué une fois, généré directement ensuite |
| Code purement mécanique sans valeur pédagogique (imports, config standard...) | ⚡ Généré directement, sans s'y attarder |

**Règle de sécurité pédagogique** : si Claude est sur le point de générer sans expliquer, il signale *"Je génère cette partie directement — dis-moi si tu veux qu'on s'y attarde"*. L'utilisateur garde le contrôle sur ce qu'il veut approfondir. Objectif : ne jamais passer à côté d'un concept important par inadvertance.

**Rappel de l'objectif** : pas devenir codeur — devenir chef d'orchestre qui comprend ce que Claude construit, pourquoi, et sait quoi lui demander ensuite. Claude Code est le véhicule pédagogique, pas une fin en soi.

### 3. Savoir reconnaître quel outil mobiliser
Pour chaque brique technique ajoutée à n'importe lequel des 3 projets, **avant de construire**, on s'arrête pour expliciter le diagnostic :
- *Pourquoi ce choix précis ?* (agent IA / clé API / Skill / MCP / simple script...)
- *Qu'est-ce qui, dans le besoin, a mené à ce choix plutôt qu'un autre ?*

Deux livrables cumulatifs dans le carnet d'apprentissage :
- **Arbre de décision** — schéma qui se construit au fil du projet, du type *"besoin d'automatiser une séquence d'actions → agent IA"*, *"besoin d'une règle fixe réutilisable → Skill"*, *"besoin de connecter un outil externe → MCP"*
- **Recueil d'exemples commentés** — chaque brique des 3 projets devient un cas concret annoté dans ce recueil, avec le raisonnement qui a mené au choix

Objectif : à terme, être capable de faire ce diagnostic seul sur un nouveau projet, en gardant Claude comme partenaire d'exécution (rôle d'assistant) plutôt que comme professeur (rôle initial pendant cette phase d'apprentissage).

### 4. Carnet d'apprentissage
Document `.md` séparé, mis à jour **après chaque session**, contenant :
- Ce qu'on a construit
- Ce qu'on a appris (concepts, définitions, bonnes pratiques)
- Les fonctionnalités Claude explorées
- Les questions ouvertes pour la prochaine session
- Un glossaire cumulatif

---

## Projet 1 — Dashboard personnel intelligent

### Objectif
Une page web qui s'ouvre comme page d'accueil de Chrome (onglet pinné, toujours ouvert), centralisant tous les outils d'organisation avec Claude intégré.

### Design
- Style : minimaliste / épuré
- Mode : light mode
- Interface : bilangue français + anglais sur la même page
- Principe : une information = un endroit, rien de superflu
- Code structuré et commenté pour être modifiable facilement par l'utilisateur
- Modifications via VS Code directement dans les fichiers — pas d'interface de paramètres

### Précisions design
- Pas d'horloge/date sur le dashboard (déjà visible ailleurs sur le système)
- Zones identifiées par icônes uniquement, pas de titres de section — épuré au maximum
- Layout fixé une fois pour toutes en étape 1, pas de réorganisation prévue pour l'instant

### Suivi des coûts (nouvelle zone)
- Compteur en temps réel des coûts liés au projet, visible sur le dashboard
- Agrège : appels API Anthropic (dashboard, résumés) + Whisper (transcriptions)
- Mise à jour à chaque appel API
- Stockage : fichier `costs.json`

### Zones visuelles (layout à définir ensemble en étape 1)
- **Calendrier Google** — vue semaine complète, interaction directe depuis le dashboard
- **Gmail** — mails triés urgent / pas urgent, recherche en langage naturel via Claude
- **Tâches** — séparation urgent / pas urgent, tâches non faites conservées d'un jour à l'autre
- **Bloc notes rapide** — saisie immédiate, analyse automatique par Claude dès la frappe
- **Section suggestions Claude** — deadlines détectées, notes → tâches, actions en attente de confirmation
- **Chat Claude** — 10 derniers échanges conservés, détection automatique de la langue (fr/en)
- **Journal d'activité** — log de toutes les actions Claude
- **Stats minimales** — compteur simple d'actions (mails traités, fichiers rangés, notes créées)
- **Suivi des coûts** — compteur temps réel des dépenses API (Anthropic + Whisper)

### Système de validation selon le type d'action
| Action | Mode de validation |
|---|---|
| Envoi de mail | Bouton "Envoyer" explicite dans le dashboard |
| Rangement fichier | Confirmation simple dans le chat |
| Ajout événement calendrier | Bouton "Confirmer" dans la section suggestions |
| Note → tâche | Suggestion automatique avec bouton confirmer/ignorer |
| Deadline détectée | Suggestion avec bouton "Ajouter au calendrier" |

### Briefing automatique du matin
Adaptatif selon l'urgence détectée :
- Calme → synthèse courte (3-4 lignes)
- Urgences détectées → briefing détaillé avec contexte complet
- Contenu : mails urgents, événements du jour, deadlines 48h, tâches non faites

### Fonctionnalités Gmail
- Un seul compte Gmail (perso + études mélangés)
- Tri automatique urgent / pas urgent
- Recherche en langage naturel via Claude ("trouve le mail de mon prof sur le projet")
- Rédaction de réponses par Claude, validation + bouton envoi obligatoire
- Ton adapté au destinataire (formel école/pro, décontracté perso)
- Détection automatique des deadlines dans les mails → suggestion ajout calendrier

### Fonctionnalités Calendrier
- Vue semaine complète
- Ajout d'événements directement depuis le dashboard (manuel ou via Claude)
- Claude peut ajouter à la place de l'utilisateur sur demande
- Toutes les deadlines détectées apparaissent automatiquement après confirmation

### Fonctionnalités Notes
- Saisie rapide dans le bloc notes
- Dès la frappe → Claude analyse et suggère automatiquement :
  - Conversion en tâche si applicable
  - Ajout au fichier `notes.md`
- Un seul fichier `notes.md` qui grandit, structuré et nettoyé par Claude
- Traduction possible si note en langue étrangère

### Notifications système
- Notifications natives Ubuntu (`notify-send`) hors dashboard
- Uniquement pour les éléments urgents nécessitant une action
- Solution Windows équivalente prévue lors de la migration

### Stockage local
- Tâches : fichier `tasks.json`
- Notes : fichier `notes.md`
- Historique chat : fichier `chat_history.json` (10 derniers échanges)
- Journal d'activité : fichier `activity_log.json`
- Stats : fichier `stats.json`

### Stack technique
- HTML / CSS / JS (commenté en français, structuré pour être modifiable)
- **SDK officiel Anthropic** (`pip install anthropic`) plutôt que requêtes HTTP brutes
- Serveur local Python (**Flask**, décidé le 14/07/2026) : sert le dashboard + fait le pont vers l'API Anthropic/Ollama (la clé API ne doit jamais être exposée côté navigateur)
  - ⚠️ **À revisiter en fin de construction du projet 1** : Flask a été choisi pour sa simplicité (premier serveur web du projet), mais une migration vers **FastAPI** est à rediscuter une fois le dashboard terminé, si le besoin de typage/async/doc auto-générée se justifie davantage.
- Bascule **Ollama (défaut, gratuit) ↔ API Anthropic (payant)** pour toutes les fonctionnalités IA, via une fonction centrale unique (`generer_reponse`) — un seul point de config, pas d'appels dispersés. Modèle local par défaut : **Llama 3.2 3B**.
- OAuth Google (Gmail + Calendar)
- Stockage : fichiers JSON + Markdown locaux — **repo GitHub public** : `costs.json`, `chat_history.json`, `activity_log.json`, `stats.json` exclus du versionnement (`.gitignore`) car données personnelles
- Notifications : `notify-send` (Ubuntu) → équivalent Windows à prévoir
- Sécurité : fichier `.env` pour toutes les clés API — jamais en clair dans le code ou le terminal
- Sécurité dépense API Anthropic : plafond **5$/mois** côté Console Anthropic (crédits prépayés + auto-reload désactivé + spend limit, configuré le 14/07/2026 — barrière principale) + blocage serveur local à **7$** depuis `costs.json` (filet de secours, traité comme anomalie s'il est atteint). Suivi en dollars (devise réelle de facturation Anthropic), pas en euros.
- Démarrage automatique : service **systemd** (lancement au boot, relance auto si crash, logs consultables)
- Chemins cross-platform dès le départ

---

## Projet 2 — Gestionnaire de fichiers intelligent

### Objectif
Claude range les fichiers et dossiers en respectant des règles strictes de validation et de confidentialité.

### Règles de validation (non négociables)

#### Nouveaux téléchargements
1. Fichier détecté → Claude notifie (notification système + dashboard)
2. Claude demande : *"Nouveau fichier : [nom]. Je peux le lire pour mieux le nommer ?"*
3. Si **oui** → Claude lit, propose nom + dossier, attend confirmation
4. Si **non** → Claude ne touche à rien, l'utilisateur gère seul

#### Nommage
- Claude suggère toujours, n'applique jamais sans confirmation
- Format : `AAAA-MM-JJ_[Catégorie]_[Description].[ext]`

#### Rangement global (sur demande uniquement)
- Claude liste les fichiers par noms uniquement — jamais de lecture de contenu
- Claude propose le rangement → validation → action

### Journal d'activité fichiers
```
[2026-09-15 09:32] Fichier détecté : rapport_final.pdf
[2026-09-15 09:33] Lecture autorisée par l'utilisateur
[2026-09-15 09:33] Nom suggéré : 2026-09-15_Cours_Rapport-Final.pdf → CONFIRMÉ
[2026-09-15 09:33] Rangé dans : ~/Cours/Marketing-International/
```

### Organisation cible des dossiers
À définir ensemble à l'étape 5 (matières du mastère inconnues pour l'instant) :
```
~/
├── Cours/
│   ├── [Matière 1]/
│   ├── [Matière 2]/
│   └── ...
├── Perso/
├── Pro/
└── Téléchargements/
```

### Skills à configurer (une seule fois)
- Logique de rangement par matière
- Règles de nommage des fichiers
- Extensions connues et dossier cible associé
- Liste des fichiers/dossiers jamais accessibles (fichiers sensibles)

### Stack technique
- Claude Desktop (accès système de fichiers Ubuntu)
- Script Python de surveillance (`inotify` Linux → `watchdog` cross-platform)
- Scripts Bash/Python cross-platform pour migration Windows
- Fichier de config Skills exportable (`skills_config.json`)

---

## Projet 3 — Assistant de cours automatique

### Objectif
Enregistrement en un clic, transcription + résumé automatiques, fichier rangé après validation.

### Workflow
```
Bouton ON (dashboard)
        ↓
Claude : "Enregistrement démarré — [heure de début]"
        ↓
Enregistrement via micro intégré (PyAudio)
        ↓
Bouton OFF
        ↓
Claude : "Envoi à Whisper pour transcription..."
        ↓
Transcription complète (Whisper en local — gratuit)
        ↓
Claude : "Génération du résumé..."
        ↓
Résumé détaillé (API Anthropic)
        ↓
Claude suggère nom + dossier → bouton confirmer
        ↓
Fichiers rangés dans ~/Cours/[Matière]/
        ↓
Log dans journal d'activité
```

### Sorties générées
1. `AAAA-MM-JJ_[Matière]_Transcription.md` — mot pour mot, fr et/ou en
2. `AAAA-MM-JJ_[Matière]_Résumé.md` — points clés, définitions, à retenir

### Gestion de l'audio et des erreurs
- Fichier audio brut **supprimé définitivement** après transcription réussie (confidentialité + espace disque)
- En cas d'échec de transcription : seules les transcriptions réussies sont conservées, pas de logs d'erreurs intermédiaires
- Sauvegarde supplémentaire (cloud/copie) : non décidé, à voir à l'usage

### Stack technique
- **Whisper en local** (gratuit, confidentiel) — transcription
- API Anthropic — résumé
- Script Python cross-platform
- Intégration bouton ON/OFF dans le dashboard

### Matériel
- Micro intégré de l'ordinateur (phase 1)
- Évolution vers micro-cravate USB si qualité insuffisante

---

## Budget estimé

| Poste | Coût |
|---|---|
| Claude Pro | ~18 €/mois |
| API Anthropic (dashboard + résumés) | ~5–10 €/mois |
| Whisper en local | **Gratuit** (remplace l'API Whisper) |
| Claude Desktop, VS Code, Chrome, GitHub | Gratuit |
| **Total estimé** | **~23–28 €/mois** |

---

## Plan de construction — étapes

Schéma de chaque étape :
1. **Comprendre** — concept expliqué (avant ou pendant selon complexité)
2. **Construire** — code via Claude Code, commenté en français
3. **Tester** — validation fonctionnelle avant de passer à la suite
4. **Documenter** — mise à jour carnet d'apprentissage

| Étape | Contenu | Fonctionnalité Claude apprise | Prérequis |
|---|---|---|---|
| 0 | Repo Git + README + fichier contexte + carnet | Tokens, context window, prompting de base | Rien |
| 1 | Squelette visuel dashboard HTML/CSS/JS | Claude Code, génération frontend | Claude Desktop |
| 2 | Chat Claude + journal d'activité + stats | API Anthropic REST, gestion messages | Clé API |
| 3 | Gmail + Calendar + notifications Ubuntu | MCP, OAuth, notify-send | Compte Google |
| 4 | Briefing matin adaptatif + détection deadlines | Agents IA, chaînage de tâches | Étape 3 |
| 5 | Notes → tâches automatique + fichier notes.md | Agents, analyse temps réel | Étape 4 |
| 6 | Skills + structure dossiers + surveillance fichiers | Skills, mémoire persistante, inotify | Claude Desktop |
| 7 | Rangement fichiers avec validation + log | Agents + Skills combinés | Étape 6 |
| 8 | Bouton ON/OFF enregistrement cours | PyAudio, scripting I/O audio | Whisper |
| 9 | Transcription + résumé + rangement auto | Pipeline complet, orchestration | Étapes 7 et 8 |

---

## Contraintes globales

- **Claude ne fait rien sans validation** — règle absolue, toutes étapes confondues
- **Claude explique systématiquement** ce qu'il fait avant de le faire, y compris les termes techniques nouveaux, sans attendre qu'on le lui demande
- **Journal d'activité** — toutes les actions loggées sans exception
- **Test obligatoire** avant validation de chaque étape
- **Cross-platform dès le départ** — migration Ubuntu → Windows en moins de 30 min
- **Confidentialité stricte** — aucune lecture de fichier sans permission explicite
- **Validation avant envoi mail** — toujours, sans exception
- **Code commenté en français** — lisible et modifiable par l'utilisateur dans VS Code
- **Construction progressive et pédagogique** — tout comprendre avant d'avancer
- **Tout via Claude Code** — approche développeur, pas de no-code
- **Un seul repo Git** — tout le projet versionné dès l'étape 0
- **Sécurité clé API** — à traiter en détail à l'étape 2 (principe du fichier `.env` à expliquer)
- **Limite technique de l'interface chat (claude.ai)** : cette interface n'a aucun accès au système de fichiers local de l'utilisateur — elle ne peut ni lire ni écrire ses fichiers réels. Toute écriture directe dans les fichiers du projet (README, carnet, code...) doit passer par **Claude Code** (terminal ou VS Code), qui lui a un accès réel au disque. Dans le chat, Claude ne peut que produire des fichiers téléchargeables ou des blocs de texte à coller manuellement.

---

*Cahier des charges v4 — 04/07/2026 — document vivant, mis à jour à chaque étape*
*Changements v3 → v4 : analogies embarqué plus légères/subtiles, parenthèses explicatives systématiques pour le jargon, explication proactive des nouveaux termes techniques, quiz de compréhension en QCM interactif plutôt qu'en question ouverte, clarification de la limite d'accès fichier du chat vs Claude Code.*
*Changements v4 → v4.1 (13/07/2026) : profil utilisateur précisé (INSA Toulouse, alternance Catamania à Issy-les-Moulineaux à partir de septembre 2026).*
