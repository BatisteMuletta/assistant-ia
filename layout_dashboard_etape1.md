# Layout dashboard — Étape 1 (squelette visuel)
> Validé dans le chat claude.ai le 05/07/2026, à transposer en HTML/CSS/JS

## Principe général
- Grille asymétrique (pas une grille uniforme), inspirée d'un croquis manuscrit
- Zones identifiées **par icônes uniquement** — aucun titre/texte visible
- Style minimaliste, light mode
- Icônes : Tabler icons (outline)

## Structure CSS Grid

```css
grid-template-columns: 1fr 1fr 1fr 0.5fr;
grid-template-rows: 90px 1fr 90px 1fr;
grid-template-areas:
  "notes taches gmail gmail"
  "suggestion suggestion gmail gmail"
  "suggestion suggestion calendrier calendrier"
  "chat chat couts misc";
gap: 10px;
```

## Détail des 9 zones

| Zone (grid-area) | Contenu prévu | Icône Tabler | Taille | Mise en avant |
|---|---|---|---|---|
| `notes` | Bloc notes rapide | `ti-notes` | petite (haut gauche) | non |
| `taches` | Tâches urgent/pas urgent | `ti-list-check` | petite (haut gauche) | non |
| `gmail` | Mails triés, dernier mail important (hors spams) | `ti-mail` | grande, colonne droite, pleine largeur restante | non |
| `suggestion` | Suggestions Claude (deadlines, notes→tâches, confirmations) | `ti-bulb` | grande, occupe 2 colonnes de gauche | **oui** — fond accent |
| `calendrier` | Vue semaine Google Calendar | `ti-calendar` | moyenne, sous gmail, pleine largeur restante | non |
| `chat` | Chat Claude (10 derniers échanges) | `ti-message-circle` | grande, bas gauche, 2 colonnes | **oui** — fond accent |
| `couts` | Suivi des coûts API (Anthropic + Whisper) | `ti-currency-euro` | petite, bas droite | non |
| `misc` (journal) | Journal d'activité | `ti-history` | mini-icône empilée, colonne étroite à droite de `couts` | non |
| `misc` (stats) | Stats (compteur actions) | `ti-chart-bar` | mini-icône empilée, sous journal | non |

Note : `journal` et `stats` ne sont **pas** affichés comme des blocs pleins pour l'instant — seulement deux petites icônes cliquables empilées dans la colonne `misc`, à droite du bloc `couts`. Le clic donnera accès au détail plus tard (agents/JS à ajouter aux étapes suivantes).

## Zones "mises en avant" (fond accent)
`suggestion` et `chat` ont un traitement visuel légèrement différent (fond teinté) des 7 autres zones, car ce sont les deux seules zones d'interaction directe avec Claude. Toutes les autres zones sont des blocs neutres identiques.

## Ce qui n'est PAS encore décidé (à voir aux étapes suivantes)
- Contenu réel de chaque zone (branchement Gmail/Calendar via MCP, etc.) → étapes 3+
- Comportement au clic/hover de chaque icône (tooltip ? ouverture panneau ?)
- Couleurs exactes au-delà de "accent vs neutre"
- Responsive / adaptation mobile (non demandé pour l'instant)

## Rappel contraintes globales du projet (cahier des charges v4)
- Pas d'horloge/date sur le dashboard
- Code HTML/CSS/JS commenté en français
- Layout fixé une fois pour toutes à cette étape — pas de réorganisation prévue ensuite
- Bilingue fr/en sur la même page (à voir comment ça s'applique avec des icônes seules — probablement via `title`/tooltip ou détection langue pour le contenu texte à l'intérieur des blocs, pas pour les icônes elles-mêmes)
