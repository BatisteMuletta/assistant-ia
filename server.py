# server.py — Serveur local : sert le dashboard et fait le pont vers Ollama/Anthropic
#
# Sécurité : les routes de fichiers statiques sont explicites (pas de wildcard sur
# tout le dossier), pour ne jamais risquer de servir .env, server.py ou costs.json
# par accident via une URL.

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from calendar_mcp import ServeurCalendarIndisponibleError, lister_evenements_semaine
from costs import etat_couts
from ia_provider import (
    CleManquanteError,
    CoutBloqueError,
    ecrire_provider,
    generer_reponse,
    lire_provider,
)

BASE_DIR = Path(__file__).parent

app = Flask(__name__)


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


if __name__ == "__main__":
    # debug=True (rechargement auto + traces détaillées) uniquement en dev explicite via
    # FLASK_DEBUG=1 — jamais par défaut, la console de debug Werkzeug permet l'exécution
    # de code arbitraire si jamais le serveur était accessible au-delà de localhost.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(port=5000, debug=debug)
