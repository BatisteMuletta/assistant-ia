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
from fichiers_manager import (
    ActionRefuseeError,
    FichierIntrouvableError,
    deplacer_fichier,
    lire_extrait,
    lister_sous_dossiers_existants,
    renommer,
    resoudre_chemin,
    scanner_nouveaux_fichiers,
)
from gmail_mcp import (
    ServeurGmailIndisponibleError,
    lire_email,
    lister_emails_recents,
)
from ia_provider import (
    CleManquanteError,
    CoutBloqueError,
    analyser_notes,
    ecrire_provider,
    generer_reponse,
    lire_provider,
    proposer_organisation_fichier,
    rediger_reponse_email,
    trier_emails_urgents,
)
from notes import (
    lister_a_analyser,
    marquer_ignoree,
    marquer_tache,
    mettre_a_jour_analyse,
    sauvegarder_texte,
    texte_notes,
)
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


@app.route("/api/fichiers/scan", methods=["POST"])
def fichiers_scan():
    """Scanne ~/Downloads et renvoie les fichiers jamais vus lors d'un scan précédent.
    Noms + taille uniquement (voir fichiers_manager.scanner_nouveaux_fichiers) — ne lit
    aucun contenu, ne renomme rien, ne déplace rien."""
    if not _origine_locale():
        return _origine_refusee()
    return jsonify({"nouveaux": scanner_nouveaux_fichiers()})


@app.route("/api/fichiers/<nom>/lire", methods=["POST"])
def fichiers_lire(nom):
    """Ce clic EST l'autorisation explicite de lire le contenu de ce fichier précis (voir
    SKILL.md — jamais automatique, jamais globale). Lit un extrait, puis appelle le modèle
    avec tool-calling (forcé Anthropic). renommer_fichier s'exécute ici même, automatique-
    ment ; un déplacement éventuel reste en attente de /api/fichiers/<nom>/confirmer."""
    if not _origine_locale():
        return _origine_refusee()
    try:
        chemin = resoudre_chemin(nom)
    except (FichierIntrouvableError, ActionRefuseeError) as erreur:
        return jsonify({"erreur": str(erreur)}), 404

    extrait = lire_extrait(nom)
    try:
        appels = proposer_organisation_fichier(
            nom, chemin.stat().st_size, extrait, lister_sous_dossiers_existants()
        )
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400

    nom_final = nom
    categorie_proposee = None
    sous_dossier_propose = None
    for appel in appels:
        if appel["name"] == "renommer_fichier":
            try:
                nom_final = renommer(nom_final, appel["input"]["nouveau_nom"])
            except ActionRefuseeError as erreur:
                return jsonify({"erreur": str(erreur)}), 400
        elif appel["name"] == "proposer_deplacement":
            categorie_proposee = appel["input"].get("categorie")
            sous_dossier_propose = appel["input"].get("sous_dossier")

    return jsonify({
        "nom": nom_final,
        "categorie_proposee": categorie_proposee,
        "sous_dossier_propose": sous_dossier_propose,
    })


@app.route("/api/fichiers/<nom>/confirmer", methods=["POST"])
def fichiers_confirmer(nom):
    """Exécute le déplacement vers <categorie>[/<sous_dossier>] — uniquement sur ce clic
    explicite, jamais automatique (à la différence du renommage, voir
    /api/fichiers/<nom>/lire). Ce clic couvre aussi la création du sous-dossier s'il
    n'existe pas encore."""
    if not _origine_locale():
        return _origine_refusee()
    donnees = request.json or {}
    categorie = donnees.get("categorie") or ""
    sous_dossier = donnees.get("sous_dossier") or None
    try:
        deplacer_fichier(nom, categorie, sous_dossier)
    except (FichierIntrouvableError, ActionRefuseeError) as erreur:
        return jsonify({"erreur": str(erreur)}), 400
    return jsonify({"deplace": True})


@app.route("/api/notes", methods=["GET"])
def notes_get():
    """Renvoie le texte brut de toutes les notes (une par ligne), pour remplir la zone
    de saisie unique du dashboard à l'ouverture."""
    return jsonify({"texte": texte_notes()})


@app.route("/api/notes", methods=["PUT"])
def notes_put():
    """Sauvegarde le texte complet de la zone de notes (auto-save côté dashboard, pas
    d'action explicite de l'utilisateur ici). Aucun appel IA : juste la persistance."""
    if not _origine_locale():
        return _origine_refusee()
    texte = (request.json or {}).get("texte", "")
    sauvegarder_texte(texte)
    return jsonify({"sauvegarde": True})


@app.route("/api/notes/analyser", methods=["POST"])
def notes_analyser():
    """Déclenché uniquement par le clic explicite sur le bouton "Analyser". N'analyse
    que les notes pas encore liées à une tâche confirmée et pas ignorées (voir
    notes.lister_a_analyser) : les autres ne sont pas renvoyées à l'IA, pour ne pas
    payer à nouveau pour du texte déjà traité."""
    if not _origine_locale():
        return _origine_refusee()
    candidates = lister_a_analyser()
    if not candidates:
        return jsonify({"suggestions": []})
    try:
        resultats = analyser_notes(candidates)
    except CoutBloqueError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": True}), 402
    except CleManquanteError as erreur:
        return jsonify({"erreur": str(erreur), "anomalie": False}), 400

    suggestions = []
    for resultat in resultats:
        note = mettre_a_jour_analyse(
            resultat.get("id"),
            langue=resultat.get("langue"),
            traduction=resultat.get("traduction"),
        )
        if note and resultat.get("tache_suggeree"):
            suggestions.append({
                "note_id": note["id"],
                "texte": note["texte"],
                "tache_suggeree": resultat["tache_suggeree"],
                "urgent": bool(resultat.get("urgent")),
            })
    return jsonify({"suggestions": suggestions})


@app.route("/api/notes/<note_id>/ignorer", methods=["POST"])
def notes_ignorer(note_id):
    """Une note ignorée ne sera plus proposée par /api/notes/analyser tant que son
    texte ne change pas (voir notes.sauvegarder_texte : une ligne modifiée redémarre
    avec un état vierge)."""
    if not _origine_locale():
        return _origine_refusee()
    if not marquer_ignoree(note_id):
        return jsonify({"erreur": "Note introuvable."}), 404
    return jsonify({"ignoree": True})


@app.route("/api/taches", methods=["GET"])
def taches():
    return jsonify(lister_taches())


@app.route("/api/taches/confirmer", methods=["POST"])
def taches_confirmer():
    """Crée réellement une tâche suggérée — appelée uniquement sur clic explicite du
    bouton "Confirmer" à côté de la suggestion, jamais automatiquement depuis /api/notes.
    Si note_id est fourni, la note d'origine est marquée comme liée à cette tâche pour
    ne plus être proposée à l'analyse."""
    if not _origine_locale():
        return _origine_refusee()
    donnees = request.json or {}
    texte = (donnees.get("texte") or "").strip()
    urgent = bool(donnees.get("urgent"))
    note_id = donnees.get("note_id")
    if not texte:
        return jsonify({"erreur": "Texte de tâche manquant."}), 400
    tache = ajouter_tache(texte, urgent=urgent)
    if note_id:
        marquer_tache(note_id, tache["id"])
    return jsonify(tache)


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
