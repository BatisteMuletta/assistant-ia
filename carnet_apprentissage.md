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

## Fiche machine actuelle
*Référence rapide, à revérifier si la machine change*

| Élément | Valeur |
|---|---|
| Modèle | ThinkPad X260 |
| RAM totale | 7,6 Gi |
| GPU | Intel HD Graphics 520, intégré (Skylake) — pas de carte dédiée, partage la RAM système |
| OS | Ubuntu, **configuré en anglais** → dossier de téléchargements = `Downloads` (pas `Téléchargements`) |
| Modèle Ollama retenu | Llama 3.2 3B |

Commandes de vérification (à refaire sur une nouvelle machine, ne jamais supposer) : `free -h` (RAM totale), `lspci | grep -i vga` (GPU dédié ou intégré), `nvidia-smi` (VRAM si NVIDIA détecté).

## Fiche portabilité — changement de machine
*Principe : tout ce qui est dans le repo Git suit automatiquement (`git clone`). Tout ce qui est propre à la machine (matériel, secrets, config système) doit être refait à la main.*

**Se retrouve automatiquement** : code du dashboard, code du serveur Python, icônes SVG auto-hébergées, la fonction d'abstraction `generer_reponse` et toute la logique métier.

**À refaire manuellement sur une nouvelle machine** :

