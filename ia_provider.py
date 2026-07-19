# ia_provider.py — Point de config unique pour toutes les fonctionnalités IA du dashboard
#
# Tout le code (chat, futur tri mails, futures analyses) doit appeler generer_reponse()
# et ne jamais parler directement à Ollama ou à l'API Anthropic. Basculer de modèle
# devient ainsi un changement de config (config.json), pas une réécriture du code
# — même logique qu'une couche d'abstraction matérielle (HAL) en embarqué.

import json
import os
from datetime import datetime
from pathlib import Path

import requests
from anthropic import Anthropic
from dotenv import load_dotenv

from costs import SEUIL_ANOMALIE, calculer_cout, get_total_spent, log_cost

load_dotenv()

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"

MODELE_OLLAMA = "llama3.2:1b"  # version allégée (1.3 Go vs 2.0 Go) — RAM machine limitée
MODELE_ANTHROPIC = "claude-haiku-4-5-20251001"  # modèle le moins cher, cohérent avec le budget serré

# Nombre de messages d'historique conservés pour le contexte envoyé au modèle.
# Limite le coût par message sur l'API Anthropic (payante) — au-delà, les échanges
# trop anciens sont oubliés plutôt que renvoyés à chaque appel.
MAX_HISTORIQUE = 5


class CoutBloqueError(Exception):
    """Levée quand le seuil de secours (anomalie) est atteint côté serveur."""


class CleManquanteError(Exception):
    """Levée quand ANTHROPIC_API_KEY n'est pas définie dans .env."""


def lire_provider():
    if not CONFIG_PATH.exists():
        return "ollama"
    return json.loads(CONFIG_PATH.read_text()).get("provider", "ollama")


def ecrire_provider(provider):
    CONFIG_PATH.write_text(json.dumps({"provider": provider}, indent=2))


def generer_reponse(historique):
    """historique : liste de {"role": "user"|"assistant", "content": str},
    dans l'ordre chronologique — nécessaire pour que le modèle garde le contexte
    de la conversation d'un message à l'autre (voir CLAUDE.md / bug "d'autres")."""
    historique = historique[-MAX_HISTORIQUE:]
    provider = lire_provider()
    if provider == "anthropic":
        return _appel_anthropic(historique)
    return _appel_ollama(historique)


def _appel_ollama(historique):
    reponse = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": MODELE_OLLAMA, "messages": historique, "stream": False},
        timeout=60,
    )
    reponse.raise_for_status()
    return reponse.json()["message"]["content"]


def _appel_anthropic(historique):
    if get_total_spent() >= SEUIL_ANOMALIE:
        raise CoutBloqueError(
            f"Seuil de secours de {SEUIL_ANOMALIE}$ atteint ce mois-ci — appel bloqué. "
            "Ceci ne devrait jamais arriver si le plafond Console Anthropic fonctionne : "
            "vérifier la configuration sur console.anthropic.com."
        )

    cle = os.environ.get("ANTHROPIC_API_KEY")
    if not cle:
        raise CleManquanteError(
            "ANTHROPIC_API_KEY absente de .env — copier .env.example en .env "
            "et y coller une vraie clé (console.anthropic.com) avant de basculer sur Anthropic."
        )
    client = Anthropic(api_key=cle)
    reponse = client.messages.create(
        model=MODELE_ANTHROPIC,
        max_tokens=1024,
        messages=historique,
    )
    log_cost(calculer_cout(reponse.usage))
    return reponse.content[0].text


def trier_emails_urgents(emails):
    """Ajoute un champ "urgent" (bool) à chaque email de la liste, en demandant au modèle
    actif (Ollama ou Anthropic) lesquels nécessitent une action rapide.
    Si l'appel échoue ou renvoie un format inattendu, aucun email n'est marqué urgent
    (dégradation silencieuse : la liste reste utilisable, juste sans tri)."""
    if not emails:
        return []

    resume = "\n".join(
        f"- id={e['id']} | sujet: {e['sujet']} | expéditeur: {e['expediteur']} | date: {e['date']}"
        for e in emails
    )
    prompt = (
        "Voici les derniers mails d'une boîte de réception. Réponds UNIQUEMENT avec un objet JSON "
        'de la forme {"urgents": ["id1", "id2"]}, sans aucun texte autour, contenant les id des '
        "mails nécessitant une action rapide (deadline proche, sujet important, expéditeur "
        "professionnel/académique). Ignore newsletters, promotions et alertes automatiques "
        "récurrentes de Google.\n\n" + resume
    )

    try:
        reponse = generer_reponse([{"role": "user", "content": prompt}])
        debut, fin = reponse.index("{"), reponse.rindex("}") + 1
        ids_urgents = set(json.loads(reponse[debut:fin]).get("urgents", []))
    except Exception:
        ids_urgents = set()

    for e in emails:
        e["urgent"] = e["id"] in ids_urgents
    return emails


