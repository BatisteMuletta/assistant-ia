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
    envoyer_email,
    extraire_adresse,
    lire_email,
    lister_emails_recents,
)
from ia_provider import (
    CleManquanteError,
    CoutBloqueError,
    ecrire_provider,
    generer_reponse,
    lire_provider,
    rediger_reponse_email,
    trier_emails_urgents,
)

BASE_DIR = Path(__file__).parent

app = Flask(__name__)

# Protection CSRF : les routes qui mutent des données ou coûtent de l'argent (API payante)
# n'acceptent que les requêtes venant de notre propre dashboard. Sans ça, n'importe quel
# appel HTTP direct (page web tierce, script, curl...) déclenche l'action sans validation
# humaine réelle — le bouton "Envoyer" côté UI n'est qu'une convention, pas un verrou serveur.
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


@app.route("/api/gmail/<message_id>/send", methods=["POST"])
def gmail_send(message_id):
    """Envoi réel : appelé uniquement depuis le clic explicite du bouton "Envoyer"
    du dashboard, jamais automatiquement. Le corps envoyé est celui validé/édité
    par l'utilisateur, pas nécessairement le brouillon généré par l'IA."""
    if not _origine_locale():
        return _origine_refusee()
    corps = ((request.json or {}).get("corps") or "").strip()
    if not corps:
        return jsonify({"erreur": "Le corps de la réponse est vide."}), 400
    try:
        email = lire_email(message_id)
        destinataire = extraire_adresse(email["expediteur"])
        sujet = email["sujet"] if email["sujet"].lower().startswith("re:") else f"Re: {email['sujet']}"
        envoyer_email(destinataire, sujet, corps, thread_id=email.get("thread_id", ""))
    except ServeurGmailIndisponibleError as erreur:
        return jsonify({"erreur": str(erreur)}), 503
    return jsonify({"envoye": True})


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


if __name__ == "__main__":
    # debug=True (rechargement auto + traces détaillées) uniquement en dev explicite via
    # FLASK_DEBUG=1 — jamais par défaut, la console de debug Werkzeug permet l'exécution
    # de code arbitraire si jamais le serveur était accessible au-delà de localhost.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(port=5000, debug=debug)
