# Étape 10 — Infrastructure ThinkCentre M700
> Positionnée après la fin du Projet 3 (donc après l'étape 9 du plan de construction) — pas entre Projet 1 et Projet 2 comme envisagé initialement. Choix explicite : construire Projet 2 et Projet 3 d'abord sur l'architecture actuelle (X260 seul), pour connaître les vrais besoins avant de dimensionner le serveur.
> Document de travail — à transmettre à Claude Code pour exécution
> Rédigé le 29/07/2026, dernière révision de séquencement le même jour

---

## 1. Objectif de cette étape

Mettre en place le ThinkCentre M700 comme **serveur domestique généraliste, headless (= piloté à distance, sans écran/clavier qui lui sont propres en usage normal), allumé 24/7**, une fois les Projets 1, 2 et 3 terminés sur l'architecture X260 seul. Disponible ensuite pour étendre le projet assistant-ia et pour des usages futurs non encore spécifiés (hébergement d'un site perso, scripts tournant pendant la nuit, etc.).

**Ce que cette étape N'EST PAS** : elle ne construit aucun service métier spécifique du projet assistant-ia. Elle amène la machine à un état fonctionnel, sécurisé, joignable, et généraliste — prête à recevoir un rôle précis le jour où le besoin se confirme. Les Projets 2 et 3 ne dépendent pas de cette étape et se construisent normalement sur le X260 seul avant qu'elle n'ait lieu.

---

## 2. Profil matériel (vérifié)

