# activity_log.py — Journal d'activité centralisé (append-only)
#
# Toutes les actions du projet qui modifient quelque chose de réel (fichiers, données)
# doivent être journalisées ici sans exception (règle du cahier des charges). Premier
# utilisateur : fichiers_manager.py (Projet 2) — le seul filet de contrôle a posteriori
# pour renommer_fichier, qui s'exécute automatiquement sans confirmation.

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "activity_log.json"


def journaliser(message: str) -> None:
    entrees = json.loads(LOG_PATH.read_text()) if LOG_PATH.exists() else []
    entrees.append({"horodatage": datetime.now().isoformat(timespec="seconds"), "message": message})
    LOG_PATH.write_text(json.dumps(entrees, indent=2, ensure_ascii=False))
