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


OUTILS_FICHIERS = [
    {
        "name": "renommer_fichier",
        "description": (
            "Renomme le fichier en cours de traitement, dans son dossier actuel — jamais "
            "un déplacement. Toujours appeler cet outil, même si le nom actuel semble déjà "
            "correct (proposer alors le même nom)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nouveau_nom": {
                    "type": "string",
                    "description": (
                        "Nouveau nom au format AAAA-MM-JJ_[Catégorie]_[Description].[ext] "
                        "— un simple nom de fichier, jamais un chemin."
                    ),
                }
            },
            "required": ["nouveau_nom"],
        },
    },
    {
        "name": "proposer_deplacement",
        "description": (
            "Propose de déplacer le fichier vers l'une des trois catégories (Cours, Perso, "
            "Pro), uniquement si l'un des trois s'applique clairement. N'appelle PAS cet "
            "outil en cas de doute — ce déplacement ne s'exécute jamais automatiquement, "
            "il attend une confirmation explicite de l'utilisateur, qui peut aussi créer "
            "le sous-dossier proposé."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categorie": {"type": "string", "enum": ["Cours", "Perso", "Pro"]},
                "sous_dossier": {
                    "type": "string",
                    "description": (
                        "Nom du sous-dossier dans cette catégorie (ex: 'Gestion-de-projet' "
                        "pour Cours, 'Photos' pour Perso). Reprendre un sous-dossier déjà "
                        "existant listé dans le prompt s'il correspond ; sinon en proposer "
                        "un nouveau, court, sans accents ni espaces (tirets). Omettre ce "
                        "champ seulement si le fichier ne correspond clairement à aucun "
                        "sous-classement utile."
                    ),
                },
            },
            "required": ["categorie"],
        },
    },
]


def proposer_organisation_fichier(
    nom_fichier: str,
    taille_octets: int,
    extrait_contenu: str,
    sous_dossiers_existants: dict[str, list[str]],
) -> list[dict]:
    """Tool-calling forcé sur Anthropic, quel que soit le provider actif ailleurs dans le
    dashboard — décision explicite de l'utilisateur (01/08/2026) : renommer_fichier
    s'exécute automatiquement sans confirmation humaine, la fiabilité du modèle prime ici
    sur le principe "gratuit par défaut" appliqué ailleurs (Ollama, modèle 1B, jugé trop
    peu fiable pour une action auto-exécutée). Renvoie la liste brute des appels d'outils
    demandés par le modèle (name + input) — ne les exécute jamais ici, l'exécution reste
    la responsabilité de fichiers_manager.py (voir server.py, route /api/fichiers/<nom>/lire)."""
    if get_total_spent() >= SEUIL_ANOMALIE:
        raise CoutBloqueError(
            f"Seuil de secours de {SEUIL_ANOMALIE}$ atteint ce mois-ci — appel bloqué."
        )
    cle = os.environ.get("ANTHROPIC_API_KEY")
    if not cle:
        raise CleManquanteError(
            "ANTHROPIC_API_KEY absente de .env — nécessaire pour le tool-calling du "
            "Projet 2, forcé sur Anthropic indépendamment du provider actif."
        )

    contexte_contenu = (
        f"Extrait du contenu :\n{extrait_contenu}" if extrait_contenu else "(contenu non lisible sous forme texte — se baser sur le nom et l'extension)"
    )
    aujourdhui = datetime.now().strftime("%Y-%m-%d")
    resume_sous_dossiers = "\n".join(
        f"- {categorie} : " + (", ".join(sous_dossiers) if sous_dossiers else "(aucun sous-dossier pour l'instant)")
        for categorie, sous_dossiers in sous_dossiers_existants.items()
    )
    prompt = (
        f"Nous sommes le {aujourdhui}. Voici un fichier détecté dans ~/Downloads. Propose un "
        "renommage (toujours) et, si pertinent seulement, un déplacement vers l'une des "
        "catégories Cours / Perso / Pro.\n\n"
        f"Nom actuel : {nom_fichier}\n"
        f"Taille : {taille_octets} octets\n"
        f"{contexte_contenu}\n\n"
        f"Sous-dossiers déjà existants par catégorie :\n{resume_sous_dossiers}\n\n"
        "Pour la date AAAA-MM-JJ du nouveau nom : utilise la date d'aujourd'hui donnée "
        "ci-dessus, sauf si le contenu du fichier mentionne explicitement une autre date "
        "clairement plus pertinente (ex: date du cours) — dans ce cas, utilise celle-là."
    )

    client = Anthropic(api_key=cle)
    reponse = client.messages.create(
        model=MODELE_ANTHROPIC,
        max_tokens=512,
        tools=OUTILS_FICHIERS,
        messages=[{"role": "user", "content": prompt}],
    )
    log_cost(calculer_cout(reponse.usage))
    return [
        {"name": bloc.name, "input": bloc.input}
        for bloc in reponse.content
        if bloc.type == "tool_use"
    ]


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


