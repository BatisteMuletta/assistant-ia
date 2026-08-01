# À intégrer dans carnet_apprentissage.md — session de conception Projet 2
> Fichier séparé du brief technique pour Claude Code (`brief_projet2_gestionnaire_fichiers.md`). À donner à Claude Code plus tard, uniquement pour mise à jour du carnet — pas des instructions de construction.

---

## Nouvelle entrée — Glossaire cumulatif

| Terme | Définition simple |
|---|---|
| **Harnais d'agent vs API brute (pour les Skills)** | Un harnais d'agent (Claude Code, Claude.ai, Claude Desktop) enveloppe l'appel au modèle avec des fonctionnalités en plus, dont la consultation automatique de Skills : c'est le harnais qui scanne les dossiers Skills et injecte lui-même leur contenu dans le contexte avant l'appel API. L'API brute (`api.anthropic.com/v1/messages`, celle qu'appelle `generer_reponse()`) n'a pas cette fonctionnalité, même avec `tools=` configuré — `tools=` et la consultation de Skill sont deux mécanismes indépendants. Un script qui appelle l'API brute doit lui-même insérer les règles dans le prompt, il ne peut pas compter sur le modèle pour "aller lire" un Skill tout seul. |
| **Tool-calling / function-calling** | Un modèle IA ne peut, par défaut, que produire du texte — jamais agir sur le monde réel. Il ne peut le faire QUE si l'appel API lui donne explicitement une liste d'outils (paramètre `tools=` : fonctions nommées, décrites, avec leurs paramètres). Le modèle demande alors "j'appelle telle fonction avec ces paramètres" — mais c'est toujours le code appelant qui décide d'exécuter réellement ou non. Le modèle demande, il n'exécute jamais lui-même directement. |
| **Contrôle préventif vs contrôle détectif** | Un contrôle préventif empêche une action non conforme de se produire (ex : rejeter un renommage qui changerait de dossier). Un contrôle détectif n'empêche rien mais permet de constater après coup qu'une action a eu lieu, avec quoi et quand (ex : le journal d'activité). Une action automatique sans confirmation humaine ne garde qu'un contrôle détectif comme filet — d'où l'importance de logger sans exception dès qu'une confirmation est retirée. |
| **Permission logicielle vs permission OS** | Une permission OS (`chmod`, droits Unix) est vérifiée par le noyau avant même que le programme s'exécute — barrière externe au code. Une permission logicielle est une règle écrite dans le code lui-même (un `if`) : elle ne protège que si le code l'implémente correctement partout, sans oubli. Le script du Projet 2 tourne avec les droits Linux normaux de l'utilisateur (accès déjà techniquement possible à tout `$HOME`) — la matrice de permissions du Projet 2 est entièrement de ce second type. |
| **Canonicalisation de chemin** | Résoudre un chemin de fichier vers sa forme réelle absolue (`os.path.realpath()`), en particulier en suivant les liens symboliques — nécessaire avant de vérifier qu'un chemin appartient bien à un dossier autorisé, car un chemin "en apparence correct" peut pointer ailleurs. |
| **Lien symbolique (symlink)** | Un fichier qui n'est qu'un raccourci pointant vers un autre emplacement réel du disque. Un programme qui agit sur "le fichier" sans résoudre le lien risque d'agir en réalité sur la cible du lien, potentiellement hors du périmètre prévu. |
| **Fonction centralisée (single entry point)** | Point de passage unique obligatoire pour toutes les opérations d'un même type dans un projet (ex : toutes les actions sur fichiers, ou tous les appels IA via `generer_reponse()`). Réduit la surface de code à auditer et à tester à un seul endroit plutôt que dispersée dans tout le projet. |
| **`CLAUDE.md` vs `SKILL.md` (Claude Code)** | Deux fichiers distincts, rôles différents. `CLAUDE.md` : un seul par projet, toujours chargé automatiquement à chaque session — pour tout ce qui est "dans ce projet, vrai en permanence" (ex : la matrice de permissions du Projet 2, pertinente pour toute tâche touchant un fichier). `SKILL.md` : une capacité réutilisable, chargée seulement quand la tâche en cours y correspond, portable entre plusieurs projets. Séparer les deux évite de tout recharger en permanence (contexte permanent = léger) tout en gardant les procédures ponctuelles disponibles sans les charger à chaque fois (économie de tokens). |
| **Skills API (bêta, API brute)** | Contrairement à une affirmation initiale trop catégorique de cette session, l'API brute a bien un mécanisme Skills — paramètre `container={"skills": [...]}` + outil d'exécution de code sandboxé, fonctionnalité bêta. Nuance : demande de référencer explicitement un `skill_id` à chaque appel (pas de découverte automatique par pertinence comme dans Claude Code), et cible surtout la génération de fichiers via code sandboxé. Disproportionné pour une règle de nommage simple — conclusion pratique inchangée pour `fichiers_manager.py` : insérer les règles dans le prompt reste la bonne approche. |

| **Sous-agent (subagent)** | Une instance Claude séparée, lancée par une session Claude Code (ou un Skill) pour une mission précise et bornée, avec son propre contexte (fenêtre fraîche, n'hérite pas de tout l'historique de la conversation principale) et son propre budget d'appels d'outils/tokens. Tourne en autonomie puis renvoie son résultat à la session appelante. Avantage concret pour un audit de sécurité : un sous-agent qui repart de zéro (sans le contexte de conception complet) est moins susceptible de se contenter de vérifier "est-ce conforme à ce qui était prévu" — il doit retrouver ou contourner les protections par lui-même, plus proche d'une revue réellement indépendante. |

## Nouvelle entrée — Recueil d'exemples commentés

| Brique | Choix fait | Pourquoi |
|---|---|---|
| Boucle de surveillance/rangement fichiers (Projet 2) | Agent IA (harnais + loop) | Plusieurs étapes chaînées avec état entre chaque (détection → permission → lecture → proposition → confirmation → action → log), pas un aller-retour unique |
| Règles de nommage, permissions par zone, structure de dossiers (Projet 2) | Skill au sens du carnet (config `skills_config.json`, insérée manuellement dans le prompt) | Règles fixes réutilisables ; **correction** : un vrai `SKILL.md` Anthropic ne s'applique pas ici même avec tool-calling — ce mécanisme n'existe qu'au niveau des harnais d'agent (Claude Code, Claude.ai, Claude Desktop), pas au niveau de l'API brute qu'appelle `fichiers_manager.py` |
| Mode de détection des nouveaux fichiers (Projet 2) | Pull (scan à la demande sur bouton dashboard), pas événementiel 24/7 | Aucun processus du projet ne tourne en continu à ce jour (Ollama, MCP Calendar, `gmail_watcher.py` — tous manuels) ; ajouter un premier daemon fiable ici aurait été un chantier d'infra à part entière |
| Renommage de fichier (Projet 2) | Tool-calling avec exécution automatique, sans confirmation | Rupture assumée avec le principe "aucun tool-calling" du Projet 1, à des fins pédagogiques ; risque jugé acceptable car contraint au même dossier (pas de changement de zone) et entièrement loggé |
| Déplacement de fichier (Projet 2) | Tool-calling avec confirmation obligatoire | Action à plus forte conséquence que le renommage (changement de zone du fichier, zones à permissions différentes) — garde la confirmation humaine comme point de vérification visuelle |
| Désambiguïsation de dossiers similaires lors d'un rangement global (Projet 2, futur) | Tool-calling avec un outil `lister_fichiers_dans_dossier()`, plutôt que texte+script | Exemple concret où le nombre et la nature des étapes ne peuvent pas être fixés d'avance dans du code Python : pour désambiguïser deux dossiers au nom proche (ex : `Finance` vs `Finance-Internationale`), il faut parfois regarder leur contenu — mais seulement pour les cas ambigus, dont le nombre dépend de ce qui est découvert en cours de route. Le pattern "texte+script" obligerait à tout précharger dans le prompt par avance (gaspillage), alors que le tool-calling permet à Claude de n'appeler l'outil que quand c'est réellement nécessaire, autant de fois que nécessaire |
| Audit de sécurité de `fichiers_manager.py` (Projet 2, observé en direct dans Claude Code) | Skill `security-review`, qui délègue à un sous-agent ("Security review step 1 — identify vulnerabilities", 12 appels d'outils, ~5 min, 58,7k tokens) | Illustration concrète de deux mécanismes vus cette session : un Skill reconnu et chargé automatiquement par pertinence (pas par section de cahier des charges), exécuté via un sous-agent à contexte isolé plutôt que dans le fil de la conversation principale — cohérent avec la recommandation de revue "indépendante" (repartir de zéro plutôt que vérifier la conformité au plan) |

## Nouvelle section — Marche à suivre : audit de fin de brique/projet (Claude Code ↔ Claude)

Procédure réutilisable, pas spécifique au Projet 2, à appliquer à la fin de chaque brique significative ou en fin de projet.

**Étape 1 — Claude Code produit une explication du code construit, avec le vrai code, pas un résumé en prose.** Demander explicitement les extraits exacts (fonctions, logique réelle), pas une paraphrase narrative — sinon on reproduit l'erreur déjà identifiée dans ce projet (rapport technique, section 4) : faire confiance à un résumé d'agent sans vérifier le code réel derrière.

**Étape 2 — Cette explication (avec le vrai code) est transmise à Claude (chat), qui imagine des scénarios de défaillance.** Valeur ajoutée spécifique de cette étape : Claude (chat) porte tout l'historique du projet — cahier des charges, décisions actées, règles explicites (ex : contrainte same-directory sur `renommer_fichier`) — et peut comparer l'implémentation réelle à l'intention documentée, pas seulement chercher des failles génériques. C'est un angle mort différent de ce qu'un audit générique type Skill `security-review` peut voir en partant du code seul, sans connaître les règles spécifiquement décidées pour ce projet.

**Étape 3 — Les scénarios générés sont repassés à Claude Code, qui écrit et exécute de vrais tests automatisés** pour chacun — pas une simple relecture, une vérification reproductible (même principe que section 6c : tests > confiance).

**Point de vigilance** : cette boucle peut recouper partiellement ce qu'un Skill `security-review` automatique fait déjà tout seul dans Claude Code (observé en direct cette session, voir recueil d'exemples) — complémentaire, pas dupliqué à l'identique : la boucle manuelle apporte spécifiquement la comparaison à l'intention documentée du projet, ce que l'audit automatique seul n'a pas forcément.

### Session — Conception Projet 2 (architecture, permissions, tool-calling)
**Étape du projet :** Étape 6 — Skills + structure dossiers + surveillance fichiers (conception, avant construction)

#### Ce qu'on a construit
- Aucun code encore — session de conception pure, en préparation du passage à Claude Code
- Brief technique complet rédigé (`brief_projet2_gestionnaire_fichiers.md`) : architecture, matrice de permissions par zone, méthode de vérification, décision tool-calling

#### Ce qu'on a appris
- Diagnostic outils appliqué au Projet 2 : Agent IA pour la boucle (état entre chaque étape), Skill pour les règles fixes
- Une "permission" définie dans une matrice n'est pas une sandbox OS — c'est une règle logicielle que le code doit implémenter correctement, sans garantie structurelle si un endroit du code est oublié
- Tool-calling : la différence entre un modèle qui *suggère* du texte et un modèle qui *exécute* une action via un outil qui lui est explicitement donné (`tools=`)
- Contrôle préventif (bloque avant) vs contrôle détectif (constate après) — une action automatisée sans confirmation ne garde que le second comme filet
- Canonicalisation de chemin et liens symboliques : un chemin "qui a l'air correct" peut pointer ailleurs, à vérifier avant toute action sur un fichier
- `CLAUDE.md` (contexte permanent, toujours chargé) vs `SKILL.md` (capacité ponctuelle, chargée seulement si pertinente) — deux mécanismes différents de Claude Code, à ne pas confondre ; la matrice de permissions du Projet 2 relève de `CLAUDE.md`, pas d'un Skill
- L'API brute a en réalité un vrai mécanisme Skills bêta (`container={"skills": [...]}`), à ne pas confondre avec la découverte automatique de Claude Code — disproportionné pour un besoin simple comme le nommage de fichiers
- Tool-calling vs texte+script : la vraie différence n'est pas la confirmation (qui dépend uniquement du code), mais la capacité à enchaîner un nombre variable d'étapes décidées en cours de route (ex : désambiguïser des dossiers similaires par exploration), impossible à précalculer entièrement dans un seul prompt
- Sous-agent (subagent) : une instance Claude séparée à contexte isolé, lancée par Claude Code (ou un Skill) pour une mission bornée — observé en direct via `Skill(security-review)` déléguant à un sous-agent pour l'audit de `fichiers_manager.py`

#### Points importants à retenir
- Rupture assumée avec le principe "zéro tool-calling" du Projet 1 — documentée explicitement comme amendement à la règle "Nommage" du cahier des charges v4, pas un oubli
- Renommage automatique strictement contraint au même dossier (sinon = déplacement déguisé, non confirmé) — contrainte non négociable, à couvrir par un test automatisé
- Logging inconditionnel du renommage automatique, seul filet de contrôle a posteriori sur cette action

#### Questions ouvertes pour la prochaine session
- Format exact de `skills_config.json` (mapping extension → dossier, liste des chemins jamais accessibles)
- Structure exacte de `fichiers_traites.json` (déduplication du mode pull)
- Contenu du `SKILL.md` dédié aux outils `renommer_fichier`/`deplacer_fichier`
