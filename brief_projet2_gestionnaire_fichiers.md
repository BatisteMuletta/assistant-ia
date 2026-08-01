# Brief Projet 2 — Gestionnaire de fichiers intelligent
> Document de passage de consigne pour Claude Code. Reflète les décisions actées en session de conception (chat), à date. Étape 5 (Notes → tâches) confirmée terminée par l'utilisateur.

---

## 0. Tool-calling / function-calling — le concept, avec des exemples déjà dans le projet

**Définition fonctionnelle** : un modèle IA ne peut, par défaut, que produire du texte — jamais agir sur le monde réel (envoyer un mail, renommer un fichier). Il ne peut le faire QUE si l'appel API lui donne explicitement une liste d'outils (paramètre `tools=` : fonctions nommées, décrites, avec leurs paramètres). Une fois ces outils donnés, le modèle peut répondre "j'appelle la fonction X avec ces paramètres" — mais c'est toujours le code appelant qui décide d'exécuter réellement cette demande ou non. Le modèle demande, il n'exécute jamais lui-même directement.

**Exemple concret déjà construit : le flux Gmail actuel, sans tool-calling.**
`gmail_mcp.py` + route `/api/gmail/<id>/send` : le modèle ne reçoit jamais `tools=[{"name": "envoyer_email", ...}]`. Le flux réel : (1) Claude, via `generer_reponse()`, reçoit le mail et répond en texte — un brouillon, une chaîne de caractères, rien de plus ; (2) le texte est affiché dans le dashboard ; (3) l'utilisateur clique "Envoyer" ; (4) **Python** (`gmail_mcp.envoyer_email()`), pas Claude, exécute l'envoi réel, déclenché par le clic humain. Le modèle n'a jamais eu le pouvoir technique d'envoyer quoi que ce soit — vérifié explicitement par `grep tools=` dans `ia_provider.py` lors de l'audit de sécurité (rapport technique, section 4) : zéro résultat.

**Le même schéma transposé au Projet 2 (renommer un fichier) :**
- *Sans tool-calling* : Claude reçoit le contenu du fichier, répond en texte (ex : `"2026-08-01_Cours_Rapport-Finance.pdf"`) — une suggestion, rien de plus. L'utilisateur confirme. Python (`shutil.move()`) exécute le renommage. Claude n'a jamais d'accès direct au disque.
- *Avec tool-calling* : on donne à Claude un outil `renommer_fichier(chemin, nouveau_nom)`. Claude peut alors décider lui-même, dans sa propre réponse, d'appeler cette fonction — et si le code exécute cette demande sans étape humaine intermédiaire, c'est Claude qui déclenche l'action réellement, pas un texte relu avant d'agir.

**⚠️ Mise à jour — décision finale en section 10 : le Projet 2 utilise bien le tool-calling**, à la différence du Projet 1. Cette section 0 reste comme référence pédagogique du concept général et de ce qui a été écarté puis reconsidéré ; voir section 10 pour l'architecture réellement retenue (renommage automatique via tool-calling contraint, déplacement avec confirmation).

**Pourquoi le passage à un vrai watchdog (24/7, section 2) ne change rien à cette question.** Que le scan de `~/Downloads` soit déclenché par un clic (pull) ou par un script qui tourne en continu et réagit à l'instant où le fichier arrive (watchdog), le déclencheur du scan est indépendant de la question tool-calling/Skill — ce sont deux décisions distinctes, voir section 10 pour l'état final de la seconde.

## 1. Architecture générale

- **Tool-calling utilisé, à la différence du Projet 1.** `tools=` configuré dans l'appel API pour deux fonctions précises (`renommer_fichier`, `deplacer_fichier`) — détail complet et garde-fous en section 10. Rupture assumée avec le principe du Projet 1 (`ia_provider.py`, aucun `tools=` — vérifié par grep lors de l'audit de sécurité étape 3-4) ; la rupture est documentée et volontaire, pas un oubli de cohérence.
- **Diagnostic outils (arbre de décision du carnet) :**
  - Boucle de surveillance/rangement → **Agent IA** (harnais + loop) — plusieurs étapes chaînées avec état entre chaque (détection → permission → lecture → proposition → confirmation → action → log), pas un aller-retour unique.
  - Règles de nommage, permissions de lecture, structure de dossiers → **Skill** (au sens large du carnet, voir section 6a) — plus, pour les deux outils de tool-calling spécifiquement, un vrai `SKILL.md` au sens Anthropic (section 10).

