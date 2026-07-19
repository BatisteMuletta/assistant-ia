# server.py — Serveur local : sert le dashboard et fait le pont vers Ollama/Anthropic
#
# Sécurité : les routes de fichiers statiques sont explicites (pas de wildcard sur
# tout le dossier), pour ne jamais risquer de servir .env, server.py ou costs.json
# par accident via une URL.

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from briefing import confirmer_deadline, construire_briefing
from calendar_mcp import ServeurCalendarIndisponibleError, lister_evenements_semaine
from costs import etat_couts
from gmail_mcp import (
    ServeurGmailIndisponibleError,
    lire_email,
    lister_emails_recents,
)
from ia_provider import (
    CleManquanteError,
    CoutBloqueError,
    analyser_note,
    ecrire_provider,
    generer_reponse,
    lire_provider,
    rediger_reponse_email,
    trier_emails_urgents,
)
from notes import ajouter_note
from taches import ajouter_tache, lister_taches, toggle_tache

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

# Protection CSRF : les routes qui mutent des données ou coûtent de l'argent (API payante)
# n'acceptent que les requêtes venant de notre propre dashboard. Sans ça, n'importe quel
# appel HTTP direct (page web tierce, script, curl...) déclenche l'action sans validation
# humaine réelle — un bouton "Confirmer" côté UI n'est qu'une convention, pas un verrou serveur.
# Note : l'envoi de mail n'a de toute façon plus de route ici (voir gmail_mcp.py) — le
# jeton OAuth Gmail est en scope lecture seule, send_email n'existe même plus côté serveur MCP.
ORIGINES_AUTORISEES = {"http://127.0.0.1:5000", "http://localhost:5000"}


def _origine_locale() -> bool:
    origine = request.headers.get("Origin")
    if origine is not None:
        return origine in ORIGINES_AUTORISEES
    # Repli sur Referer : certains navigateurs/requêtes n'envoient pas Origin sur un POST
    # same-origin selon le contexte ; Referer inclut la même information dans ce cas.
    referer = request.headers.get("Referer", "")
    return any(referer.startswith(o) for o in ORIGINES_AUTORISEES)


def _origine_refusee():
    return jsonify({"erreur": "Origine non autorisée."}), 403


@app.route("/")
def accueil():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def script():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/assets/<path:chemin>")
def assets(chemin):
    return send_from_directory(BASE_DIR / "assets", chemin)


@app.route("/api/chat", methods=["POST"])
def chat():
    if not _origine_locale():
        return _origine_refusee()
    historique = (request.json or {}).get("historique", [])
    try:
        reponse = generer_reponse(historique)
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400
    return jsonify({"reponse": reponse, "provider": lire_provider()})


@app.route("/api/provider", methods=["GET"])
def provider_actuel():
    return jsonify({"provider": lire_provider()})


@app.route("/api/provider/toggle", methods=["POST"])
def basculer_provider():
    if not _origine_locale():
        return _origine_refusee()
    nouveau = "anthropic" if lire_provider() == "ollama" else "ollama"
    ecrire_provider(nouveau)
    return jsonify({"provider": nouveau})


@app.route("/api/costs", methods=["GET"])
def couts():
    return jsonify(etat_couts())


@app.route("/api/calendar", methods=["GET"])
def calendrier():
    try:
        evenements_json = lister_evenements_semaine()
    except ServeurCalendarIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503
    return app.response_class(evenements_json, mimetype="application/json")


NOMBRE_CANDIDATS_GMAIL = 25  # pool examiné par le tri, plus large que ce qui est affiché
NOMBRE_AFFICHES_GMAIL = 10  # nombre de mails non urgents affichés (les urgents sont tous gardés)


@app.route("/api/gmail", methods=["GET"])
def gmail():
    try:
        candidats = lister_emails_recents(nombre=NOMBRE_CANDIDATS_GMAIL)
    except ServeurGmailIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503

    tries = trier_emails_urgents(candidats)
    urgents = [e for e in tries if e["urgent"]]
    non_urgents = [e for e in tries if not e["urgent"]]
    # Un mail urgent ne doit jamais disparaître faute de place : on garde tous les
    # urgents et on complète avec les non-urgents les plus récents jusqu'à la limite.
    place_restante = max(0, NOMBRE_AFFICHES_GMAIL - len(urgents))
    return jsonify(urgents + non_urgents[:place_restante])


