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
 
*Les sessions suivantes s'ajouteront ici au fur et à mesure*