## 2. Mode de détection : pull (scan à la demande), pas événementiel 24/7

- Pas de process qui tourne en continu pour l'instant. Cohérent avec l'état réel actuel du projet : Ollama non lancé au dernier rapport, serveur MCP Calendar à relancer manuellement à chaque session, `gmail_watcher.py` jamais lancé en continu (dette technique déjà identifiée dans le rapport du 19/07).
- Fonctionnement retenu : bouton dans le dashboard → scan de `~/Downloads` → comparaison à un fichier d'état des fichiers déjà vus/traités (`fichiers_traites.json`, même principe que `mails_notifies.json` existant) → affichage uniquement de la différence (nouveaux fichiers).
- Notification temps réel façon `inotify`/`watchdog` (processus 24/7, réagit à l'instant où le fichier arrive) explicitement écartée pour cette étape — voir section 5.

## 3. Interface de confirmation

- Réutilisation de la zone dashboard existante **"Suggestions Claude"** — déjà le pattern texte + bouton confirmer/ignorer (utilisé pour les deadlines à l'étape 4). Aucune modification du layout figé depuis l'étape 1.
- Routes Flask attendues (à créer dans `server.py`, protégées par `_origine_locale()` comme les routes mutantes existantes) :
  - `POST /api/fichiers/scan` — détecte les nouveaux fichiers dans `~/Downloads`, ne modifie rien, ne lit aucun contenu.
  - `POST /api/fichiers/<id>/lire` — lit le contenu, uniquement après autorisation explicite de l'utilisateur pour ce fichier précis. Déclenche ensuite l'appel avec `tools=` : le renommage (`renommer_fichier`) s'exécute automatiquement à ce stade (section 10), sans passage par cette route de confirmation.
  - `POST /api/fichiers/<id>/confirmer` — exécute uniquement le déplacement (`deplacer_fichier`) vers le dossier proposé, sur clic explicite. Affiche le nom déjà renommé + le dossier de destination proposé.
- Nouveau module attendu : `fichiers_manager.py` (surveillance + actions FS), suivant le même principe de séparation que `gmail_mcp.py` / `calendar_mcp.py`.

## 4. Matrice de permissions par zone du système de fichiers

**Note de mécanisme, importante pour Claude Code** : cette matrice n'est pas une sandbox au niveau OS. Le script tourne avec les droits Linux normaux de l'utilisateur (accès déjà techniquement possible à tout `$HOME`). Chaque ligne ci-dessous est une règle **logicielle** à implémenter explicitement dans `fichiers_manager.py` — une vérification en code avant chaque action, pas une protection qui existe indépendamment du code écrit.

| Zone | Lecture des noms | Lecture du contenu | Renommer/déplacer | Supprimer/modifier |
|---|---|---|---|---|
| **`$HOME` (hors caché), hors zones ci-dessous** | Toujours (sert uniquement à repérer les dossiers/catégories existants pour bien classer un nouveau fichier — jamais besoin du contenu pour ça) | **Jamais** | — | — |
| **`~/Downloads`** | Toujours | Sauf autorisation à chaque fois (le fichier concerné, un par un) | Sauf autorisation | Sauf autorisation |
| **Fichiers/dossiers cachés (`.ssh`, `.config`...)** | Jamais | Jamais | Jamais | Jamais |
| **`~/projets/Cours/`** | Toujours | Librement, sans demander — sandbox pédagogique assumé, cantonné strictement à ce dossier | Librement, sans demander | Autorisation requise |
| **`~/Perso/`, `~/Pro/`** *(par défaut, non objecté — traité comme hypothèse validée)* | Toujours | Sauf autorisation à chaque fois | Sauf autorisation | Sauf autorisation |

**Canonicalisation obligatoire avant toute action** : quel que soit le chemin proposé par l'IA (destination suggérée par `generer_reponse()`), le code doit d'abord le résoudre en chemin réel absolu (`os.path.realpath()` — résout aussi les liens symboliques) puis vérifier qu'il tombe bien à l'intérieur d'un dossier de la liste autorisée, jamais se fier au texte du chemin tel quel. Motif : un chemin suggéré du type `../../../etc/` ou un fichier-lien symbolique pointant hors des zones prévues doit être rejeté même s'il "a l'air" correct en apparence.

## 5. Points de vigilance

1. **Périmètre "tout l'ordinateur" resserré** — passé de "sauf caché" (n'excluait que les dotfiles, pas `/etc`, `/var`, d'autres comptes) à `$HOME`. Lecture de noms uniquement, contenu jamais — tranché.
2. **`~/projets/Cours/` : accès large confirmé comme choix assumé**, sandbox pédagogique volontairement cantonné à ce seul dossier. Reste une asymétrie interne non résolue (renommer/déplacer libre vs supprimer/modifier restreint) — pas bloquant, à garder en tête si un renommage non désiré devient gênant.
3. **`~/Perso/` et `~/Pro/`** : traitement par défaut confirmé faute d'objection — même régime que `Downloads`.
4. **Pas de liste prédéfinie de matières/catégories.** Les matières du mastère n'étaient pas connues au moment du cahier des charges v4. Solution retenue : pas besoin d'une liste figée — la lecture des noms de dossiers existants (zone `$HOME`, section 4) permet à l'IA de proposer une catégorie en la faisant correspondre à un dossier déjà existant, ou d'en proposer une nouvelle sinon, validée par confirmation utilisateur avant création. Dynamique plutôt que statique, cohérent avec pourquoi la lecture des noms a été élargie en premier lieu.
5. **Journal d'activité : réutilisation de `activity_log.json` existant**, plutôt qu'un fichier de log séparé pour le Projet 2 — un seul journal centralisé, cohérent avec la zone unique "Journal d'activité" déjà présente sur le dashboard. Le format d'exemple donné dans le cahier des charges (section Projet 2) sert de structure d'entrée, pas de fichier séparé.
6. **Aucune décision prise sur le détail d'implémentation restant** : structure exacte de `fichiers_traites.json`, format exact de `skills_config.json` (mapping extension → dossier, liste des chemins jamais accessibles) — laissé à la phase de construction avec Claude Code.

## 10. Décision finale d'architecture — tool-calling avec split renommer/déplacer

**Choix acté** : le Projet 2 utilise du vrai tool-calling (paramètre `tools=` configuré), à la différence du Projet 1. Deux outils distincts exposés au modèle :

- **`renommer_fichier(chemin_actuel, nouveau_nom)`** — exécuté **automatiquement, sans confirmation**, dès que la lecture du contenu a été autorisée pour ce fichier (section 4). Contrainte de sécurité non négociable : cette fonction doit vérifier que `nouveau_nom` reste **dans le même dossier** que `chemin_actuel` — tout appel qui tenterait de changer de dossier via cet outil doit être rejeté (sinon un renommage pourrait déguiser un déplacement non confirmé). À couvrir explicitement par un test automatisé (section 6c, point 2) et vérifié par `grep` que ce garde-fou existe bien dans le code. **Logging obligatoire sans exception**, même sans confirmation utilisateur — c'est le seul filet de contrôle a posteriori sur cette action automatique.
- **`deplacer_fichier(chemin_actuel, dossier_destination)`** — exécuté **uniquement après confirmation explicite** dans la zone Suggestions du dashboard. La confirmation affiche à la fois le nom du fichier (déjà renommé à ce stade) et le dossier de destination proposé — c'est le point de vérification visuelle réel avant toute action de plus haute conséquence (changement de zone du fichier).

**Amendement explicite à la règle "Nommage" du cahier des charges v4** : la règle *"Claude suggère toujours, n'applique jamais sans confirmation"* est modifiée pour l'action de renommage spécifiquement — remplacée par le principe ci-dessus (renommage automatique contraint + loggé, confirmation reportée sur le déplacement). Décision assumée consciemment le 01/08/2026, pas un oubli : le renommage seul (sans changement de dossier) est jugé à conséquence suffisamment faible et réversible (fichier au même endroit, ancien nom conservé dans le journal) pour ne pas nécessiter de confirmation séparée, tant que la contrainte same-directory est respectée.

**Bénéfice pédagogique confirmé** : ce choix introduit du vrai tool-calling, ce qui justifie et rend pertinent un vrai `SKILL.md` (section 6a) dédié à ces deux outils — contrairement au Projet 1, où l'absence de tool-calling rendait un Skill de production sans objet.

Le mot "Skill" recouvre deux réalités distinctes dans ce projet, à ne pas confondre :

- **Skill au sens Anthropic** : un dossier contenant au minimum un `SKILL.md` (manuel de procédure : quand l'utiliser, comment faire, pièges à éviter, exemples), consulté par **Claude lui-même** à l'exécution, quand il reconnaît que la tâche en cours correspond à ce skill. N'a de sens que si c'est Claude qui exécute la tâche en relisant les instructions à chaque fois — jamais le cas ici, puisque `fichiers_manager.py` tourne seul, sans tool-calling (section 1).
- **"Skill" au sens du carnet** (arbre de décision) : *"règle fixe, réutilisable, apprise une fois pour toutes"* — définition volontairement générique du projet, pas le mécanisme produit.

**Conséquence pour Projet 2** : les règles de nommage, le mapping extension→dossier, la liste des chemins jamais accessibles finiront en **`skills_config.json`**, un simple fichier de config lu par du code Python classique — pas un vrai Skill Anthropic. Pour la suggestion de nom de fichier en particulier : ça reste un appel direct à `generer_reponse()` avec les règles de nommage insérées dans le prompt lui-même, pas une consultation de dossier Skill.

**Un vrai `SKILL.md` aurait un usage séparé et légitime** : comme mémoire procédurale pour **Claude Code** (l'outil de développement), pour qu'il se souvienne automatiquement de la matrice de permissions (section 4) et de la méthode de vérification (section 6b) à chaque nouvelle session de code sur ce projet, sans avoir à tout recoller. Ce cas d'usage ne dépend pas du mode de déclenchement pull vs watchdog (section 2) — il concerne l'outil de développement, pas le comportement du script en production, quel que soit son mode de déclenchement.

## 6b. Coût : pourquoi l'absence de tool-calling est aussi un choix économique

Pas seulement une question de cohérence architecturale (section 1) — aussi une question de coût direct. Le tool-calling fait gonfler la facture de deux façons : les définitions d'outils sont réinjectées à chaque tour de la conversation (tokens facturés), et une tâche peut nécessiter plusieurs allers-retours modèle↔outil avant d'aboutir (plusieurs appels API pour une seule décision). Le pattern retenu ici — un script qui appelle `generer_reponse()` une seule fois par fichier pour obtenir uniquement une suggestion de nom — reste au plus près d'un aller-retour unique par fichier, quel que soit pull ou watchdog.

## 6c. Méthode de vérification du code — pas de confiance aveugle envers l'IA qui écrit `fichiers_manager.py`

Principe : une règle qui n'existe que dans la logique applicative (section 4) n'est vraie que si le code l'implémente correctement, partout, tout le temps — ce n'est jamais une garantie structurelle comme une vérification faite par le système d'exploitation lui-même (même leçon que CORS, étape 3-4). Donc vérifier plutôt que faire confiance :

1. **Fonction centralisée unique** (ex : `executer_action_fichier(zone, action, chemin)`) que tout le code doit obligatoirement appeler pour toute opération sur un fichier — même principe que `generer_reponse()` qui centralise déjà tous les appels IA du projet. Réduit la surface à auditer à un seul endroit.
2. **Tests automatisés** sur cette fonction centrale : tenter explicitement de lire `.ssh/config`, de déplacer vers `../../../etc/`, de suivre un lien symbolique piégé — vérifier que chaque cas est bien bloqué. Exécutable à volonté, réponse factuelle (vert/rouge), pas d'interprétation.
3. **Audit exhaustif par recherche** (`grep`) de tous les appels à `shutil.move`, `os.rename`, `open(` dans le code, vérification que chacun passe bien par la fonction centralisée — même méthode que l'audit de sécurité du Projet 1 (rapport technique, section 4).
4. **Revue croisée par un second agent/modèle**, comme pour l'audit CSRF du Projet 1 (un agent construit, un autre — Fable dans ce précédent — relit indépendamment).
5. **Logging exhaustif** (déjà une règle actée du projet) comme filet de sécurité a posteriori : si un bug de la matrice laisse passer une action non prévue malgré tout, le journal permet de le détecter après coup.

## 7. Entrées à ajouter au carnet d'apprentissage (`carnet_apprentissage.md`)

### Glossaire cumulatif — nouveaux termes de cette session
| Terme | Définition simple |
|---|---|
| **Permission logicielle vs permission OS** | Une permission OS (`chmod`, droits Unix) est vérifiée par le noyau avant même que le programme s'exécute — barrière externe au code. Une permission logicielle est une règle écrite dans le code lui-même (un `if`) : elle ne protège que si le code l'implémente correctement partout, sans oubli. Le script du Projet 2 tourne avec les droits Linux normaux de l'utilisateur (accès déjà techniquement possible à tout `$HOME`) — la matrice de permissions du Projet 2 est entièrement de ce second type. |
| **Canonicalisation de chemin** | Résoudre un chemin de fichier vers sa forme réelle absolue (`os.path.realpath()`), en particulier en suivant les liens symboliques — nécessaire avant de vérifier qu'un chemin appartient bien à un dossier autorisé, car un chemin "en apparence correct" peut pointer ailleurs. |
| **Lien symbolique (symlink)** | Un fichier qui n'est qu'un raccourci pointant vers un autre emplacement réel du disque. Un programme qui agit sur "le fichier" sans résoudre le lien risque d'agir en réalité sur la cible du lien, potentiellement hors du périmètre prévu. |
| **Fonction centralisée (single entry point)** | Point de passage unique obligatoire pour toutes les opérations d'un même type dans un projet (ex : toutes les actions sur fichiers, ou tous les appels IA via `generer_reponse()`). Réduit la surface de code à auditer et à tester à un seul endroit plutôt que dispersée dans tout le projet. |
| **Confiance vs vérification (méthode)** | Faire confiance à du code écrit par une IA repose sur une expectative non testable. Vérifier repose sur des méthodes reproductibles et factuelles : tests automatisés qui tentent explicitement de casser une règle, audit par recherche exhaustive (`grep`) dans le code réel, revue croisée par un second modèle. Les trois méthodes ne suppriment pas le risque zéro, mais remplacent un pari par une procédure répétable. |

### Recueil d'exemples commentés — nouvelle ligne
| Brique | Choix fait | Pourquoi |
|---|---|---|
| Boucle de surveillance/rangement fichiers (Projet 2) | Agent IA (harnais + loop), sans tool-calling — le modèle ne produit que du texte/JSON, le code Python exécute les actions réelles | Plusieurs étapes chaînées avec état entre chaque (détection → permission → lecture → proposition → confirmation → action → log) ; cohérence maintenue avec le choix déjà audité du Projet 1 de n'avoir aucun `tools=` nulle part |
| Règles de nommage, permissions par zone, structure de dossiers (Projet 2) | Skill | Règles fixes, apprises une fois, réutilisées identiquement à chaque exécution — pas de raisonnement à refaire à chaque fichier |
| Mode de détection des nouveaux fichiers (Projet 2) | Pull (scan à la demande sur bouton dashboard), pas événementiel 24/7 (`inotify`/`watchdog`) | Aucun processus du projet ne tourne en continu à ce jour (Ollama, MCP Calendar, `gmail_watcher.py` — tous manuels) ; ajouter un premier daemon fiable ici aurait été un chantier d'infra à part entière, pas un détail de cette étape |

## 6. Reporté — non traité dans cette session

**Script de notification temps réel (surveillance 24/7 façon `inotify`/`watchdog`)** : volontairement mis de côté pour cette étape. Le mode pull (scan à la demande) suffit pour démarrer sans ajouter un chantier d'infra (process persistant, gestion de crash, démarrage auto) en plus du reste. À rediscuter **une fois le serveur (Flask) et son infra de lancement automatisés** (le rapport technique note déjà que `systemd`/cron n'est configuré pour aucun processus du projet à ce jour) — pas avant.