def rediger_reponse_email(email):
    """Propose une réponse à un email, avec un ton adapté à l'expéditeur (formel pour un
    contact professionnel/académique, décontracté pour un contact personnel). Le texte
    généré est un brouillon éditable : rien n'est envoyé sans validation + clic explicite
    côté dashboard (voir /api/gmail/<id>/send)."""
    prompt = (
        "Rédige une réponse à ce mail, en français, avec un ton adapté à l'expéditeur "
        "(formel s'il semble professionnel ou académique, décontracté s'il semble personnel). "
        "Réponds UNIQUEMENT avec le texte de la réponse, sans objet, sans formule du type "
        "« Voici une proposition de réponse », et sans notes entre crochets.\n\n"
        f"Sujet : {email['sujet']}\n"
        f"Expéditeur : {email['expediteur']}\n"
        f"Contenu du mail :\n{email['corps'][:3000]}"
    )
    return generer_reponse([{"role": "user", "content": prompt}])


def detecter_deadlines(mails: list[dict]) -> list[dict]:
    """Analyse le corps de mails (avec leur contenu complet, champ "corps") pour repérer des
    deadlines explicites ou implicites (date limite, réunion déplacée, rendu attendu...).
    Renvoie une liste vide si rien n'est détecté ou si l'appel IA échoue (même principe de
    dégradation silencieuse que trier_emails_urgents : une suggestion en moins, pas un plantage)."""
    if not mails:
        return []

    aujourdhui = datetime.now().strftime("%A %d %B %Y")
    resume = "\n\n".join(
        f"Mail id={m['id']} | sujet : {m['sujet']}\n{m['corps'][:1500]}" for m in mails
    )
    prompt = (
        f"Nous sommes le {aujourdhui}. Voici des mails jugés urgents. Repère toute deadline "
        "explicite ou implicite (date limite, rendu attendu, réunion déplacée à confirmer...). "
        'Réponds UNIQUEMENT avec un JSON de la forme '
        '{"deadlines": [{"mail_id": "...", "titre": "...", "date": "AAAA-MM-JJ", "heure": "HH:MM ou null"}]}, '
        "sans aucun texte autour. Si aucune deadline n'est identifiable, réponds "
        '{"deadlines": []}. N\'invente jamais de date : ignore un mail si la date exacte '
        "n'est pas déductible de son contenu.\n\n" + resume
    )
    try:
        reponse = generer_reponse([{"role": "user", "content": prompt}])
        debut, fin = reponse.index("{"), reponse.rindex("}") + 1
        return json.loads(reponse[debut:fin]).get("deadlines", [])
    except Exception:
        return []


def generer_briefing(mails_urgents: list[dict], evenements_jour: list[dict], deadlines: list[dict]) -> str:
    """Chaînage : combine mails urgents + événements du jour + deadlines détectées en un seul
    texte de briefing, dont la longueur s'adapte au niveau d'urgence (calme -> synthèse courte,
    urgences détectées -> briefing détaillé), conformément au cahier des charges."""
    rien_d_urgent = not mails_urgents and not deadlines
    resume_mails = "\n".join(f"- {m['sujet']} (de {m['expediteur']})" for m in mails_urgents) or "Aucun"
    resume_evenements = "\n".join(f"- {e.get('summary') or '(sans titre)'}" for e in evenements_jour) or "Aucun"
    resume_deadlines = "\n".join(f"- {d.get('titre')} ({d.get('date')})" for d in deadlines) or "Aucune"

    consigne_longueur = (
        "Rien d'urgent aujourd'hui : rédige une synthèse courte, 3 à 4 lignes maximum."
        if rien_d_urgent
        else "Des urgences ont été détectées : rédige un briefing détaillé, avec le contexte utile de chaque point."
    )

    prompt = (
        "Rédige un briefing du matin en français, ton direct et concret, sans formule de politesse "
        "ni salutation.\n"
        f"{consigne_longueur}\n\n"
        f"Mails urgents :\n{resume_mails}\n\n"
        f"Événements du jour :\n{resume_evenements}\n\n"
        f"Deadlines détectées dans les mails :\n{resume_deadlines}"
    )
    return generer_reponse([{"role": "user", "content": prompt}])
