# notes.py — Stockage local du bloc notes (notes.md), un seul fichier qui grandit
#
# Contrairement à tasks.json/costs.json (données structurées), notes.md est pensé
# pour rester lisible directement par l'utilisateur dans VS Code — texte Markdown
# simple, pas un format à parser par le code.

from datetime import datetime
from pathlib import Path

NOTES_PATH = Path(__file__).parent / "notes.md"


def ajouter_note(texte_nettoye: str) -> None:
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M")
    entree = f"## {horodatage}\n{texte_nettoye}\n\n"
    with NOTES_PATH.open("a", encoding="utf-8") as fichier:
        fichier.write(entree)