def analyser_notes(notes: list[dict]) -> list[dict]:
    """Analyse en un seul appel IA toutes les notes passées (liste de {"id", "texte"})
    pour repérer, par note, une éventuelle tâche à en tirer (jamais créée automatiquement
    — voir /api/taches/confirmer) et sa langue/traduction si besoin. Un seul appel pour
    tout le lot plutôt qu'un par note : moins cher, cohérent avec le suivi des coûts.
    Si l'appel échoue ou renvoie un format inattendu, aucune suggestion cette fois-ci
    (dégradation silencieuse : les notes restent telles quelles, on retentera au prochain
    clic sur "Analyser")."""
    if not notes:
        return []

    resume = "\n".join(f'- id={n["id"]} : "{n["texte"]}"' for n in notes)
    prompt = (
        "Voici une liste de notes rapides prises par l'utilisateur. Pour CHAQUE note, "
        "détecte si elle décrit une action à faire, sa langue, et sa traduction française "
        "si besoin. Réponds UNIQUEMENT avec un JSON de la forme "
        '{"resultats": [{"id": "...", "tache_suggeree": "..." ou null, "urgent": true/false, '
        '"langue": "fr"/"en"/..., "traduction": "..." ou null}, ...]}, une entrée par note, '
        "sans aucun texte autour.\n"
        "- tache_suggeree : si la note décrit une action à faire, un texte de tâche court "
        "et actionnable ; sinon null.\n"
        "- urgent : uniquement pertinent si tache_suggeree n'est pas null.\n"
        "- langue : code à 2 lettres de la langue de la note.\n"
        "- traduction : traduction française si la langue n'est pas le français, sinon null.\n\n"
        f"Notes :\n{resume}"
    )
    try:
        reponse = generer_reponse([{"role": "user", "content": prompt}])
        debut, fin = reponse.index("{"), reponse.rindex("}") + 1
        return json.loads(reponse[debut:fin]).get("resultats", [])
    except Exception:
        return []


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


def generer_briefing(
    mails_urgents: list[dict],
    evenements_jour: list[dict],
    deadlines: list[dict],
    taches_non_faites: list[dict] | None = None,
) -> str:
    """Chaînage : combine mails urgents + événements du jour + deadlines détectées +
    tâches non faites en un seul texte de briefing, dont la longueur s'adapte au niveau
    d'urgence (calme -> synthèse courte, urgences détectées -> briefing détaillé),
    conformément au cahier des charges."""
    taches_non_faites = taches_non_faites or []
    taches_urgentes = [t for t in taches_non_faites if t["urgent"]]
    rien_d_urgent = not mails_urgents and not deadlines and not taches_urgentes

    resume_mails = "\n".join(f"- {m['sujet']} (de {m['expediteur']})" for m in mails_urgents) or "Aucun"
    resume_evenements = "\n".join(f"- {e.get('summary') or '(sans titre)'}" for e in evenements_jour) or "Aucun"
    resume_deadlines = "\n".join(f"- {d.get('titre')} ({d.get('date')})" for d in deadlines) or "Aucune"
    resume_taches = "\n".join(
        f"- {t['texte']}" + (" (urgent)" if t["urgent"] else "") for t in taches_non_faites
    ) or "Aucune"

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
        f"Deadlines détectées dans les mails :\n{resume_deadlines}\n\n"
        f"Tâches non faites :\n{resume_taches}"
    )
    return generer_reponse([{"role": "user", "content": prompt}])