| Élément | Pourquoi ça ne se transfère pas | Quoi faire |
|---|---|---|
| `.env` (clé API Anthropic) | Protégé par `.gitignore`, jamais versionné — c'est le principe même de sa protection | Recréer le fichier à la main avec la clé |
| PAT GitHub / credential Git | Local à la machine, jamais dans le repo | Reconfigurer un fine-grained PAT limité au repo, ou `gh auth login` |
| Ollama + modèle local | Logiciel et modèle à retélécharger | Réinstaller ; **revérifier le matériel** avant de choisir le modèle, ne pas supposer que Llama 3.2 3B reste adapté |
| Claude Code | Outil installé sur le système, pas dans le repo | Réinstaller (`curl -fsSL https://claude.ai/install.sh \| bash`) |
| Service `systemd` (lancement auto) | Config système, pas un fichier de projet | Recréer/réactiver sur la nouvelle machine |
| Dossier de téléchargements | Le nom dépend de la langue du système | Vérifier le nom exact avant toute commande `mv` |
| `~/mcp-servers/google-calendar-mcp/` (serveur MCP Calendar) | Installé hors du repo Git (comme Ollama), et **contient un correctif local fait à la main** dans `src/transports/http.ts` (bug du mode HTTP stateless du serveur, voir Recueil d'exemples commentés) | Réinstaller (`git clone` + `npm install --omit=dev` + `npm audit fix` + `npm run build`), **puis réappliquer le correctif manuellement** — le code patché n'est sauvegardé nulle part ailleurs. Refaire aussi l'authentification OAuth (`npm run auth`) et replacer `gcp-oauth.keys.json`. |
| **nvm + Node.js** (installés pour faire tourner le serveur MCP) | Installateur exécuté une fois dans `~/.nvm`, jamais versionné | Réinstaller `nvm` (`curl ... install.sh \| bash`) puis `nvm install --lts` ; **le Node système par défaut de la machine peut être trop ancien** (rencontré ici : v12, EOL) — toujours vérifier `node --version` avant de supposer qu'il convient |
| `~/mcp-servers/Gmail-MCP-Server/` (serveur MCP Gmail) + `~/.gmail-mcp/` (credentials OAuth) | Installé hors du repo Git (comme Calendar) ; les credentials OAuth authentifiés sont stockés séparément, dans `~/.gmail-mcp/`, pas dans le dossier du serveur | Réinstaller (`git clone` + `npm install`, le build tourne automatiquement via le script `prepare`), copier un `gcp-oauth.keys.json` valide (même projet GCP que Calendar) et relancer `node dist/index.js auth` pour ré-authentifier |

**Cas particulier migration Windows** (déjà prévue au cahier des charges) : `notify-send` n'existe pas sous Windows, équivalent à trouver ; chemins déjà pensés cross-platform.

---
 
## Recueil d'exemples commentés
*Chaque brique technique des 3 projets, avec le raisonnement qui a mené au choix*
 
| Brique | Choix fait | Pourquoi (et ce qui a été écarté) |
|---|---|---|
| Intégration des icônes SVG dans le HTML | **SVG inline** (code du dessin copié directement dans le HTML) | Permet de changer la couleur de l'icône en CSS via `stroke="currentColor"` — utile pour les zones `suggestion`/`chat` qui ont un fond accent différent. **Écarté** : balise `<img src="icon.svg">` — HTML plus court et plus lisible, mais couleur de l'icône figée, impossible à changer en CSS sans bidouille (filtres peu fiables). |
| Source des 9 icônes Tabler | **Téléchargées via script** (`curl`), une seule fois, depuis le dépôt officiel `tabler/tabler-icons` sur GitHub | Dépôt open source (licence MIT), téléchargement ponctuel au moment de la construction — aucune dépendance réseau ensuite au chargement du dashboard (cohérent avec la décision auto-hébergé déjà actée). **Écarté** : téléchargement manuel un par un sur tabler-icons.io — plus fastidieux, sans bénéfice de contrôle supplémentaire ici. |
| Organisation des fichiers du dashboard | **Racine du repo** (`index.html`, `style.css`, `script.js`, `assets/icons/`) | Simple et suffisant tant qu'il n'y a qu'un seul dashboard à construire. **Écarté pour l'instant** : sous-dossier dédié (ex: `dashboard/`) — jugé prématuré à ce stade, décision volontairement provisoire : réorganisation prévue plus tard une fois les scripts des projets 2 et 3 présents dans le repo. |
| Protection de la clé API Anthropic | **Serveur local Python (Flask)** en pont entre `script.js` et l'API — la clé reste dans `.env`, lue uniquement côté serveur | `script.js` s'exécute dans le navigateur, donc lisible par n'importe qui via F12 — une clé écrite là serait aussi commitée sur GitHub (repo public) au premier push. **Écarté** : appeler l'API Anthropic directement depuis `script.js` — impossible à sécuriser, quelle que soit la précaution prise côté front. |
| Framework du serveur local | **Flask**, provisoire | Le plus simple pour un premier serveur web fait maison, peu de concepts à apprendre d'un coup. **Écarté pour l'instant** : FastAPI (plus moderne, typé, doc auto-générée) — à rediscuter explicitement en fin de construction du projet 1 (dashboard), noté dans `cahier_des_charges.md`. |
| Modèle IA par défaut du dashboard | **Ollama (Llama 3.2 3B) au démarrage**, bascule possible vers l'API Anthropic via une icône dédiée | Gratuit par défaut, cohérent avec la logique "minimiser les dépendances/coûts" déjà actée ailleurs (Whisper local). Bascule pensée pour toutes les fonctionnalités IA futures (pas que le chat), via une fonction centrale unique `generer_reponse()` — un seul point de config à changer, jamais d'appel dispersé à un provider précis dans le code. **Écarté** : coder des appels Ollama/Anthropic séparés dans chaque fonctionnalité — casserait la bascule globale et dupliquerait la logique de sécurité des coûts. |
| Sécurité de dépense API Anthropic | **Double seuil asymétrique** : plafond 7,5€/mois côté Console Anthropic (barrière principale, crédits prépayés + auto-reload désactivé) + blocage serveur local à 10€ depuis `costs.json` (filet de secours) | Le plafond Console est un vrai plafond dur, impossible à dépasser techniquement. Le seuil serveur à 10€ est une anomalie si jamais atteint — signe que le premier a échoué quelque part, pas un fonctionnement normal. **Écarté** : un seul seuil unique — moins robuste, aucune détection possible si le mécanisme principal tombe en panne. |
| Affichage du bloc "Suivi des coûts" | **Icône seule par défaut, détail affiché au clic** (montant dépensé / 7,5€, alerte distincte si 10€ atteint) | Respecte le design validé à l'étape 1 (zones identifiées par icône uniquement, pas de texte visible en permanence) tout en rendant la donnée consultable. **Écarté** : texte permanent sous l'icône — plus lisible en un coup d'œil, mais entorse au principe du layout figé sans qu'on en ait rediscuté explicitement. |
| Données personnelles et repo public | **`.gitignore`** étendu à `costs.json`, `chat_history.json`, `activity_log.json`, `stats.json` | Le repo GitHub est public — ces fichiers contiennent des données personnelles générées à l'usage (dépenses, conversations), pas du code. **Écarté** : les versionner comme le reste — exposerait publiquement des informations privées à chaque push. |
| Stockage du PAT GitHub (session 0-1) | **`credential.helper store` + fine-grained PAT scopé au seul repo `assistant-ia`** | Le PAT en clair sur disque n'est acceptable que parce que son rayon de dégât est limité à ce seul repo (moindre privilège) — même en cas de processus compromis tournant sous l'utilisateur, aucun autre dépôt n'est atteignable. **Écarté** : `gh auth login` — plus simple (trousseau chiffré) mais scopes larges par défaut, proches d'un accès à tous les repos privés ; `credential.helper cache` — plus prudent mais retapage régulier, jugé pas nécessaire vu le scope déjà restreint du PAT ; push manuel à chaque fois — zéro risque mais trop de friction pour un usage quotidien. |
| Interface Claude Code pour ce projet | **Terminal** (plutôt que l'onglet Code de Claude Desktop) | Plusieurs étapes à venir demandent une exécution autonome et continue (service systemd, surveillance `inotify`, pipeline audio) — seul le terminal permet ça, l'onglet Code s'arrête si l'app se ferme (une seule session active). **Écarté** : onglet Code comme interface principale — reste utile ponctuellement pour visualiser un diff, mais pas comme outil principal. |
| Vérification visuelle du dashboard | **Playwright** (bibliothèque de pilotage automatique de navigateur) | Permet à l'agent de vérifier lui-même le rendu (capture d'écran, lecture de la console) sans dépendre du regard de l'utilisateur à chaque petit test — complète (et non remplace) la validation finale de l'utilisateur. **Écarté** : Firefox classique piloté en headless — a échoué techniquement dans cet environnement (conflit avec l'instance déjà ouverte) ; `chromium-cli` — outil non installé sur cette machine. |
| Architecture Gmail/Calendar (étape 3) | **Serveur MCP existant** plutôt que REST direct | REST direct (SDK Google officiel) était l'option la plus cohérente avec ce qui était déjà maîtrisé (même schéma que l'appel Anthropic), mais MCP est confirmé comme une compétence standard de l'industrie (gouvernance Linux Foundation, adoption large) — apprendre ce protocole maintenant apporte une compétence nouvelle et durable. **Écarté** : REST direct (`google-api-python-client`) — plus de contrôle total et zéro dépendance tierce, mais n'apprend rien de nouveau puisque le principe REST/SDK est déjà acquis via Anthropic. |
| Sécurité de l'envoi de mail (étape 3) | **Double garantie** : jeton OAuth scopé à `gmail.compose` (jamais `gmail.send`) + séparation stricte `generer_brouillon()` / `envoyer_mail()`, cette dernière appelée uniquement par la route du clic "Envoyer" | Un bouton de confirmation dans l'interface est une règle de design, pas un mur technique — un bug pourrait la contourner. La portée du jeton est une garantie que Google applique lui-même côté serveur, indépendamment de la qualité du code ; la séparation des fonctions empêche qu'un bug ailleurs dans le pipeline déclenche un envoi. **Écarté** : se fier au seul bouton de confirmation dans l'UI — insuffisant si le jeton a la capacité `gmail.send` et qu'un bug appelle la fonction d'envoi par erreur. |
| Compte Gmail pour le développement (étape 3) | **Compte de test dédié**, connecté en premier à l'OAuth, avant le compte perso/étudiant réel | Code jeune = bugs probables ; un bug de tri/envoi sur le vrai compte pourrait toucher un mail important (deadline, info école), et des logs de debug pourraient afficher du contenu réel de mail à l'écran (risque captures d'écran). **Écarté** : développer directement sur le compte perso/étudiant réel — aucune protection en cas de bug pendant la phase la plus instable du développement. |
| Transport du serveur MCP Calendar (étape 3) | **HTTP** (le serveur MCP tourne en continu sur `localhost:3000`, notre Flask lui envoie des requêtes HTTP) | Cohérent avec le modèle client-serveur déjà acquis (même principe qu'Ollama sur `localhost:11434`) — un service persistant qui répond à la demande, testable isolément (`curl`), redémarrable indépendamment de Flask. **Écarté** : `stdio` (Flask lance et pilote lui-même le processus Node comme enfant) — mode recommandé par MCP pour des outils ponctuels type Claude Desktop, mais nous oblige à gérer le cycle de vie du processus dans notre propre code pour un gain qui ne sert pas notre cas (service persistant, pas ponctuel). |
| Bug HTTP stateless du serveur `google-calendar-mcp` (corrigé le 15/07/2026) | **Correctif local** : créer une connexion MCP neuve à chaque requête HTTP reçue (au lieu d'une seule connexion réutilisée pour toutes les requêtes) | Le serveur créait une seule connexion "stateless" au démarrage et la réutilisait pour toutes les requêtes — le SDK MCP officiel interdit explicitement ça (`"Stateless transport cannot be reused across requests"`), trouvé en lisant le code source de la bibliothèque. Confirmé qu'aucune version corrigée n'existe (dernière version npm déjà installée). **Écarté** : revenir sur stdio pour contourner le bug — aurait fonctionné, mais on perdait la cohérence pédagogique du choix HTTP pour une raison qui n'a rien à voir avec le fond du problème (juste un bug réparable). Signalement public du bug sur GitHub **volontairement non fait** (décision explicite : garder ça en interne). |
| Bug de concurrence sur le correctif HTTP ci-dessus (corrigé le 15/07/2026) | **File d'attente (mutex)** : les requêtes MCP reçues en parallèle sont traitées une par une, jamais simultanément | Le premier correctif marchait pour des requêtes bien espacées dans le temps, mais échouait dès que deux requêtes arrivaient rapprochées (cas réel : un navigateur qui envoie plusieurs `fetch` proches) — `"Already connected to a transport"`, car la connexion précédente n'était pas encore refermée quand la suivante essayait de se connecter. Repéré uniquement en testant plusieurs requêtes à la suite dans un vrai navigateur (Playwright), pas avec des tests `curl` isolés un par un. **Écarté** : ignorer le cas (le premier correctif suffisait aux tests `curl` séquentiels) — aurait laissé un bug intermittent, difficile à diagnostiquer plus tard, dépendant du timing réel d'usage. |
| Bug CSS : l'attribut `hidden` peut être silencieusement écrasé (corrigé le 15/07/2026) | **Règle globale `[hidden] { display: none !important; }`** ajoutée une fois pour toutes en tête du fichier CSS | N'importe quelle règle de classe avec `display: flex/block` (ex: `.panneau-chat`, `.panneau-calendrier`) peut annuler l'effet de l'attribut HTML `hidden` si elle a une spécificité CSS égale ou supérieure — bug retrouvé deux fois indépendamment (zone chat, puis zone calendrier) avant d'être traité à la racine. Conséquence concrète pas seulement visuelle : un panneau "invisible mais techniquement affiché" peut intercepter de vrais clics de souris destinés à l'élément parent. **Écarté** : corriger au cas par cas dans chaque zone concernée — aurait laissé le même piège se reproduire à la prochaine zone dépliable ajoutée. |
| Design de la zone Calendrier (affiné le 15/07/2026, après retour utilisateur sur le premier essai) | **Bande de 7 jours côte à côte (lundi → dimanche)**, point indicateur sous les jours avec événement, détail au clic affiché en **popover flottant** (pas empilé dans la zone) | Premier essai (liste verticale simple) jugé pas assez lisible par l'utilisateur. La zone occupe une ligne de grille fixée à 90px (layout figé étape 1) — pas la place d'empiler bande de jours + liste d'événements dans la hauteur disponible, d'où le choix du popover qui dépasse temporairement de la zone au clic plutôt que de casser la grille figée. **Écarté** : agrandir la ligne de grille de la zone calendrier — aurait rouvert une décision de layout explicitement figée à l'étape 1. |
| Transport du serveur MCP Gmail (étape 3) | **stdio** (notre code Python lance et pilote le processus Node à chaque appel, pas de service persistant) | Le serveur choisi (`ArtyMcLabin/Gmail-MCP-Server`) n'expose que ce mode selon sa documentation — pas de choix laissé contrairement à Calendar. Cohérent avec l'usage "outil ponctuel" recommandé par MCP pour ce type de service. **Écarté** : chercher un serveur Gmail alternatif exposant HTTP pour rester cohérent avec Calendar — jugé pas utile de complexifier la recherche pour une simple préférence de cohérence, le SDK MCP gère les deux transports nativement. |
| Tri urgent/pas urgent des mails (étape 3) | Appel à la fonction d'abstraction existante `generer_reponse()` (`ia_provider.py`), avec un prompt demandant une réponse JSON stricte | Réutilise directement la bascule Ollama/Anthropic déjà en place pour le chat — aucun nouveau point de configuration provider à créer. Dégradation silencieuse si l'appel échoue ou renvoie un format inattendu (aucun mail marqué urgent plutôt qu'un plantage). **Écarté** : règles heuristiques locales (mots-clés, expéditeurs connus) — plus rapide et gratuit à coup sûr, mais moins pertinent et moins intéressant pédagogiquement ici (le prompt/parsing JSON était déjà maîtrisé via le chat, l'appliquer à Gmail est un nouveau cas d'usage plutôt qu'une nouvelle notion). |
| Fenêtre d'affichage Gmail vs tri (bug trouvé et corrigé le 18/07/2026) | Pool de **25 mails candidats** examinés par le tri, puis tous les urgents conservés + complément de non-urgents récents jusqu'à 10 affichés | Filtrer "les 10 plus récents" *avant* de trier faisait disparaître un mail urgent mais légèrement plus ancien que les 10 derniers reçus — jamais même évalué par le tri. Repéré en testant volontairement avec des mails urgents envoyés avant des mails non urgents. **Écarté** : augmenter simplement la limite affichée à 25 — aurait noyé les mails vraiment urgents au milieu de mails sans intérêt plutôt que de les faire remonter en priorité. |
| Scope OAuth Gmail (étape 3) | **`gmail.modify`**, au lieu du `gmail.compose` prévu en session 5 | Nécessaire pour la lecture du contenu des mails et le tri urgent, construits cette session — un scope `gmail.compose` seul (écriture/envoi sans lecture) les aurait rendus impossibles. Écart avec la décision de sécurité de la session 5, présenté à l'utilisateur en cours de session, gardé en connaissance de cause plutôt que défait après coup (voir Session 6). **Écarté** : revenir à `gmail.compose` et retirer lecture/tri — casserait des fonctionnalités déjà construites et validées, pour un gain de sécurité jugé faible vu la garantie de substitution (séparation stricte brouillon/envoi dans le code). |
| Protection des routes Flask qui mutent des données (corrigé le 18/07/2026, suite audit) | Vérification de l'en-tête **`Origin`** (repli sur `Referer`) sur `/api/chat`, `/api/provider/toggle`, `/api/gmail/<id>/draft`, `/api/gmail/<id>/send` — rejet 403 si l'origine ne correspond pas à `127.0.0.1:5000`/`localhost:5000` | Ces routes n'avaient aucune protection propre : seul le fait que le JS du dashboard soit le seul appelant "normal" les protégeait, un simple appel `curl`/script direct suffisait à les déclencher (démontré par l'incident du mail de test envoyé sans validation). Solution simple, cohérente avec un projet perso mono-utilisateur non exposé au réseau. **Écarté** : jeton CSRF classique ou authentification complète — protection plus forte (résiste à un programme local qui forge son propre en-tête Origin, contrairement à la solution retenue), mais jugée disproportionnée pour ce projet à ce stade. |

---
 
## Glossaire cumulatif
*Se remplit au fil des sessions*
 
| Terme | Définition simple |
|---|---|
| **Token** | Unité de base de découpage du texte pour un LLM — souvent un mot courant entier, ou un fragment pour un mot plus rare. C'est l'unité qui sert de base à la facturation de l'API et à la limite de context window. |
| **Context window** | Quantité maximale de tokens qu'un LLM peut "voir" en même temps (message actuel + historique + documents attachés). Au-delà, les informations les plus anciennes sortent de la vue du modèle. Dans Claude Code : `/context` affiche le détail par catégorie, `/usage` le coût réel de la session, `/clear` vide l'historique (repart à 0 token, garde les fichiers projet), `/compact` résume la conversation en cours sans tout perdre. Chaque nouveau message renvoie tout l'historique précédent — le coût grimpe avec la longueur de la conversation, même pour un message court. |
| **LLM** (*Large Language Model*) | Modèle de langage entraîné sur d'énormes quantités de texte, capable de générer du texte en réponse à un prompt. Claude et Llama (via Ollama) en sont deux exemples — l'un hébergé (API payante), l'autre exécutable en local (gratuit). |
| **Prompt** | Le texte envoyé à Claude pour formuler une demande. Un bon prompt précise le contexte et le format attendu, donne des exemples (positifs/négatifs), et peut demander un raisonnement étape par étape pour les tâches complexes. |
| **API REST** | Manière standardisée pour deux programmes de communiquer par Internet/réseau local via des requêtes HTTP (GET, POST...) envoyées à des URLs précises (*endpoints*). Le serveur local du dashboard expose sa propre API REST (`/api/chat`, `/api/costs`...) que `script.js` appelle. |
| **Agent IA** | Programme qui ne se contente pas de répondre une fois, mais **observe → réfléchit → agit → observe le résultat → recommence**, de façon autonome sur plusieurs étapes. Composé de deux parties : le **harnais** (les outils autorisés, les règles à respecter, la mission) et la **loop** (la boucle d'exécution elle-même). Pas encore construit dans ce projet (prévu Projet 2, surveillance de fichiers) — `briefing.py` (étape 4) s'en approche par son chaînage, mais reste une loop courte et linéaire, pas un agent autonome multi-tours. |
| **Skill** | Règle ou procédure fixe, apprise une fois, réutilisable — pas d'autonomie ni de boucle, contrairement à un agent. Utile quand le besoin est répétitif mais toujours identique. Pas encore utilisé dans ce projet (prévu Projet 2). |
| **MCP** (*Model Context Protocol*) | Protocole standardisé (créé par Anthropic, gouvernance confiée depuis à la Linux Foundation avec OpenAI/Google/Microsoft/AWS) qui permet à une IA ou une application de se connecter à des outils/données externes (Gmail, Calendar, fichiers...) de façon uniforme, plutôt que d'écrire un appel REST sur-mesure pour chaque service. Une application qui utilise MCP joue le rôle de **client MCP**, qui parle à un **serveur MCP** (déjà écrit, par un tiers ou soi-même) qui lui sait interroger le vrai service (ex: Gmail). Adoption large et confirmée dans l'industrie (pas un effet de mode), retenu pour Gmail/Calendar à l'étape 3. |
| **Claude Code** | Outil en ligne de commande d'Anthropic : Claude tournant dans le terminal, avec accès direct au système de fichiers et à l'exécution de commandes (contrairement au chat claude.ai classique). Interface principale de ce projet (voir `feedback_outils_travail`) car plusieurs étapes à venir demandent une exécution autonome et continue (service `systemd`, surveillance `inotify`, pipeline audio) — impossible depuis un chat web classique. |
| **Whisper** | Modèle de reconnaissance vocale (speech-to-text) d'OpenAI, exécutable en local sans connexion internet. Retenu pour la transcription du Projet 3 (assistant de cours) plutôt que l'API payante — pas encore construit à ce jour. |
| **OAuth** | Protocole d'autorisation qui permet à une application tierce (notre dashboard) d'accéder à des données d'un compte (Gmail, Calendar) **sans jamais connaître le mot de passe** du compte. L'utilisateur autorise via un écran officiel du fournisseur (Google), qui délivre en échange un **jeton d'accès** (courte durée, utilisé pour chaque appel) et un **jeton de rafraîchissement** (longue durée, permet de renouveler l'accès automatiquement sans redemander l'autorisation) — l'autorisation se fait une fois, puis reste persistante, même principe que `gh auth login` pour GitHub. La **portée (scope)** du jeton limite précisément ce qu'il permet de faire — une vraie garantie technique, appliquée par Google lui-même, pas juste une règle de design côté interface. Scope réellement utilisé pour Gmail dans ce projet : `gmail.modify` (lecture + envoi + labels + suppression), plus large que le `gmail.compose` initialement prévu — voir Session 6 pour le pourquoi de cet écart assumé. |
| **notify-send** | Commande Linux qui affiche une notification native du système (bulle en haut de l'écran sur Ubuntu), indépendante de toute application ouverte — utilisée ici pour alerter des mails urgents même quand le dashboard n'est pas ouvert dans le navigateur. N'existe pas sous Windows (équivalent à trouver lors de la migration prévue). |
| **Dégradation silencieuse (silent failure)** | Un code qui, face à une erreur, continue de fonctionner avec un résultat par défaut plutôt que de planter ou d'afficher une erreur visible. Volontaire et utile pour ne pas casser tout un dashboard à cause d'une seule fonctionnalité IA en panne — mais peut aussi cacher une vraie panne si rien n'indique que le résultat affiché n'est pas fiable (rencontré avec le tri Gmail quand Ollama était arrêté sans que rien ne le signale dans l'interface). |
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
| **Serveur proxy (pont)** | Petit serveur intermédiaire qui reçoit une requête, la retransmet à un autre service (ici l'API Anthropic ou Ollama), puis renvoie la réponse. Utilisé ici pour que la clé API reste côté serveur, jamais exposée au navigateur. |
| **Endpoint / route API** | URL précise qu'un serveur expose pour une action donnée (ex: `/api/chat` pour envoyer un message). Le "verbe" HTTP (GET, POST...) précise le type d'action attendu. |
| **Provider (fournisseur de modèle IA)** | Dans ce projet : soit Ollama (local, gratuit), soit l'API Anthropic (payante). Le code ne doit jamais appeler un provider directement — toujours passer par la fonction centrale `generer_reponse()`, qui décide elle-même lequel utiliser. |
| **Ollama** | Outil qui fait tourner un LLM en local sur sa propre machine (ex: Llama 3.2), avec une API HTTP locale (`localhost:11434`) très proche de celle d'un vrai service cloud — ce qui permet de coder contre la même interface qu'on utilise Ollama ou l'API Anthropic. |
| **Seuil de dépense (cost cap)** | Limite de dépense fixée à l'avance sur un service payant, pour éviter une facture incontrôlée (bug, boucle infinie...). Deux seuils utilisés ici : un plafond compte (Console Anthropic, barrière principale) et un blocage applicatif (serveur local, filet de secours en cas d'échec du premier). |
| **Trousseau système (keyring)** | Coffre-fort intégré à l'OS (GNOME Keyring sur Ubuntu) qui stocke des secrets chiffrés — illisibles sans la clé de déchiffrement, elle-même liée à la session utilisateur ouverte. Protège un secret au repos (disque volé, session verrouillée), mais pas pendant une session active : tout processus tournant sous l'utilisateur peut alors y accéder déchiffré. |
| **Injection de prompt** | Instructions cachées dans un contenu lu par un agent IA (fichier, page web...) qui tentent de le manipuler pour lui faire exécuter des actions non voulues. Un contenu lu par l'agent n'est jamais traité comme une instruction valide venant de l'utilisateur — seule la vraie conversation avec l'utilisateur fait autorité. |
| **Serveur** | Un programme qui reste allumé en continu et attend des questions, comme un guichet qui ne ferme jamais tout seul — répond, puis attend la suivante. Ollama, le serveur Python du dashboard, et l'API Anthropic sont trois exemples du même principe **client-serveur**, seule change l'adresse du guichet. |
| **`localhost` / port** | `localhost` = "sur ma propre machine, jamais sur internet". Le **port** (ex: `5000` pour le serveur Flask, `11434` pour Ollama) = le numéro de bureau précis à l'intérieur du bâtiment, pour distinguer plusieurs programmes qui tournent en même temps sur la même machine. |
| **JSON** | Format texte structuré (ex: `{"message": "salut"}`) utilisé comme langue commune entre le navigateur (JavaScript) et le serveur (Python), malgré des langages différents. |
| **Loopback / LAN / WAN** | Trois échelles réseau, du plus petit au plus grand. **Loopback** : la machine se parle à elle-même, ne sort jamais par la carte réseau — c'est `localhost` (ex: Ollama). **LAN** : plusieurs appareils reliés entre eux sans sortir sur internet (ex: PC et imprimante sur la même box). **WAN** : la communication traverse vraiment internet (ex: `api.anthropic.com`). |
| **Moindre privilège (dossiers)** | Sur Linux, les permissions appartiennent aux dossiers, pas aux programmes. `~/` appartient à l'utilisateur (aucune élévation nécessaire) ; `/usr`, `/etc` appartiennent à root (`sudo` obligatoire). Un programme installé dans `~/.local/` (Ollama, Playwright, Claude Code...) ne peut, au pire, abîmer que les fichiers de l'utilisateur — jamais le système entier. |
| **Quota Claude Code Pro vs budget API** | Deux limites séparées, à ne pas confondre : le quota de l'abonnement Pro (fenêtre glissante de 5h + plafond hebdomadaire, pour l'usage interactif de Claude Code) et le budget API (5$/7$ configuré dans ce projet, pour les appels Anthropic du dashboard). Si le quota Pro s'épuise en pleine tâche, Claude Code s'arrête net (rien n'est perdu sur le disque) ; `/usage` permet de surveiller ce quota, comme `/context` pour la fenêtre de contexte. |
| **Environnement de test / staging** | Espace de développement isolé, sans conséquence réelle (ex: compte Gmail dédié aux tests), utilisé pour valider une fonctionnalité avant de la brancher sur les vraies données (**production** — ex: le compte perso/étudiant réel). Pratique standard en développement logiciel dès qu'une fonctionnalité peut faire une action réelle et risquée (envoyer un mail, modifier un calendrier). |
| **Transport (MCP)** | Le mécanisme concret par lequel un client MCP et un serveur MCP échangent leurs messages : `stdio` (processus enfant, flux d'entrée/sortie standard) ou `HTTP` (requêtes réseau classiques sur un port local). Le choix du transport ne change pas ce que le serveur sait faire (ses outils), seulement la façon dont on lui parle. |
| **Mode stateless (sans état)** | Mode de fonctionnement où le serveur ne garde aucune mémoire d'une requête à l'autre — chaque appel doit être autonome. Piège rencontré ici : un serveur MCP qui réutilisait une seule connexion stateless pour toutes les requêtes, alors que le protocole exige une connexion neuve à chaque fois en mode stateless. |
| **`npm audit`** | Commande qui analyse les dépendances d'un projet Node.js et signale les vulnérabilités connues (avec un niveau de gravité : low/moderate/high/critical). `npm audit fix` applique les corrections disponibles automatiquement. Distinguer les vulnérabilités dans les dépendances de **production** (utilisées quand le programme tourne réellement) de celles des dépendances de **développement** (outils de test, jamais exécutés en usage normal) — ces dernières peuvent être exclues avec `npm install --omit=dev`. |
| **Mutex / file d'attente (concurrence)** | Mécanisme qui force plusieurs opérations à s'exécuter une par une plutôt qu'en même temps, quand une ressource partagée (ici : une seule connexion MCP à la fois) ne supporte pas d'être utilisée par deux opérations simultanément. Un bug de concurrence n'apparaît souvent qu'avec des requêtes rapprochées dans le temps — un test isolé (une requête, on attend la réponse, puis la suivante) peut sembler fonctionner alors que le vrai usage (plusieurs requêtes quasi simultanées, ex: un navigateur) révèle le problème. |
| **`[hidden] { display: none !important; }`** | Garde-fou CSS qui garantit que l'attribut HTML `hidden` (censé cacher un élément) l'emporte toujours, même si une règle de classe ailleurs dans la feuille de style définit `display: flex`/`block` sur ce même élément — une règle de classe peut sinon silencieusement annuler `hidden` (bug rencontré deux fois dans ce projet, zone chat puis zone calendrier). |
| **Popover** | Petit panneau qui apparaît par-dessus le reste de l'interface (position flottante, pas intégré au flux normal de la page), généralement déclenché par un clic, et qui disparaît sans réorganiser le contenu autour de lui. Utilisé ici pour afficher le détail d'un jour du calendrier sans agrandir la zone qui le contient. |
| **CSRF** (*Cross-Site Request Forgery*) | Attaque où une page web piégée, ouverte dans le même navigateur qu'un service local (ex: notre dashboard sur `127.0.0.1:5000`), déclenche une requête vers ce service à l'insu de l'utilisateur — le navigateur envoie la requête avec les mêmes droits que si l'utilisateur l'avait faite lui-même. Se protège en vérifiant l'origine de la requête (en-tête `Origin`/`Referer`) ou avec un jeton dédié. |
| **CORS** (*Cross-Origin Resource Sharing*) | Mécanisme du navigateur qui contrôle si une page peut *lire la réponse* d'une requête envoyée vers un autre site/port. Point souvent mal compris : CORS ne bloque pas forcément l'*envoi* de la requête (qui peut atteindre le serveur et produire son effet), seulement la lecture du résultat par le script attaquant — sauf pour les requêtes dites "non simples" (ex: `Content-Type: application/json`), qui déclenchent un **préflight** (une requête `OPTIONS` de vérification envoyée avant la vraie requête) : si le serveur n'y répond pas avec les bons en-têtes, le navigateur bloque alors la vraie requête avant même qu'elle parte. |

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

### Session 1 — Layout dashboard + choix icônes Tabler (chat claude.ai) ✅ Terminée
**Date :** 05/07/2026
**Durée :** —
**Étape du projet :** Étape 1 — Squelette visuel du dashboard

#### Ce qu'on a construit
- Layout du dashboard validé dans le chat claude.ai (grille CSS asymétrique 9 zones, icônes Tabler outline) — design validé, pas de code écrit encore
- Décision actée : icônes Tabler en **auto-hébergé (SVG locaux)**, pas de CDN

#### Ce qu'on a appris
- Claude Code et le chat claude.ai n'ont **aucune mémoire partagée** : ce sont deux environnements complètement séparés (même si même modèle sous-jacent). Le pont entre les deux se fait manuellement via des fichiers `.md` transmis d'une session à l'autre.
- **CDN vs auto-hébergé** pour un asset statique (icône) : le CDN introduit une dépendance réseau externe à chaque chargement (risque si le dashboard est un onglet ouvert en permanence) ; l'auto-hébergé évite ce point de fragilité et ne charge que les fichiers réellement utilisés — cohérent avec la philosophie déjà actée dans le projet (Whisper local, stockage local, minimiser les dépendances externes).
- Différence entre **élément statique** (icône, fixe, ne change jamais) et **donnée dynamique** (contenu Gmail/Calendar récupéré via API) : deux mécanismes totalement indépendants — où est stocké le fichier icône n'a aucun impact sur la fraîcheur des données affichées.

#### Points importants à retenir
- Icônes Tabler → SVG locaux à ranger dans `assets/icons/` (à créer), pas de CDN.
- Consigne explicite de l'utilisateur : continuer à poser une question d'architecture avant de générer du code dès qu'un choix structurant se présente (ex: CDN vs local), **même si la situation semble identique à une fois précédente** — ne jamais supposer que la réponse sera automatiquement la même.

#### Questions ouvertes pour la prochaine session
- Construction effective du HTML/CSS/JS du layout dashboard (étape 1)

---

### Session 2 — Construction du squelette HTML/CSS/JS ✅ Terminée
**Date :** 14/07/2026
**Durée :** —
**Étape du projet :** Étape 1 — Squelette visuel du dashboard

#### Ce qu'on a construit
- `assets/icons/` : les 9 SVG Tabler outline téléchargés (notes, list-check, mail, bulb, calendar, message-circle, currency-euro, history, chart-bar)
- `index.html` : structure de la grille 9 zones, icônes en SVG inline, commenté en français
- `style.css` : CSS Grid asymétrique reprenant exactement `layout_dashboard_etape1.md`, zones `suggestion`/`chat` en fond accent, les 7 autres en style neutre identique
- `script.js` : fichier créé mais vide pour l'instant — pas de logique dynamique à cette étape

#### Décisions d'architecture prises avant de construire
Voir le tableau **Recueil d'exemples commentés** plus haut dans ce carnet pour le détail choisi/écarté/pourquoi sur : intégration SVG inline vs `<img>`, source des icônes (script vs téléchargement manuel), organisation des fichiers (racine vs sous-dossier).

#### Points importants à retenir
- Organisation en racine du repo = choix **volontairement provisoire**, à revoir quand les projets 2 et 3 arriveront.
- Configuration Git faite en parallèle : `credential.helper store` + PAT fine-grained scopé à ce seul repo (accès complet uniquement sur `assistant-ia`, pas sur le reste du compte GitHub) → push possible sans ressaisir les identifiants.

#### Questions ouvertes pour la prochaine session
- Test visuel du dashboard dans Chrome
- Étape 2 : chat Claude + journal d'activité + stats (API Anthropic)

---

### Session 3 — Chat Claude, serveur local, bascule Ollama/Anthropic ✅ Terminée
**Date :** 14/07/2026
**Durée :** —
**Étape du projet :** Étape 2 — Chat Claude + suivi des coûts

#### Ce qu'on a construit
- `server.py` : serveur Flask local, sert le dashboard et expose `/api/chat`, `/api/provider`, `/api/provider/toggle`, `/api/costs`
- `ia_provider.py` : fonction centrale `generer_reponse()` qui décide seule du provider (Ollama ou Anthropic) — aucun appel direct dispersé ailleurs dans le code
- `costs.py` : suivi de dépense mensuel dans `costs.json`, double seuil (7,5€ informationnel / 10€ blocage anomalie)
- Ollama installé **sans `sudo`** (binaire seul dans `~/.local`, pas de service système) + modèle `llama3.2:3b` téléchargé
- `index.html`/`style.css`/`script.js` mis à jour : panneau de chat (icône → zone de saisie au clic), icône de bascule provider (`toggle-left`/`toggle-right`) dans la colonne `misc`, détail des coûts affiché au clic sur la zone `couts`
- `.env.example`, `requirements.txt`, `config.json` (état du provider, défaut `ollama`)
- `.gitignore` étendu : `costs.json`, `chat_history.json`, `activity_log.json`, `stats.json` exclus (repo public, données personnelles)

#### Décisions d'architecture prises avant de construire
Voir le tableau **Recueil d'exemples commentés** plus haut : protection de la clé API par serveur proxy, choix Flask (provisoire, FastAPI à revoir en fin de projet 1 — noté dans `cahier_des_charges.md`), bascule Ollama/Anthropic via fonction centrale, double seuil de dépense asymétrique, affichage coûts icône-seule-puis-clic, `.gitignore` étendu.

#### Ce qu'on a appris
- **Pourquoi une clé API ne peut jamais vivre dans `script.js`** : le JS côté navigateur est lisible par n'importe qui (F12), et un fichier non exclu par `.gitignore` finit de toute façon commité sur un repo public dès le premier push.
- **Pattern d'abstraction "provider"** : une seule fonction (`generer_reponse`) décide quel modèle utiliser, le reste du code ne connaît jamais Ollama ou Anthropic directement — même logique qu'une couche d'abstraction matérielle (HAL) en embarqué : le code appelant ne change jamais, seule la couche du dessous change de driver.
- **Ollama sans `sudo`** : le binaire officiel peut être extrait manuellement (`tar --zstd`) dans `~/.local/bin` et lancé à la main (`ollama serve`) sans passer par l'installeur qui, lui, exige `sudo` pour un service système complet (utilisateur dédié, `systemd`).
- **Pourquoi deux seuils de dépense asymétriques** : le plafond Console Anthropic est un vrai plafond dur (crédits prépayés), donc censé suffire seul. Le seuil serveur à 10€ n'est qu'un filet de secours — s'il se déclenche un jour, ce n'est pas un événement normal mais le signe que le premier mécanisme a échoué quelque part.

#### Points importants à retenir
- Le provider par défaut au lancement est **Ollama** (gratuit) — l'API Anthropic ne s'active qu'en cliquant sur l'icône de bascule.
- Le plafond de 7,5€/mois côté **Console Anthropic reste à configurer manuellement** (compte utilisateur, pas accessible depuis le code) — à faire avant tout premier vrai test avec l'API Anthropic, guidé pas à pas.
- Modèle Anthropic choisi pour le chat : `claude-haiku-4-5-20251001` (le moins cher de la gamme), cohérent avec le budget serré du projet.
- Les prix utilisés dans `costs.py` pour estimer le coût par appel sont approximatifs — le seuil de 10€ est un filet de secours, pas un compteur exact ; se fier au tableau de bord de la Console Anthropic pour le montant réel.

#### Questions ouvertes pour la prochaine session
- Configurer le plafond 7,5€ sur la Console Anthropic (guidé pas à pas) avant tout usage réel de l'API Anthropic
- Tester concrètement la bascule vers Anthropic une fois le plafond en place
- Rediscuter Flask vs FastAPI en fin de construction du dashboard (projet 1)
- Étape 3 : Gmail + Calendar + notifications (MCP, OAuth)

---

### Session 4 — Test réel du dashboard, config Console Anthropic, passage €→$ ✅ Terminée
**Date :** 14/07/2026
**Durée :** —
**Étape du projet :** Étape 2 — Chat Claude + suivi des coûts (finalisation)

#### Ce qu'on a fait
- Test réel du dashboard construit en Session 3 : chat Ollama fonctionnel, mais réponses lentes (~45s pour 3 phrases)
- Diagnostic de la lenteur : RAM quasi saturée (234 Mio libres sur 7,6 Go) + swap plein à 100% (2 Go/2 Go) au moment du test, pas un bug du code — le modèle Ollama doit composer avec la mémoire déjà occupée par Claude Desktop/VS Code/Firefox tournant en parallèle
- Configuration réelle de la Console Anthropic : **5$ de crédits prépayés, auto-reload désactivé, spend limit à 5$, alertes email activées** (montant finalement choisi par l'utilisateur, différent des 7,5€ envisagés en Session 3)
- Recalage du code sur la vraie devise de facturation (**dollars**, pas euros) : `costs.py` (seuils 5$/7$), icône `€` remplacée par une icône `$` (`currency-dollar.svg`) sur le bloc coûts du dashboard, textes de `script.js` et messages d'erreur de `ia_provider.py` mis à jour

#### Ce qu'on a appris
- **RAM quasi pleine + swap plein → ralentissement massif**, même pour un petit modèle (3B) sur un CPU à 4 cœurs sans GPU dédié — la mémoire disponible compte plus que le nombre de cœurs pour l'inférence locale.
- **Le compromis Ollama/Anthropic redevient concret ici** : Ollama gratuit mais consomme les ressources de la machine (RAM/CPU, peut ralentir tout le reste) ; l'API Anthropic payante mais aucune charge locale — le tout s'exécute dans le cloud d'Anthropic.
- La Console Anthropic facture en **dollars**, pas en euros — un point à vérifier avant de fixer des seuils dans le code plutôt que de supposer la devise.

#### Décisions d'architecture
| Brique | Choix fait | Pourquoi (et ce qui a été écarté) |
|---|---|---|
| Devise de suivi des coûts | **Dollars ($)** partout dans le code (seuils, calculs, affichage, icône) | Coïncide avec la vraie devise de facturation Anthropic — évite d'empiler une conversion €/$ approximative sur des prix déjà approximatifs. **Écarté** : garder l'affichage en euros avec conversion au taux du jour — ajoute une source d'erreur supplémentaire sans bénéfice réel. |
| Seuils de dépense finaux | **5$ principal (= plafond Console réel) / 7$ secours** | Recalés sur ce que l'utilisateur a réellement configuré sur la Console (5$, pas 7,5€ comme envisagé en Session 3) — le code doit refléter la vraie configuration du compte, pas un plan initial dépassé. |

#### Points importants à retenir
- Le plafond réel est maintenant **5$/mois**, crédits prépayés + auto-reload désactivé + spend limit + alertes email — confirmé actif.
- Si la RAM libre est basse au moment d'utiliser le dashboard, fermer des applications avant de tester le chat Ollama (ou basculer sur Anthropic, qui ne consomme aucune ressource locale).
- **Clé API Anthropic créée et testée en conditions réelles** : `.env` configuré par l'utilisateur (jamais partagé dans la conversation), bascule Ollama→Anthropic→Ollama validée de bout en bout. Premier appel réel : 0,0004$ dépensé, réponse quasi instantanée (contre ~45s avec Ollama sur cette machine) — écart de rapidité qui rend le compromis payant/gratuit très concret.
- **Design volontairement laissé au minimum jusqu'ici** (pas de vraie identité visuelle, juste la structure fonctionnelle) — passe design dédiée à prévoir une fois toutes les zones du dashboard connectées à de vraies données (fin projet 1), plutôt que de peaufiner une coquille encore vide.

#### Questions ouvertes pour la prochaine session
- Passe design dédiée sur le dashboard (couleurs, typographie, finitions) une fois toutes les fonctionnalités branchées
- Rediscuter Flask vs FastAPI en fin de construction du dashboard (projet 1)
- Étape 3 : Gmail + Calendar + notifications (MCP, OAuth)

---

### Session 5 — Ouverture étape 3 : architecture Gmail/Calendar + premier serveur MCP Calendar opérationnel 🔄 En cours
**Date :** 14-15/07/2026
**Durée :** —
**Étape du projet :** Étape 3 — Gmail + Calendar + notifications Ubuntu

#### Ce qu'on a fait
- Intégration du chat claude.ai (entrées 21 à 24) sur les décisions d'architecture de l'étape 3, avant toute construction de code
- Discussion des concepts MCP et OAuth avec l'utilisateur, questions d'architecture posées avant de coder (conformément à la consigne de la Session 1)
- Recherche en ligne : l'option "MCP officiel Google" existe mais s'est révélée non praticable (serveur distant réservé au programme Developer Preview, scopes lecture seule uniquement) — bascule vers un serveur MCP communautaire
- **Vérification de sécurité du code source** de `nspady/google-calendar-mcp` avant installation : dépôt cloné et lu directement (dépendances, gestion du jeton OAuth dans `tokenManager.ts`, absence de script `postinstall` suspect, absence d'URL externe cachée) — confirmé que le jeton ne quitte jamais la machine, sauf vers Google lui-même
- Installation de **nvm** (Node Version Manager) + Node.js LTS (v24), sans `sudo`, le Node système (v12, obsolète) resté intact
- Installation du serveur `@cocal/google-calendar-mcp` hors du repo Git (`~/mcp-servers/`) avec `npm install --omit=dev` (exclusion des dépendances de développement, qui concentraient toutes les vulnérabilités signalées, dont 2 critiques) + `npm audit fix` → 0 vulnérabilité sur les dépendances réellement utilisées
- Configuration Google Cloud Console (par l'utilisateur, guidé pas à pas) : projet, API Calendar activée, écran de consentement OAuth (External, Testing, compte de test ajouté), client OAuth type Desktop app
- Première authentification OAuth réussie (`npm run auth`) avec le compte Gmail de test, tokens sauvegardés localement (`chmod 600`)
- Vérification de bout en bout avec l'Inspector MCP officiel : lecture réelle des calendriers du compte de test confirmée
- **Bug trouvé et corrigé** dans le mode HTTP du serveur (réutilisation invalide d'une connexion stateless) — voir Recueil d'exemples commentés pour le détail technique. Serveur MCP Calendar maintenant fonctionnel en HTTP sur `localhost:3000`, testé avec plusieurs appels à la suite (`list-calendars`, `list-events`)

#### Décisions d'architecture prises avant de construire
Voir le tableau **Recueil d'exemples commentés** plus haut : architecture Gmail/Calendar via serveur MCP existant (plutôt que REST direct), double garantie de sécurité pour l'envoi de mail (scope OAuth `gmail.compose` + séparation `generer_brouillon()`/`envoyer_mail()`), compte Gmail de test dédié pendant tout le développement.

- **Ordre de construction retenu : Calendar en premier**, avant Gmail — plus simple côté données (événements datés) et bon premier contact avec OAuth avant d'attaquer Gmail, plus complexe (tri urgent/pas urgent, recherche langage naturel, génération de brouillons).

#### Ce qu'on a appris
- **MCP en pratique** : une application peut jouer le rôle de client MCP et interroger un serveur MCP déjà écrit (par un tiers) pour un service externe, au lieu d'écrire soi-même tous les appels REST — une couche d'abstraction en plus par rapport à l'appel REST direct déjà maîtrisé (SDK Anthropic, étape 2).
- **La confidentialité des mails dépend du provider actif** : avec Ollama, le contenu ne quitte jamais la machine ; avec l'API Anthropic, il sort nécessairement pour être traité — les journaux API ne sont conservés que 7 jours par défaut et ne servent pas à l'entraînement sous conditions commerciales (à distinguer de la politique du chat claude.ai lui-même, différente, sur les comptes Free/Pro/Max).
- **Un bouton de confirmation dans l'UI n'est pas une vraie garantie technique** — un bug peut le contourner. La vraie garantie contre un envoi de mail non voulu vient de la portée du jeton OAuth (Google refuse l'action lui-même si le scope ne l'autorise pas) combinée à une séparation stricte du code entre génération et envoi.
- **Pourquoi un compte de test avant le compte réel** : le code le plus jeune est le plus susceptible de bugs — isoler les premiers cycles de test protège les vraies données (mails importants, deadlines) et limite le risque d'exposition accidentelle (logs de debug affichant du contenu réel de mail).
- **Vérifier soi-même le code source d'une dépendance tierce plutôt que de faire confiance à sa documentation** : le README de `google-calendar-mcp` affirmait déjà que le jeton ne quittait jamais la machine — la lecture directe du code (`tokenManager.ts`, dépendances, absence de script d'installation suspect) l'a confirmé de façon vérifiable, pas juste déclarée.
- **`npm audit` peut alarmer sans raison réelle** : les vulnérabilités signalées peuvent se trouver uniquement dans des dépendances de développement (tests), jamais exécutées par le programme réel — `npm install --omit=dev` réduit à la fois la surface de code installée et le nombre de vraies vulnérabilités à traiter.
- **Un serveur qui "marche au premier essai" n'est pas forcément sans bug** : le mode HTTP du serveur MCP répondait correctement à la toute première requête, ce qui masquait un bug qui ne se révélait qu'à partir du deuxième appel — d'où l'intérêt de tester plusieurs appels à la suite avant de valider une intégration, pas juste un aller-retour isolé.

#### Points importants à retenir
- Le compte Gmail de test doit être créé et connecté à l'OAuth en premier ; le compte perso/étudiant réel ne sera rebranché qu'après plusieurs cycles de test validés — **fait dans cette session**, respecté.
- Le serveur MCP Calendar tourne en HTTP sur `localhost:3000` avec deux correctifs locaux cumulés (transport neuf par requête + file d'attente pour la concurrence, voir Fiche portabilité et Recueil d'exemples commentés) — à relancer manuellement à chaque session de travail pour l'instant (pas encore de `systemd`).
- Zone Calendrier du dashboard **fonctionnelle et branchée sur de vraies données** : bande de 7 jours, point indicateur, détail en popover au clic — testé avec un vrai événement créé sur le compte de test.
- **Deux bugs génériques corrigés au passage**, qui auraient pu ressurgir sur d'autres zones du dashboard plus tard : l'attribut `hidden` silencieusement écrasé par du CSS (garde-fou global ajouté), et un panneau invisible-mais-affiché qui bloque les vrais clics de souris (même cause racine).

#### Questions ouvertes pour la prochaine session
- Décider si on signale un jour le bug MCP à l'auteur du paquet (pour l'instant : non, gardé en interne)
- Construire Gmail (tri urgent/pas urgent, génération de brouillons, séparation stricte génération/envoi)
- Rediscuter Flask vs FastAPI en fin de construction du dashboard (projet 1)
- Passe design dédiée sur le dashboard, une fois toutes les fonctionnalités branchées
- Prévoir `systemd` pour lancer automatiquement Flask + le serveur MCP Calendar (actuellement démarrage manuel à chaque session)

---

### Session 6 — Construction Gmail (tri urgent, réponses, notifications) : étape 3 terminée ✅ Terminée
**Date :** 18/07/2026
**Durée :** —
**Étape du projet :** Étape 3 — Gmail + Calendar + notifications Ubuntu (clôture)

#### Ce qu'on a fait
- Choix du serveur MCP Gmail : `ArtyMcLabin/Gmail-MCP-Server`, fork activement maintenu de `GongRzhe/Gmail-MCP-Server` (original inactif depuis 7 mois, 72+ PR non fusionnées) — vérifié en ligne avant installation
- OAuth Gmail configuré sur le **même projet Google Cloud que Calendar** (décision explicitement validée avec l'utilisateur) : API Gmail activée, scope ajouté via le nouvel écran "Google Auth Platform → Data Access" (le menu Google Cloud Console a changé depuis la session 5, "OAuth consent screen" a été remplacé)
- Installation du serveur (`~/mcp-servers/Gmail-MCP-Server/`, hors repo Git comme Calendar), authentification OAuth réussie, credentials stockés dans `~/.gmail-mcp/`
- `gmail_mcp.py` : client MCP en **stdio** (processus Node lancé à la demande à chaque appel, pas de service persistant contrairement à Calendar) — parsing du texte brut renvoyé par le serveur en JSON structuré, nettoyage HTML→texte lisible (dont suppression de caractères invisibles zero-width utilisés par certains mails marketing comme espaceurs de mise en page)
- Route `/api/gmail` : tri urgent/pas urgent via `trier_emails_urgents()` (nouvelle fonction dans `ia_provider.py`, appelle `generer_reponse()` comme le chat — respecte automatiquement la bascule Ollama/Anthropic)
- Zone Gmail branchée sur le dashboard : liste cliquable (limitée à 10 mails affichés), lecture du contenu complet au clic sur un mail, génération de brouillon de réponse éditable + bouton d'envoi séparé
- **Test réel en conditions contrôlées** : envoi de 15 mails de test (5 vraiment urgents, 10 non urgents) au vrai compte connecté, vérification que le tri IA (Claude, provider actif à ce moment) classe les 15 correctement (15/15)
- **Bug trouvé et corrigé pendant ce test** : la route ne regardait que les 10 mails les plus récents *avant* de trier — un mail urgent mais légèrement plus ancien que les 10 derniers reçus disparaissait complètement de la liste, jamais même évalué par le tri. Corrigé en élargissant le pool examiné (25 mails) puis en gardant systématiquement tous les urgents détectés, complétés par les non-urgents les plus récents jusqu'à la limite d'affichage
- Envoi réel d'une réponse testé de bout en bout (brouillon généré par Claude → édition possible → clic "Envoyer" → mail réellement parti, correctement threadé `Re:`)
- `gmail_watcher.py` : script de surveillance en arrière-plan (boucle avec pause), notifications `notify-send` pour les mails urgents détectés, déduplication via un fichier local d'ids déjà notifiés (`mails_notifies.json`, exclu du repo) — testé : 6 notifications à l'écran au premier passage, 0 au second (mêmes mails), confirmées vues par l'utilisateur
- `CONTEXTE.md` mis à jour (étapes 0-3 marquées terminées, nouvelles décisions actées)

#### Décisions d'architecture prises pendant la construction
Voir le tableau **Recueil d'exemples commentés** plus haut pour le détail : transport stdio pour Gmail (vs HTTP pour Calendar), tri urgent via la fonction d'abstraction `generer_reponse()` existante, pool de mails élargi avant tri pour ne jamais perdre un urgent par effet de fenêtre glissante, scope OAuth `gmail.modify`.

#### ⚠️ Écart avec une décision de sécurité actée en session 5
Deux choix de la session 5 n'ont pas été respectés pendant cette session, **par manque de contexte au moment de guider la configuration OAuth** (le carnet n'a été relu qu'après coup, conformément à la consigne du projet de ne pas le charger automatiquement en début de session) :
- **Scope OAuth demandé : `gmail.modify`** au lieu de `gmail.compose` prévu — `gmail.modify` inclut la lecture complète, l'envoi, la modification des labels et la suppression, alors que `gmail.compose` se limite à la rédaction/l'envoi sans lecture. Le tri urgent et la lecture du contenu des mails, construits cette session, ont de toute façon besoin d'un scope de lecture — un pur `gmail.compose` les aurait rendus impossibles tels que conçus.
- **Compte connecté : le vrai compte (`batistemuletta7@gmail.com`) directement**, sans compte de test dédié préalable, contrairement au plan de la session 5.

Présenté à l'utilisateur en cours de session ; décision explicite prise de **garder cet état** plutôt que de tout refaire (le compte réel a déjà été testé en conditions réelles sans incident : lecture, tri, génération et envoi de réponse tous validés avec succès). Le garde-fou réel reste la séparation stricte `/api/gmail/<id>/draft` (aucun effet de bord) / `/api/gmail/<id>/send` (seule route qui appelle réellement `send_email`, déclenchée uniquement par le clic explicite du bouton "Envoyer" côté dashboard) — moins fort qu'une restriction de scope OAuth, mais réel.

#### Ce qu'on a appris
- **`stdio` vs `HTTP` en pratique, pas juste en théorie** : Calendar tourne en service persistant (HTTP, comme Ollama) parce que ça correspondait au modèle client-serveur déjà connu ; Gmail, lui, ne propose que `stdio` selon la doc du serveur choisi — notre code Python devient alors responsable de lancer et refermer le processus Node à chaque appel (`stdio_client` + `StdioServerParameters` du SDK MCP), au lieu d'un simple `curl`/`fetch` vers un port fixe. Le choix du transport dépend donc aussi de ce que le serveur MCP tiers a choisi d'exposer, pas seulement d'une préférence d'architecture.
- **Une dégradation silencieuse peut cacher une vraie panne** : `trier_emails_urgents()` est conçu pour ne jamais faire planter le dashboard si l'appel IA échoue (aucun mail marqué urgent plutôt qu'une erreur affichée) — bonne pratique en soi, mais rencontrée concrètement quand Ollama s'est révélé arrêté sur la machine : rien ne le signalait dans l'interface, ça ressemblait à un tri qui se trompait alors que le tri ne tournait tout simplement pas.
- **Un pool de candidats plus large que l'affichage final** est nécessaire dès qu'un tri/filtre s'applique après une limite de fraîcheur — sinon un élément important mais légèrement plus ancien peut sortir de la fenêtre avant même d'être évalué. Repéré concrètement avec le test des 15 mails (urgents envoyés en premier, donc mécaniquement les plus anciens du lot).
- **Les caractères invisibles (zero-width space/joiner, BOM) sont une vraie technique de mise en page email**, pas un artefact rare — un mail marketing HTML testé en contenait des dizaines, utilisés comme espaceurs. Un nettoyage HTML→texte doit les filtrer explicitement (`​`, `‌`, `‍`, `﻿`), une simple suppression des balises ne suffit pas.
- **Le menu Google Cloud Console pour les scopes OAuth a changé depuis la session 5** : "OAuth consent screen" a été remplacé par "APIs & Services → Google Auth Platform", scopes déplacés dans l'onglet "Data Access". Les interfaces des consoles cloud évoluent sans préavis — vérifier l'état actuel plutôt que de se fier à un souvenir de session précédente.

#### Points importants à retenir
- Compte Gmail réellement connecté : **`batistemuletta7@gmail.com`** (différent de l'adresse de contact habituelle) — à utiliser pour tout test futur touchant Gmail.
- **15 mails `[TEST]`** envoyés pendant cette session restent volontairement dans la vraie boîte de réception (l'utilisateur a choisi de ne pas les supprimer) — à garder en tête si une future fonctionnalité traite "tous les mails" sans filtre.
- `gmail_watcher.py` doit être **lancé manuellement** à chaque session pour l'instant (`python3 gmail_watcher.py`), comme le serveur MCP Calendar — aucun des deux n'est encore automatisé au démarrage (`systemd`/cron).
- Détection de deadlines dans les mails → suggestion d'ajout au calendrier : **volontairement pas construite cette session**, reportée à l'étape 4 (déjà prévue au tableau "Plan de construction" du cahier des charges), malgré sa mention dans la section "Fonctionnalités Gmail" du même document — légère incohérence interne du cahier des charges relevée avec l'utilisateur, tranchée en faveur du tableau.

#### Questions ouvertes pour la prochaine session
- Étape 4 : briefing matin adaptatif + détection de deadlines dans les mails → suggestion calendrier
- Prévoir `systemd`/cron pour `gmail_watcher.py` et le serveur MCP Calendar (les deux tournent manuellement pour l'instant)
- Décider un jour si les 15 mails `[TEST]` doivent être nettoyés de la vraie boîte
- Rediscuter Flask vs FastAPI en fin de construction du dashboard (projet 1) — toujours en attente depuis la session 3
- Passe design dédiée sur le dashboard, une fois toutes les fonctionnalités branchées — toujours en attente

---

### Session 7 — Audit de sécurité Gmail + protection CSRF des routes sensibles ✅ Terminée
**Date :** 18/07/2026
**Durée :** —
**Étape du projet :** Étape 3 (suivi post-clôture) — durcissement sécurité, pas de nouvelle fonctionnalité

#### Ce qu'on a fait
- Suite à l'incident de la session 6 (mail de test envoyé via `curl` sans validation explicite de l'utilisateur), question posée par l'utilisateur : le dashboard peut-il envoyer un mail tout seul, à cause de l'IA ?
- Audit de sécurité en deux passes : analyse directe du code, puis revue indépendante déléguée à un agent utilisant le **modèle Fable** (demande explicite de l'utilisateur), avec vérification a posteriori des affirmations clés du rapport par des `grep` ciblés sur le vrai code plutôt que de faire confiance aveuglément au rapport
- Conclusion de l'audit : le LLM n'a **aucune capacité d'exécuter des actions** (pas de paramètre `tools=` configuré nulle part dans `generer_reponse()`, sa sortie n'est jamais interprétée comme une commande) ; un seul chemin de code mène à un envoi réel (route `/send`), appelé uniquement par le clic "Envoyer" côté UI — **mais cette route (et `/draft`, `/toggle`) n'avait aucune protection côté serveur** : n'importe quel appel HTTP direct (curl, script, page web) pouvait la déclencher
- Creusé plus loin que le rapport initial : `/draft` n'avait même pas la protection *accidentelle* dont bénéficiait `/send` (pas de corps JSON requis) — une requête POST cross-origin "simple" (sans préflight CORS) pouvait l'atteindre sans qu'aucun navigateur ne la bloque, contrairement à `/send`
- Correctif implémenté (`server.py`) : vérification de l'en-tête **`Origin`** (repli sur `Referer`) sur toutes les routes qui mutent des données ou coûtent de l'argent (`/api/chat`, `/api/provider/toggle`, `/api/gmail/<id>/draft`, `/api/gmail/<id>/send`) — rejet `403` si l'origine ne correspond pas au dashboard local (`127.0.0.1:5000` ou `localhost:5000`)
- Testé sur les 4 routes : requête sans `Origin` → `403` ; requête avec origine tierce → `403` ; requête avec la bonne origine → `200`, fonctionnement normal confirmé

#### Décisions d'architecture
Voir le tableau **Recueil d'exemples commentés** plus haut : vérification Origin/Referer plutôt qu'un jeton CSRF classique ou une authentification complète — plus simple à mettre en place pour un projet perso mono-utilisateur, protège contre le scénario "page web piégée dans le même navigateur", mais n'empêche pas un programme local qui forge lui-même son en-tête Origin (accepté comme limite connue).

#### Ce qu'on a appris
- **"L'IA peut-elle agir seule" et "la route qui agit est-elle protégée" sont deux questions de sécurité distinctes.** Ici la première réponse était non (architecture saine : aucun tool-calling nulle part), mais ça ne dit rien sur la seconde — une route HTTP sans authentification reste actionnable par n'importe qui/quoi capable de l'atteindre, indépendamment de ce qui la déclenche normalement côté UI. Le vrai risque de la session 6 n'était pas l'IA, c'était l'absence de verrou serveur.
- **CORS protège la lecture de la réponse par un script, pas forcément l'envoi de la requête** : sans configuration CORS explicite, une requête cross-origin peut quand même atteindre le serveur et produire son effet — sauf pour les requêtes "non simples" (ex: `Content-Type: application/json`), qui déclenchent un **préflight** `OPTIONS` que le navigateur peut bloquer si le serveur n'y répond pas correctement. C'est ce qui protégeait `/send` par accident (elle exige du JSON), mais pas `/draft` (requête "simple", sans corps, donc sans préflight).
- **Vérifier soi-même les affirmations d'un rapport d'audit avant de les répéter** : le rapport de l'agent Fable était globalement juste et confirmé par des `grep` ciblés sur le vrai code (appelants de `envoyer_email`, absence de `tools=`, absence de CORS) — mais une relecture manuelle a quand même trouvé un angle que le rapport n'avait pas complètement creusé (`/draft` moins protégée que `/send`, alors que le rapport la classait "sévérité faible" sans cette distinction précise).
- **Une protection Origin/Referer est un compromis, pas une garantie absolue** : elle arrête un navigateur qui respecte les règles CORS/Origin (donc une page web piégée), mais un programme local qui parle HTTP directement (comme nos propres tests `curl` pendant tout ce projet) peut fabriquer n'importe quel en-tête lui-même. La vraie garantie contre ce cas serait un secret partagé (jeton d'authentification), jugée disproportionnée pour ce projet à ce stade.

#### Points importants à retenir
- **Quatre routes désormais protégées** (`403` si origine absente ou non reconnue) : `/api/chat`, `/api/provider/toggle`, `/api/gmail/<id>/draft`, `/api/gmail/<id>/send`. Les routes de lecture seule (`/api/gmail`, `/api/gmail/<id>`, `/api/calendar`, `/api/costs`, `/api/provider`) restent non protégées — pas de risque de mutation, jugé pas nécessaire.
- **Pour tout futur test via `curl` sur ces 4 routes** : ajouter `-H "Origin: http://127.0.0.1:5000"`, sinon la requête est rejetée (c'est voulu — exactement ce qui aurait empêché l'incident de la session 6).
- Origines autorisées : `http://127.0.0.1:5000` **et** `http://localhost:5000` — les deux acceptées, car les navigateurs les traitent comme deux origines distinctes malgré le fait qu'elles pointent vers la même machine.

#### Questions ouvertes pour la prochaine session
- Étape 4 : briefing matin adaptatif + détection de deadlines dans les mails → suggestion calendrier
- Si le dashboard doit un jour être accessible depuis un autre appareil (pas seulement `127.0.0.1`), la liste `ORIGINES_AUTORISEES` de `server.py` devra être mise à jour en conséquence
- Prévoir `systemd`/cron pour `gmail_watcher.py` et le serveur MCP Calendar (toujours en attente)
- Décider un jour si les 15 mails `[TEST]` doivent être nettoyés de la vraie boîte (toujours en attente)

---

### Session 8 — Étape 4 : briefing matin adaptatif + détection de deadlines ✅ Terminée
**Date :** 19/07/2026
**Durée :** —
**Étape du projet :** Étape 4 — Briefing matin adaptatif + détection deadlines (partie "tâches" reportée à l'étape 5, la fonctionnalité Tâches n'existe pas encore)

#### Ce qu'on a fait
- Deux décisions tranchées avant de coder : (1) le briefing omet la section "tâches non faites" pour l'instant — la fonctionnalité Tâches elle-même n'existe pas, prévue étape 5 — plutôt que de la construire en avance et empiéter sur le périmètre de l'étape suivante ; (2) déclenchement **manuel** (bouton dans la zone Suggestions), pas d'automatisation à heure fixe, pour ne pas ajouter une couche de planification (cron/scheduler) en plus du chaînage lui-même
- Relance du serveur MCP Calendar (`npm run start:http`), qui n'était plus lancé depuis la session précédente — confirme le point déjà noté : aucun démarrage automatique pour l'instant
- `briefing.py` créé : module d'orchestration qui **chaîne** plusieurs étapes — récupérer les mails urgents (Gmail) → récupérer les événements du jour (Calendar) → récupérer le corps complet de chaque mail urgent → en extraire des deadlines par IA → générer le texte final du briefing à partir de tout ça
- `calendar_mcp.py` : nouvelle fonction `lister_evenements_jour()` (bornée à aujourd'hui, distincte de la fonction "semaine" déjà existante) et **`ajouter_evenement()`** — première capacité d'écriture côté Calendar (jusqu'ici lecture seule). Vérifié au préalable que l'outil `create-event` existait bien côté serveur MCP (liste complète des outils inspectée) avant de coder dessus
- `ia_provider.py` : `detecter_deadlines()` (extraction IA de deadlines depuis le corps des mails, consigne explicite de ne jamais inventer une date non déductible du texte) et `generer_briefing()` (texte adaptatif : court si calme, détaillé si urgence)
- Routes `/api/briefing` et `/api/briefing/deadline`, protégées par la même vérification d'origine que les routes Gmail (voir session 7)
- Zone "Suggestions" du dashboard (jusque-là une icône inutilisée depuis l'étape 1) rendue cliquable : affiche le briefing (rendu Markdown, même traitement que le chat) et chaque deadline détectée avec son propre bouton "Ajouter au calendrier"
- **Avant de tester la création réelle d'événement, question explicite posée à l'utilisateur** (leçon directement tirée de l'incident de la session 6 — voir plus bas) : accord donné, événement de test créé et confirmé présent dans le vrai calendrier

#### Décisions d'architecture
Voir le tableau **Recueil d'exemples commentés** plus haut pour le détail — rien de nouveau ajouté cette session côté tableau, les choix (stdio/HTTP, tri via `generer_reponse()`, etc.) avaient déjà été actés à l'étape 3 et sont simplement réutilisés/étendus ici.

#### Ce qu'on a appris
- **Le chaînage de tâches en pratique** (compétence Claude explicitement associée à cette étape par le cahier des charges) : ce n'est pas un concept abstrait, c'est concrètement `briefing.py` — plusieurs appels successifs où le résultat de l'un nourrit le prompt du suivant (le corps des mails urgents alimente la détection de deadlines, qui elle-même alimente la rédaction du briefing final). Rejoint le vocabulaire du carnet (harnais + loop) : ici la loop est courte et linéaire (récupérer → analyser → générer → proposer → attendre confirmation), pas une boucle autonome.
- **Dérive pédagogique repérée par l'utilisateur, pas par moi** : pendant la construction (plusieurs fichiers créés à la suite), je suis resté en mode "exécution + rapport de statut" sans expliquer le concept de chaînage au fur et à mesure, alors que la règle du projet l'impose. Corrigé après coup, mémoire de feedback mise à jour (voir `feedback_pedagogie.md`).
- **La leçon de l'incident de la session 6 appliquée avec succès cette fois** : avant de tester la création réelle d'un événement calendrier (action à effet réel), j'ai posé la question et attendu la réponse plutôt que d'annoncer puis d'exécuter dans la foulée. Contraste direct avec l'envoi de mail non validé de la session 6 — preuve concrète que le correctif de comportement (mémoire de feedback) fonctionne, pas juste une bonne intention déclarée.
- **Vérifier qu'un outil MCP existe avant de coder dessus** : avant d'écrire `ajouter_evenement()`, la liste complète des outils exposés par le serveur MCP Calendar a été interrogée pour confirmer que `create-event` existait vraiment et connaître son schéma exact (champs requis, format de date) — plutôt que de supposer d'après la documentation du projet ou le nom probable de l'outil.

#### Points importants à retenir
- Un événement `[TEST] Vérification création événement` reste dans le vrai calendrier (créé pour tester, jamais supprimé).
- Le serveur MCP Calendar doit être relancé manuellement à chaque nouvelle session de travail (`cd ~/mcp-servers/google-calendar-mcp && npm run start:http`) — oublié en début de cette session, repéré uniquement en tentant d'interroger ses outils.
- Le briefing ne couvre que mails urgents + calendrier + deadlines détectées — pas de section tâches tant que l'étape 5 n'est pas construite.

#### Questions ouvertes pour la prochaine session
- Étape 5 : notes → tâches automatique + fichier `notes.md` — une fois construite, le briefing pourra intégrer la section "tâches non faites" laissée de côté cette session
- Prévoir `systemd`/cron pour `gmail_watcher.py` ET le serveur MCP Calendar (toujours en attente, se répète depuis plusieurs sessions)
- Décider un jour si les 15 mails `[TEST]` et l'événement `[TEST]` doivent être nettoyés
- Rediscuter Flask vs FastAPI, passe design dédiée — toujours en attente depuis la session 3

---

### Session 9 — Intégration du chat claude.ai (entrées 21-35) : réconciliation et un écart de scope Calendar non documenté jusqu'ici ✅ Terminée
**Date :** 19/07/2026
**Durée :** —
**Étape du projet :** Suivi/documentation (aucun code construit cette session)

#### Ce qu'on a fait
- `explications_techniques_cumulees_4.md` déplacé de `~/Downloads` vers le projet (demande explicite), lu en entier — 35 entrées, dont 21 à 35 jamais encore confrontées à ce qui a réellement été construit (les entrées 1-20 recoupent des sujets déjà intégrés lors de sessions précédentes : PAT GitHub, moindre privilège, serveur proxy, architecture provider, choix Ollama, `CLAUDE.md`).
- **Quatre définitions de glossaire restées vides depuis la session 0** (`Agent IA`, `Skill`, `Claude Code`, `Whisper` — littéralement marquées "*À définir en session 0*" et jamais complétées) : remplies maintenant, avec le vocabulaire harnais/loop déjà utilisé ailleurs dans le carnet.
- **Vérification factuelle plutôt que supposition** : l'entrée 31 du fichier recommandait de démarrer l'accès Calendar en portée `calendar.readonly` (lecture seule) et de n'ajouter l'écriture qu'une fois prêt à tester la création d'événements. Vérifié directement dans le code source du serveur MCP Calendar installé (`~/mcp-servers/google-calendar-mcp/src/`) : le scope réellement demandé, **dès la session 5 (installation initiale, étape 3)**, est `https://www.googleapis.com/auth/calendar` — l'accès complet lecture+écriture, jamais restreint à `readonly` puis élargi comme prévu. Le point n'avait jusqu'ici jamais été vérifié ni documenté explicitement dans le carnet.
- Repéré (sans le vérifier en profondeur, juste noté) : l'entrée 33 décrivait un mécanisme de brouillon **natif** côté serveur MCP Gmail (`draft_email` / `update_draft` / `send_draft` — un vrai brouillon Gmail créé puis envoyé en deux temps). Ce que `gmail_mcp.py` utilise réellement est différent : le "brouillon" n'existe que dans le `<textarea>` du navigateur (texte généré par l'IA, jamais sauvegardé comme brouillon Gmail), et le clic "Envoyer" appelle directement `send_email`. Le résultat côté sécurité est équivalent (rien n'est envoyé sans clic explicite), mais l'implémentation diffère de ce qui avait été anticipé dans la réflexion en amont.

#### Ce qu'on a appris
- **Une recommandation actée "avant de coder" n'est réellement respectée que si elle est revérifiée au moment de coder.** Comme pour le scope Gmail (session 6), ce scope Calendar avait été discuté et une prudence précise recommandée (readonly d'abord) dans un espace de réflexion externe (chat claude.ai) — mais l'installation technique (session 5) a suivi la configuration par défaut du serveur MCP choisi, sans repasser par cette recommandation. Le fichier `explications_techniques_cumulees` documente des **intentions**, pas l'état réel du code — les deux peuvent diverger silencieusement si personne ne les recroise explicitement.
- **Une garantie fonctionnelle équivalente peut être obtenue par un chemin technique différent de celui prévu** (mécanisme de brouillon Gmail natif vs texte côté navigateur) — utile de le savoir, mais ça ne dispense pas de vérifier que la garantie tient vraiment dans l'implémentation choisie, pas seulement dans celle qui avait été anticipée.

#### Points importants à retenir
- **Scope Calendar réellement actif : accès complet lecture+écriture** (`https://www.googleapis.com/auth/calendar`), depuis le tout début de l'étape 3 — pas de restriction `readonly` en place, contrairement à la prudence initialement envisagée. Comme pour Gmail (session 6), c'est un état accepté a posteriori plutôt qu'un choix explicite fait au bon moment.
- Glossaire du carnet maintenant complet — plus aucune entrée "à définir".

#### Questions ouvertes pour la prochaine session
- Décider si le scope Calendar doit être restreint a posteriori (probablement non prioritaire : la capacité d'écriture est maintenant utilisée intentionnellement par `briefing.py`, contrairement au cas Gmail où la lecture était nécessaire mais pas forcément tout le reste du scope `modify`)
- Étape 5, automatisation `systemd`/cron, passe design, Flask vs FastAPI — toujours en attente (inchangé depuis la session 8)

---
 
*Les sessions suivantes s'ajouteront ici au fur et à mesure*