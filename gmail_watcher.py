# gmail_watcher.py — Surveillance en arrière-plan des mails urgents, notifications Ubuntu
#
# Tourne en boucle indépendamment du dashboard (cahier des charges : notifications
# "hors dashboard"). Lancement manuel pour l'instant : `python3 gmail_watcher.py`.
# L'automatisation au démarrage (cron/systemd) est un choix à part, pas encore fait.

import json
import subprocess
import time
from pathlib import Path

from gmail_mcp import ServeurGmailIndisponibleError, lister_emails_recents
from ia_provider import trier_emails_urgents

BASE_DIR = Path(__file__).parent
FICHIER_NOTIFIES = BASE_DIR / "mails_notifies.json"
INTERVALLE_SECONDES = 300  # 5 minutes
NOMBRE_CANDIDATS = 25
MAX_IDS_CONSERVES = 200  # évite que le fichier de suivi grossisse indéfiniment


def _charger_notifies() -> set:
    if not FICHIER_NOTIFIES.exists():
        return set()
    return set(json.loads(FICHIER_NOTIFIES.read_text()))


def _sauvegarder_notifies(ids: set) -> None:
    recents = list(ids)[-MAX_IDS_CONSERVES:]
    FICHIER_NOTIFIES.write_text(json.dumps(recents))


def _notifier(email: dict) -> None:
    subprocess.run(
        [
            "notify-send",
            "--icon=mail-unread",
            f"Mail urgent : {email['sujet'] or '(sans sujet)'}",
            f"De : {email['expediteur']}",
        ],
        check=False,
    )


def verifier_une_fois() -> None:
    """Un seul passage : vérifie les mails urgents, notifie ceux qui ne l'ont pas déjà été."""
    deja_notifies = _charger_notifies()
    try:
        candidats = lister_emails_recents(nombre=NOMBRE_CANDIDATS)
    except ServeurGmailIndisponibleError as erreur:
        print(f"[gmail_watcher] {erreur}")
        return

    tries = trier_emails_urgents(candidats)
    nouveaux = 0
    for email in tries:
        if email["urgent"] and email["id"] not in deja_notifies:
            _notifier(email)
            deja_notifies.add(email["id"])
            nouveaux += 1
    _sauvegarder_notifies(deja_notifies)
    print(f"[gmail_watcher] vérification faite, {nouveaux} nouvelle(s) notification(s)")


def boucle() -> None:
    while True:
        verifier_une_fois()
        time.sleep(INTERVALLE_SECONDES)


if __name__ == "__main__":
    boucle()
