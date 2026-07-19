# taches.py — Stockage local des tâches (tasks.json), séparé du reste comme costs.py
#
# Une tâche cochée reste visible (barrée) jusqu'à la fin de la journée où elle a été
# faite, puis disparaît le lendemain — "tâches non faites conservées d'un jour à
# l'autre" du cahier des charges implique, en creux, que les faites ne le sont pas.

import json
import uuid
from datetime import datetime
from pathlib import Path

TACHES_PATH = Path(__file__).parent / "tasks.json"


def _aujourdhui() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _charger() -> list[dict]:
    if not TACHES_PATH.exists():
        return []
    return json.loads(TACHES_PATH.read_text())


def _sauvegarder(taches: list[dict]) -> None:
    TACHES_PATH.write_text(json.dumps(taches, indent=2, ensure_ascii=False))


def ajouter_tache(texte: str, urgent: bool = False) -> dict:
    taches = _charger()
    tache = {
        "id": uuid.uuid4().hex[:8],
        "texte": texte,
        "urgent": urgent,
        "fait": False,
        "date_creation": _aujourdhui(),
        "date_completion": None,
    }
    taches.append(tache)
    _sauvegarder(taches)
    return tache


def lister_taches() -> list[dict]:
    """Tâches non faites + tâches faites aujourd'hui seulement (les faites les jours
    précédents ne sont plus renvoyées, sans avoir besoin d'être supprimées explicitement)."""
    aujourdhui = _aujourdhui()
    return [
        t for t in _charger()
        if not t["fait"] or t["date_completion"] == aujourdhui
    ]


def lister_taches_non_faites() -> list[dict]:
    """Utilisé par le briefing du matin : uniquement ce qui reste réellement à faire."""
    return [t for t in _charger() if not t["fait"]]


def toggle_tache(tache_id: str) -> dict | None:
    taches = _charger()
    for t in taches:
        if t["id"] == tache_id:
            t["fait"] = not t["fait"]
            t["date_completion"] = _aujourdhui() if t["fait"] else None
            _sauvegarder(taches)
            return t
    return None