@app.route("/api/gmail/<message_id>", methods=["GET"])
def gmail_detail(message_id):
    try:
        email = lire_email(message_id)
    except ServeurGmailIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503
    return jsonify(email)


@app.route("/api/gmail/<message_id>/draft", methods=["POST"])
def gmail_draft(message_id):
    """Propose un brouillon de réponse (Claude/Ollama selon le provider actif).
    N'envoie rien : le brouillon est éditable côté dashboard avant tout envoi."""
    if not _origine_locale():
        return _origine_refusee()
    try:
        email = lire_email(message_id)
    except ServeurGmailIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503
    try:
        brouillon = rediger_reponse_email(email)
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400
    return jsonify({"brouillon": brouillon})


@app.route("/api/briefing", methods=["POST"])
def briefing():
    """Génère le briefing du matin à la demande (mails urgents + événements du jour +
    deadlines détectées). Ne modifie jamais le calendrier — voir /api/briefing/deadline
    pour la confirmation, séparée et explicite, de chaque deadline suggérée."""
    if not _origine_locale():
        return _origine_refusee()
    try:
        return jsonify(construire_briefing())
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400


@app.route("/api/briefing/deadline", methods=["POST"])
def briefing_deadline():
    """Ajoute une deadline suggérée par le briefing au calendrier — uniquement sur clic
    explicite du bouton "Ajouter au calendrier" côté dashboard, jamais automatiquement."""
    if not _origine_locale():
        return _origine_refusee()
    donnees = request.json or {}
    titre = (donnees.get("titre") or "").strip()
    date = (donnees.get("date") or "").strip()
    heure = donnees.get("heure") or None
    if not titre or not date:
        return jsonify({"erreur": "Titre ou date manquant."}), 400
    try:
        confirmer_deadline(titre, date, heure)
    except ServeurCalendarIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503
    return jsonify({"ajoute": True})


@app.route("/api/notes", methods=["POST"])
def notes():
    """Analyse une note (tâche potentielle ? langue ? version nettoyée), puis l'archive
    automatiquement dans notes.md. La tâche suggérée, elle, n'est PAS créée ici : elle
    est seulement renvoyée pour affichage, la création réelle attend la confirmation
    explicite côté dashboard (voir /api/taches/confirmer)."""
    if not _origine_locale():
        return _origine_refusee()
    texte = ((request.json or {}).get("texte") or "").strip()
    if not texte:
        return jsonify({"erreur": "Note vide."}), 400
    try:
        analyse = analyser_note(texte)
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400
    ajouter_note(analyse["note_nettoyee"])
    return jsonify(analyse)


@app.route("/api/taches", methods=["GET"])
def taches():
    return jsonify(lister_taches())


@app.route("/api/taches/confirmer", methods=["POST"])
def taches_confirmer():
    """Crée réellement une tâche suggérée — appelée uniquement sur clic explicite du
    bouton "Confirmer" à côté de la suggestion, jamais automatiquement depuis /api/notes."""
    if not _origine_locale():
        return _origine_refusee()
    donnees = request.json or {}
    texte = (donnees.get("texte") or "").strip()
    urgent = bool(donnees.get("urgent"))
    if not texte:
        return jsonify({"erreur": "Texte de tâche manquant."}), 400
    return jsonify(ajouter_tache(texte, urgent=urgent))


@app.route("/api/taches/<tache_id>/toggle", methods=["POST"])
def taches_toggle(tache_id):
    if not _origine_locale():
        return _origine_refusee()
    tache = toggle_tache(tache_id)
    if tache is None:
        return jsonify({"erreur": "Tâche introuvable."}), 404
    return jsonify(tache)


if __name__ == "__main__":
    # debug=True (rechargement auto + traces détaillées) uniquement en dev explicite via
    # FLASK_DEBUG=1 — jamais par défaut, la console de debug Werkzeug permet l'exécution
    # de code arbitraire si jamais le serveur était accessible au-delà de localhost.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(port=5000, debug=debug)
