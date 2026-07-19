# briefing.py — Chaînage : mails urgents + calendrier du jour + détection de deadlines,
# combinés en un briefing adapté au niveau d'urgence.
#
# C'est ici qu'apparaît la notion d'"agent" au sens de ce projet (voir carnet
# d'apprentissage, Arbre de décision) : un harnais (outils Gmail/Calendar/IA
# disponibles, règle absolue "jamais d'ajout au calendrier sans confirmation
# explicite") et une loop courte et linéaire — rassembler → analyser → générer →
# proposer → attendre confirmation —, pas une boucle autonome multi-tours.

from datetime import datetime, timedelta

from calendar_mcp import ServeurCalendarIndisponibleError, ajouter_evenement, lister_evenements_jour
from gmail_mcp import ServeurGmailIndisponibleError, lire_email, lister_emails_recents
from ia_provider import detecter_deadlines, generer_briefing, trier_emails_urgents

NOMBRE_CANDIDATS_GMAIL = 25


def construire_briefing() -> dict:
    """Rassemble mails urgents + événements du jour, détecte d'éventuelles deadlines
    cachées dans les mails, puis génère le texte du briefing. Ne modifie jamais le
    calendrier : les deadlines détectées ne sont que des suggestions affichées côté UI,
    chacune avec son propre bouton de confirmation (voir /api/briefing/deadline)."""
    try:
        candidats = lister_emails_recents(nombre=NOMBRE_CANDIDATS_GMAIL)
        mails_urgents = [e for e in trier_emails_urgents(candidats) if e["urgent"]]
    except ServeurGmailIndisponibleError:
        mails_urgents = []

    try:
        evenements_jour = lister_evenements_jour()
    except ServeurCalendarIndisponibleError:
        evenements_jour = []

    # Le tri urgent ne donne que sujet/expéditeur/date : il faut le corps complet de
    # chaque mail pour espérer y détecter une deadline (souvent dans le texte, pas le sujet).
    mails_avec_corps = []
    for mail in mails_urgents:
        try:
            mails_avec_corps.append(lire_email(mail["id"]))
        except ServeurGmailIndisponibleError:
            continue
        mails_avec_corps[-1]["id"] = mail["id"]

    deadlines = detecter_deadlines(mails_avec_corps)
    texte = generer_briefing(mails_urgents, evenements_jour, deadlines)

    return {
        "texte": texte,
        "mails_urgents": mails_urgents,
        "evenements_jour": evenements_jour,
        "deadlines": deadlines,
    }


def confirmer_deadline(titre: str, date: str, heure: str | None) -> None:
    """Ajoute une deadline confirmée par l'utilisateur au calendrier principal.
    Événement d'une heure si une heure est précisée, sinon événement journée entière."""
    if heure:
        debut = f"{date}T{heure}:00"
        fin = f"{date}T{_heure_plus_une_heure(heure)}:00"
    else:
        debut = date
        fin = _jour_suivant(date)
    ajouter_evenement(titre, debut, fin, description="Ajouté depuis le briefing du matin.")


def _heure_plus_une_heure(heure: str) -> str:
    h, m = (int(x) for x in heure.split(":"))
    return f"{(h + 1) % 24:02d}:{m:02d}"


def _jour_suivant(date: str) -> str:
    return (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