| Champ | Valeur |
|---|---|
| Modèle | Lenovo ThinkCentre M700 **Tiny** (format ultra-compact ~1L) |
| Machine Type / Model | 10HY / 0052FR |
| CPU | Intel Core i5-6400T — 4 cœurs / 4 threads, 2.2 GHz base / 2.8 GHz max |
| RAM d'usine | 4 Go DDR4-2133 (2 slots SO-DIMM, max 32 Go) |
| Stockage | SSD 256 Go (2.5" SATA) + 1 slot M.2 SATA libre (extension future possible) |
| Graphique | Intel HD 530 intégré — **aucun slot PCIe, GPU dédié impossible** |
| Réseau | Ethernet Gigabit + WiFi ac + Bluetooth 4.1 |
| Alimentation | Bloc externe 65W — faible consommation au repos, adapté à un usage 24/7 |
| OS d'usine | Windows 10 Pro (support Microsoft terminé oct. 2025 — remplacé, voir §3) |

---

## 3. Décisions actées pour cette étape

| Sujet | Décision |
|---|---|
| **OS** | Ubuntu **Server** 26.04 LTS "Resolute Raccoon" (sortie 23/04/2026, support standard jusqu'en 2029) — à revérifier au moment de l'implémentation si une version LTS plus récente est sortie entretemps, vu le report de cette étape. Pas de Desktop : aucune interface graphique nécessaire, empreinte mémoire minimale, pilotage 100% SSH. |
| **RAM** | Démarrage avec **8 Go** (1 barrette Samsung DDR4-2400 SO-DIMM déjà en possession — compatible malgré la fréquence supérieure à ce que la carte mère supporte officiellement en DDR4-2133, elle tournera simplement bridée à cette vitesse). Upgrade à 16 Go (2ème barrette identique, ~15-25€) différé et déclenché seulement si le besoin se confirme après test réel des modèles Whisper (§4.3) — "medium" tourne serré sur 8 Go (~1 Go de marge), "small" reste confortable. |
| **Chiffrement disque** | **Non** — disque en clair. Machine qui reste physiquement à la maison, risque de vol jugé faible ; pas de contrainte particulière. |
| **Réseau physique** | Ethernet filaire (prise disponible près de l'emplacement prévu) — pas de WiFi, pour éviter coupures/portée. |
| **Adressage réseau** | Réservation DHCP sur la box (IP locale fixe, attribuée via l'adresse MAC de la machine) comme référence pour tous les scripts du projet. mDNS (`assistant-server.local`) en confort optionnel, jamais comme dépendance critique. |
| **Nom d'hôte** | `assistant-server` |
| **Compte utilisateur** | `batiste`, avec droits sudo (pas de connexion root directe). |
| **Fuseau horaire** | `Europe/Paris` — pertinent notamment pour un futur brief automatique programmé (§4.1). |
| **Redémarrage après coupure de courant** | Activé (réglage BIOS "AC Power Recovery" / "Power On after Power Loss") — la machine se rallume seule après une coupure, sans intervention manuelle. Essentiel pour un serveur 24/7 sans surveillance. |
| **Emplacement physique** | À définir par l'utilisateur (ventilation à surveiller sur un usage 24/7, consommation faible donc peu contraignant). |
| **Accès distant (administration)** | Réseau local uniquement pour l'instant. Aucune exposition sur l'internet public pour SSH. Si un besoin d'accès administratif depuis l'extérieur apparaît plus tard : Tailscale (plan Personal, gratuit) pour un accès privé, indépendamment de la question du site web public (voir §4.4). |
| **Authentification SSH** | Par clé uniquement (pas de mot de passe). Vérifier si une paire existe déjà sur le X260 (`ls -la ~/.ssh/`), sinon en générer une (`ssh-keygen -t ed25519`) au moment du montage. |
| **Port SSH** | Standard (22). Un port custom n'apporte rien de concret ici : la machine n'est de toute façon pas exposée à internet sur ce port, donc il n'y a pas de bots à repousser. |
| **fail2ban** | Écarté. Protège contre le bruteforce par mot de passe — or l'authentification par mot de passe est déjà désactivée, il n'y a rien à deviner. Redondant avec une mesure plus radicale déjà en place. |
| **Pare-feu** | `ufw` activé, SSH autorisé uniquement depuis le réseau local au démarrage — règles supplémentaires ajoutées au cas par cas quand un rôle concret est déployé (ex: le futur reverse proxy, voir §4.4). |
| **Mises à jour** | Automatiques pour la sécurité uniquement (`unattended-upgrades`, limité aux patchs de sécurité). Le reste (montées de version, nouveaux paquets) reste manuel et validé par l'utilisateur — cohérent avec la règle projet "rien sans validation explicite". |
| **Reverse proxy + conteneurisation** | **Caddy** (reverse proxy — reçoit les requêtes web entrantes et les redirige vers le bon site/appli selon l'adresse demandée ; choisi plutôt que nginx pour sa gestion automatique des certificats HTTPS et sa configuration plus simple) + **Docker** (fait tourner chaque site/appli dans son propre environnement isolé, sans interférence entre projets) installés dès cette étape, comme capacité générale — sans site précis à héberger pour l'instant. |
| **Sauvegarde système M700** | Pas d'image système (Clonezilla ou équivalent) — les données précieuses (fichiers de cours) vivent sur Google Drive, pas sur le M700 ; la configuration système est déjà entièrement documentée ici et rapide à refaire (~1h-1h30, voir §7) en cas de panne disque. |
| **Mises à jour des futurs conteneurs Docker** | Automatiques, cohérent avec le choix déjà fait pour l'OS — via un outil comme **Watchtower** (conteneur qui surveille et met à jour les autres conteneurs) une fois que des services existent. À restreindre aux versions mineures/patchs (tags de version épinglés, pas `latest` en aveugle) pour éviter qu'une montée de version majeure casse silencieusement un site en production. |
| **Rôle métier immédiat** | Aucun. Machine généraliste, prête à l'emploi. |

---

## 4. Usages potentiels identifiés — à évaluer une fois cette étape en place

Puisque cette étape n'arrive qu'après la fin des Projets 2 et 3, les besoins réels de ces deux projets seront déjà connus (contrairement à une évaluation spéculative faite en amont). Ces pistes restent néanmoins des décisions à prendre à ce moment-là, pas des rôles déjà construits.

### 4.1 Brief automatique du matin (9h)
- **Principe** : à 9h, un script planifié (cron/systemd timer) sur le M700 exécute de façon autonome toute la chaîne du briefing (mails urgents → événements du jour → lecture des corps de mail → détection de deadlines → rédaction du texte), sans dépendre de l'état du X260 (éteint ou non).
- **Implications techniques actées à l'avance** :
  - MCP Calendar **et** MCP Gmail doivent tourner/être invocables depuis le M700 (pas seulement Calendar) — le script du matin lit les mails lui-même.
  - Identifiants OAuth Gmail à dupliquer ou reconfigurer sur le M700.
  - L'étape IA (détection de deadlines + rédaction) **doit passer par l'API Anthropic, pas par Ollama** — Ollama reste sur le X260 (voir §5), qui ne sera pas joignable à 9h si le laptop est éteint. Coût : appel API payant quotidien, modeste, accepté explicitement par l'utilisateur.
  - Résultat écrit dans un fichier lisible par le dashboard (sur le X260) à l'ouverture — mécanisme de partage exact à définir au moment de la construction.
  - Réappliquer le patch local non versionné du bug MCP Calendar (réutilisation de connexion stateless, déjà documenté dans le rapport technique) si ce service est déployé sur le M700.

### 4.2 NAS pour le Projet 2 (gestionnaire de fichiers)
- Piste : centraliser `~/Cours`, `~/Perso`, `~/Pro` sur le M700 via **Samba/SMB** (protocole de partage réseau compatible nativement Linux et Windows — cohérent avec la migration Windows prévue ; NFS serait Linux-only, écarté).
- Flux envisagé : téléchargements et logique de tri/renommage restent sur le X260 (c'est là que ça se passe), seule la destination finale du rangement pointe vers le partage réseau.
- **Note de cohérence avec le §4.3** : le pipeline Whisper (ci-dessous) dépose finalement ses résultats sur Google Drive plutôt que sur ce NAS local — le NAS reste pertinent pour d'autres catégories de fichiers (téléchargements généraux, Perso, Pro), mais son rôle vis-à-vis des fichiers de cours est à reconsidérer une fois les deux pistes en place.
- Projet 2 sera déjà terminé et fonctionnel sur le X260 seul au moment de cette étape — décision à prendre en fonction de l'usage réel constaté, pas en spéculant à l'avance.

### 4.3 Pipeline transcription Whisper pour le Projet 3 — architecture validée
- **Flux complet retenu** :
  1. Enregistrement manuel via l'appli **Notes vocales** native de l'iPad (plus fiable qu'une page web dans Safari, qui risque d'être suspendue par iOS en arrière-plan pendant 1-2h de cours). Vérifier que le mode d'enregistrement est en qualité standard/compressée (AAC, ~80-100 Mo pour 3h) et non en mode "sans perte" (Réglages → Dictaphone → Qualité audio), qui multiplierait la taille par 15-20x sans bénéfice pour de la voix.
  2. Dépôt manuel du fichier audio par l'utilisateur dans un dossier **Google Drive** partagé, accessible via un connecteur Claude — choisi plutôt qu'un NAS local car consultable depuis n'importe quelle conversation Claude.ai, peu importe où l'utilisateur se trouve, sans dépendre du réseau domestique. **Compte utilisé : l'adresse Gmail principale de l'utilisateur** (pas un compte dédié séparé) — choix conscient, les fichiers de cours cohabitent avec le reste du compte perso.
  3. À 21h (cron/systemd timer sur le M700), un script récupère le fichier via l'**API Google Drive** (nécessite un projet Google Cloud + identifiants OAuth — même type de configuration déjà réalisée pour Gmail et Calendar). **Le script ne retraite un dossier de cours que si un fichier à l'intérieur a changé depuis le dernier traitement réussi** (comparaison de date de modification) — évite un retraitement infini de tous les dossiers accumulés depuis le début du semestre à chaque exécution, ce qui ferait gonfler le coût API de façon incontrôlée au fil du temps (voir chiffrage ci-dessous).
  4. **Whisper transcrit en local sur le M700** (whisper.cpp ou faster-whisper, pas l'implémentation Python d'origine — nettement plus rapide en CPU pur). Ordre de grandeur pour 3h d'audio, à confirmer par un test réel une fois la machine montée : ~1h30-3h avec le modèle "small", ~3h-6h avec "medium" (recommandé si vocabulaire technique dense, `small` perd en précision sur du français spécialisé). **Choix du modèle par défaut non tranché à l'avance** : tester les deux sur les premiers cours réels une fois le pipeline en place, comparer qualité/temps concrètement, puis fixer un choix par défaut sur cette base plutôt que de deviner à l'avance.
  5. Le script appelle l'**API Anthropic** pour générer le résumé (même mécanisme que `generer_reponse()` dans `ia_provider.py`).
  6. Transcription + résumé, renommés et organisés, redéposés dans le même dossier Drive. **Copie intacte du support original conservée à côté de la version annotée** (§4.3.1) — filet de sécurité si l'annotation casse une mise en page complexe.
  7. **Le fichier audio brut est supprimé de Google Drive immédiatement après une transcription réussie** — cohérent avec la règle déjà actée du cahier des charges principal (suppression de l'audio après traitement), étendue à sa copie temporaire cloud pour limiter la fenêtre d'exposition.
  8. **Toute copie locale temporaire téléchargée sur le M700 pour le traitement (audio, support) est supprimée une fois le traitement terminé** — les fichiers vivent sur Drive, pas de raison de les accumuler aussi en local sur les 256 Go du SSD au fil du semestre.
  9. **En cas d'échec** (transcription ratée, appel API en erreur, etc.) : notification push via **ntfy** (appli gratuite à installer sur le téléphone, abonnement à un canal que le M700 utilise pour publier ses alertes — pas lié à un numéro, gratuit, aucun compte tiers à créer). Contrairement à `gmail_watcher.py` où une notification avait été jugée superflue, elle est justifiée ici : ce pipeline n'a aucune validation manuelle (voir ci-dessous), un échec silencieux pourrait passer inaperçu longtemps.
- **Chiffrage du coût API (Claude Haiku 4.5, tarif vérifié : 1$/million tokens en entrée, 5$/million en sortie)** :
  - Résumé (§4.3) : ~35 000 tokens transcription en entrée + ~1 200 en sortie ≈ **0,04$/cours**.
  - Mise en correspondance/annotation (§4.3.1) : transcription(s) + contenu de tous les supports du dossier en entrée, annotations en sortie ≈ **0,065$/cours**.
  - **Total : ~0,10€/cours traité**, soit environ **2-4€/mois** pour un rythme de 3-4 cours/semaine — largement dans le plafond existant (5$/7$), à condition que le correctif anti-retraitement infini (point 3 ci-dessus) soit bien en place.
- **Exception actée à la règle projet "Claude ne fait rien sans validation"** : ce pipeline s'exécute de bout en bout sans validation manuelle avant le rangement final dans Drive. Justification explicite de l'utilisateur : risque d'erreur faible (un mauvais nom ou classement se corrige facilement après coup), aucune donnée irréversible en jeu. Décision assumée comme exception ponctuelle, pas comme un changement de la règle générale du projet.
- **Point de vigilance confidentialité** : contredit partiellement le principe "Whisper en local pour rester confidentiel" du cahier des charges principal de Projet 3, puisque l'audio brut transite temporairement par les serveurs Google avant traitement. Fenêtre limitée par la suppression immédiate post-traitement (point précédent).
- **Piste complémentaire — accès direct depuis la salle de cours** (hors réseau domestique, si besoin d'uploader avant 21h sans attendre de rentrer) : Tailscale installé sur le M700 et l'appareil source (plan Personal, gratuit) — indépendant du choix Google Drive, à évaluer séparément si le besoin se confirme.
- **Organisation Drive : un sous-dossier par cours/séance** (ex: `2026-09-15_Marketing/`), contenant l'audio et le(s) support(s) de ce cours. Choisi plutôt qu'une convention de nommage par préfixe — plus simple à respecter au moment du dépôt (glisser des fichiers dans un dossier plutôt que renommer soigneusement chaque fichier), et reste lisible même relu des mois après.
- Projet 3 sera déjà terminé et fonctionnel sur le X260 seul au moment de cette étape — cette architecture s'ajoute par-dessus, une fois le besoin réel confirmé.

### 4.3.1 Extension — annotation des supports de cours avec les propos oraux du prof
- **Objectif** : en plus du résumé (§4.3), générer une version du support de cours (PowerPoint, PDF, ou Word — les trois seront construits, un par un, au fil des cours réels, aucun format dominant chez les profs) où les propos oraux du prof sont insérés directement en annotation sur les slides/pages/sections concernées.
- **Mécanisme de mise en correspondance : par le contenu, pas par le minutage.** Aucune synchronisation native entre "minute X de l'audio" et "slide Y du support" — l'IA reçoit le texte extrait de chaque slide/page/section ET la ou les transcriptions complètes, et déduit elle-même quel passage parlé correspond à quel endroit du support, par proximité de sujet. Choisi explicitement plutôt qu'un minutage manuel (trop de friction pendant un cours), notamment parce que l'ordre du cours ne suit pas toujours l'ordre du support.
- **Traitement par lot, dossier entier, pas fichier par fichier** : un cours peut avoir plusieurs audios pour un même support, ou un audio qui couvre plusieurs supports (many-to-many) — le script donne à l'IA, en une fois, tous les supports et toutes les transcriptions du sous-dossier, clairement étiquetés (Support A / Support B / Audio 1 / Audio 2...), pour qu'elle fasse la mise en correspondance sur l'ensemble du lot plutôt que par paire fixe.
- **Retraitement à chaque exécution de 21h** : plutôt que de détecter artificiellement "le dossier est complet", le script retraite l'état actuel du dossier à chaque passage — un fichier ajouté plus tard (support déposé après l'audio, ou audio d'une session suivante) est automatiquement pris en compte au prochain passage, sans logique de détection de fin à construire.
- **Extraction du contenu du support, selon le format** :
  - PowerPoint : `python-pptx`, découpage net slide par slide.
  - Word : `python-docx`, découpage plus grossier (par section/titre, pas de pagination native).
  - PDF : texte réel sélectionnable côté profs (confirmé, pas de scan) — extraction directe, pas besoin d'OCR.
- **Réinsertion des annotations, spécifique à chaque format** (trois implémentations distinctes, pas une variation mineure d'une même fonction) :
  - PowerPoint : notes de présentateur ou encadré visuel sur le slide.
  - Word : commentaires insérés aux bons endroits du texte.
  - PDF : annotations façon post-it aux bonnes pages.
- **Limite honnête à connaître** : du contenu oral qui ne correspond à aucun support (digression, questions-réponses, exemple non présent sur les slides) n'ira dans aucune annotation — mais reste capturé dans la transcription et le résumé bruts (§4.3), qui existent indépendamment.
- **Séquencement de construction recommandé** : construire un seul format d'abord (le plus fréquent en pratique une fois Projet 3 commencé), ajouter les deux autres au fil des cours réels plutôt que de spéculer sur les trois en même temps — le principe de mise en correspondance par contenu reste identique pour les trois.

### 4.4 Site web public accessible à un collègue
- **Objectif** : héberger un site sur le M700, accessible depuis internet par un collègue via un navigateur classique, sans installer quoi que ce soit chez lui.
- **Mécanisme retenu : Cloudflare Tunnel** (programme sur le M700 qui ouvre une connexion *sortante* vers Cloudflare, qui redirige ensuite le trafic public vers le site — aucun port à ouvrir sur la box, l'IP publique domestique n'est jamais directement exposée). Gratuit, vérifié.
  - *Correction actée en cours de discussion* : Tailscale Funnel avait été envisagé initialement pour ce rôle, mais un changement de tarification (avril 2026) l'a fait passer dans le plan payant Premium (18$/mois) — écarté pour cette raison. Tailscale (plan Personal gratuit) reste néanmoins pertinent pour un futur accès administratif privé (§3) et pour l'usage iPad (§4.3), une question séparée de l'exposition publique d'un site.
- **Prérequis non encore réunis** : un nom de domaine (aucun acheté à ce jour, ~10-15€/an), un compte Cloudflare, et le site lui-même (nature pas encore définie).
- **Ce qui est prêt dès cette étape** : Caddy + Docker (§3), pour que le jour où le site existe, il ne reste plus qu'à créer un conteneur et une entrée de configuration.

### 4.5 Usages génériques futurs (hors projet assistant-ia)
Tout autre usage de développeur non encore anticipé — capacité générale disponible dès cette étape (Docker + Caddy + Tailscale en réserve), aucune spécification supplémentaire nécessaire pour l'instant.

---

## 5. Rôles explicitement écartés (et pourquoi)

| Candidat | Décision | Raison |
|---|---|---|
| **Ollama** | Reste sur le X260 | Le CPU du M700 (i5-6400T, basse consommation) n'accélère pas l'inférence — plus de RAM permet de charger un modèle plus gros, pas de répondre plus vite. Migrer ajoute une dépendance réseau à une fonctionnalité 100% locale aujourd'hui, sans gain de vitesse ni de qualité garanti. |
| **`gmail_watcher.py`** | Reste sur le X260 (via un service systemd à ajouter) | Le besoin réel ("relancer à la main à chaque session") se résout par l'automatisation locale, sans nécessiter une deuxième machine. Aurait de toute façon nécessité de remplacer `notify-send` (qui ne fonctionne pas sur une machine headless) par un nouveau composant (ntfy) pour un bénéfice non démontré. |
| **MCP Gmail (usage interactif quotidien)** | Reste avec le dashboard (X260) | Serveur invoqué à la demande (stdio, pas persistant) — "toujours allumé" n'apporte rien à un processus qui ne tourne que le temps d'un appel. |
| **`server.py` / dashboard Flask** | Reste sur le X260 | Le dashboard est un onglet épinglé censé être instantanément disponible (latence zéro, zéro dépendance réseau aujourd'hui). Le déplacer introduirait une fragilité nouvelle pour un problème qui n'existe pas actuellement. |
| **Tailscale Funnel** | Écarté au profit de Cloudflare Tunnel | Passé payant (plan Premium, 18$/mois) lors d'un changement de tarification en avril 2026 — ne correspond plus à l'exigence de gratuité. |

---

## 6. Nouveaux termes techniques abordés cette session
*(à reporter dans `explications_techniques_cumulees.md` puis `carnet_apprentissage.md`)*

| Terme | Définition |
|---|---|
| **Headless** | Machine pilotée à distance, sans écran/clavier qui lui sont propres en fonctionnement normal. |
| **SSH** | Protocole ouvrant un terminal sécurisé sur une machine distante depuis son propre terminal. |
| **SO-DIMM** | Format de barrette mémoire compact (utilisé dans les laptops et les mini-PC comme le M700 Tiny), par opposition au format DIMM plein format des tours. |
| **TPM** | Puce dédiée qui stocke des secrets cryptographiques liés physiquement à la carte mère — utilisée notamment pour le chiffrement de disque avec déverrouillage automatique. |
| **Réservation DHCP** | Règle configurée sur la box qui attribue toujours la même IP locale à une machine identifiée par son adresse MAC, au lieu d'une IP qui pourrait changer. |
| **mDNS / Avahi** | Service qui permet de joindre une machine par un nom (`machine.local`) plutôt qu'une IP, sans configuration côté box — mais dépend d'un service actif sur les deux machines. |
| **fail2ban** | Outil qui bloque temporairement une IP après plusieurs échecs de connexion (SSH notamment) — utile contre le bruteforce par mot de passe. |
| **Samba / SMB** | Protocole de partage de fichiers réseau, compatible nativement Linux et Windows. |
| **ufw** | Pare-feu simplifié sous Ubuntu, contrôle quelles connexions réseau entrantes sont autorisées. |
| **unattended-upgrades** | Mécanisme Ubuntu qui applique automatiquement certaines mises à jour (configurable pour se limiter aux patchs de sécurité). |
| **VPN mesh (Tailscale)** | Réseau privé virtuel chiffré reliant plusieurs machines entre elles sans exposer de port directement sur internet. |
| **Reverse proxy (Caddy)** | Programme qui reçoit toutes les requêtes web entrantes et les redirige vers le bon site/appli selon l'adresse demandée ; Caddy gère les certificats HTTPS automatiquement. |
| **Docker** | Outil de conteneurisation — fait tourner chaque site/appli dans son propre environnement isolé, avec ses propres dépendances, sans interférence avec les autres projets sur la même machine. |
| **Cloudflare Tunnel** | Programme qui ouvre une connexion sortante depuis le serveur vers Cloudflare, qui redirige ensuite le trafic public internet vers ce serveur — sans ouvrir de port entrant sur la box. |
| **Ubuntu Server vs Desktop** | Même OS de base ; Desktop ajoute un environnement graphique complet (consommateur de ressources), Server n'installe que l'essentiel, piloté en ligne de commande. |
| **ntfy** | Service de notifications push auto-hébergeable — un script envoie une requête simple, une appli sur le téléphone (abonnée à un canal précis) reçoit l'alerte, où que l'utilisateur se trouve. Gratuit, aucun compte tiers requis. |
| **API Google Drive** | Interface permettant à un script de lire/écrire des fichiers dans un compte Google Drive de façon automatisée — nécessite un projet Google Cloud + identifiants OAuth, même principe que les intégrations Gmail/Calendar déjà réalisées. |

---

## 7. Actions concrètes pour Claude Code (à exécuter après la fin du Projet 3)

1. Préparer une clé USB bootable Ubuntu Server (vérifier au moment venu s'il existe une version LTS plus récente que la 26.04).
2. Ouvrir le boîtier, vérifier que la barrette RAM DDR4 SO-DIMM déjà en possession (8 Go) est bien installée. Ne pas acheter/installer de deuxième barrette pour l'instant — à faire plus tard seulement si le besoin se confirme après test réel (voir §3).
3. Installer Ubuntu Server (écran + clavier temporaires nécessaires pour cette seule étape) — compte utilisateur `batiste`, disque non chiffré, fuseau horaire `Europe/Paris`.
4. Dans le BIOS, activer le redémarrage automatique après coupure de courant ("AC Power Recovery" / "Power On after Power Loss").
5. Sur la box internet : créer une réservation DHCP pour l'adresse MAC de la machine.
6. Configurer le nom d'hôte `assistant-server`.
7. Vérifier/générer une paire de clés SSH sur le X260, copier la clé publique sur le M700, désactiver l'authentification par mot de passe. Garder le port SSH standard (22).
8. Installer et configurer `ufw` (SSH autorisé depuis le réseau local uniquement). Ne pas installer fail2ban.
9. Installer et configurer `unattended-upgrades` en mode sécurité uniquement.
10. Installer Docker et Caddy (aucun site configuré dessus pour l'instant — juste la capacité prête).
11. Documenter l'ensemble dans `carnet_apprentissage.md` (nouvelle session) et ajouter les termes du §6.
12. Ne construire aucun rôle métier (§4) à ce stade — cette étape se termine une fois la machine joignable en SSH, sécurisée, dotée de Docker/Caddy, et documentée. Les rôles du §4 sont évalués séparément, une fois les besoins réels de Projet 2/3 connus.
