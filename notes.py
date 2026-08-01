# notes.py — Stockage local des notes (notes.json)
#
# Une seule zone de texte libre côté dashboard (une ligne = une note), mais stockée en
# structuré (comme taches.py) pour pouvoir suivre par note : a-t-elle déjà une tâche
# confirmée ? a-t-elle été ignorée ? quelle traduction lui a déjà été trouvée ?
# Le rapprochement entre l'ancien et le nouveau texte se fait par contenu exact de la
# ligne (pas de bouton "supprimer" dédié dans l'UI) : une ligne qui disparaît du texte
# saisi est considérée supprimée ; une ligne modifiée, même légèrement, est traitée
# comme une note neuve (état remis à zéro, y compris "ignorée").

import json
import uuid
from pathlib import Path

NOTES_PATH = Path(__file__).parent / "notes.json"


def _charger() -> list[dict]:
    if not NOTES_PATH.exists():
        return []
    return json.loads(NOTES_PATH.read_text())


def _sauvegarder(notes: list[dict]) -> None:
    NOTES_PATH.write_text(json.dumps(notes, indent=2, ensure_ascii=False))


def texte_notes() -> str:
    """Reconstruit le texte brut affiché dans la zone de saisie, une note par ligne."""
    return "\n".join(n["texte"] for n in _charger())


def sauvegarder_texte(texte_brut: str) -> list[dict]:
    """Remplace l'ensemble des notes à partir du texte brut de la zone de saisie.
    Les lignes vides sont ignorées (pas des notes). Une ligne dont le texte exact
    existait déjà garde son état (tache_id/ignoree/traduction) ; une ligne absente
    du nouveau texte est supprimée ; une ligne neuve démarre avec un état vierge."""
    anciennes = {n["texte"]: n for n in _charger()}
    notes = []
    for ligne in texte_brut.split("\n"):
        ligne = ligne.strip()
        if not ligne:
            continue
        if ligne in anciennes:
            notes.append(anciennes[ligne])
        else:
            notes.append({
                "id": uuid.uuid4().hex[:8],
                "texte": ligne,
                "tache_id": None,
                "ignoree": False,
                "langue": None,
                "traduction": None,
            })
    _sauvegarder(notes)
    return notes


def lister_a_analyser() -> list[dict]:
    """Notes candidates pour le bouton "Analyser" : pas encore liées à une tâche
    confirmée, et dont la suggestion (s'il y en avait une) n'a pas été ignorée."""
    return [n for n in _charger() if not n["tache_id"] and not n["ignoree"]]


def mettre_a_jour_analyse(note_id: str, langue: str | None, traduction: str | None) -> dict | None:
    notes = _charger()
    for n in notes:
        if n["id"] == note_id:
            n["langue"] = langue
            n["traduction"] = traduction
            _sauvegarder(notes)
            return n
    return None


def marquer_ignoree(note_id: str) -> bool:
    notes = _charger()
    for n in notes:
        if n["id"] == note_id:
            n["ignoree"] = True
            _sauvegarder(notes)
            return True
    return False


def marquer_tache(note_id: str, tache_id: str) -> bool:
    notes = _charger()
    for n in notes:
        if n["id"] == note_id:
            n["tache_id"] = tache_id
            _sauvegarder(notes)
            return True
    return False
