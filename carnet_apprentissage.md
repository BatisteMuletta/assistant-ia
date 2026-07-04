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
| Token | *À définir en session 0* |
| Context window | *À définir en session 0* |
| LLM | *À définir en session 0* |
| Prompt | *À définir en session 0* |
| API REST | *À définir en session 0* |
| Agent IA | *À définir en session 0* |
| Skill | *À définir en session 0* |
| MCP | *À définir en session 0* |
| Claude Code | *À définir en session 0* |
| Whisper | *À définir en session 0* |
| OAuth | *À définir en session 0* |
| **Harnais (agent)** | La structure qui encadre un agent IA — ses instructions, ses outils disponibles, ses règles de sécurité. Comme un harnais d'escalade : il ne t'empêche pas d'agir mais définit le cadre sécurisé dans lequel l'agent opère. |
| **Loop (agent)** | La boucle d'exécution d'un agent : observer → réfléchir → agir → observer le résultat → réfléchir à nouveau → etc. Exactement comme une boucle de contrôle en embarqué. Le harnais définit le cadre, la loop est ce qui tourne dedans. |

---

## Sessions

---

### Session 0 — *À venir*
**Date :** —
**Durée :** —
**Étape du projet :** Étape 0 — Fichier de contexte + repo Git

#### Ce qu'on a construit
*À remplir*

#### Ce qu'on a appris
*À remplir*

#### Fonctionnalités Claude explorées
*À remplir*

#### Points importants à retenir
*À remplir*

#### Questions ouvertes pour la prochaine session
*À remplir*

---

*Les sessions suivantes s'ajouteront ici au fur et à mesure*
