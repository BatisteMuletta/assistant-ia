# ia_provider.py — Point de config unique pour toutes les fonctionnalités IA du dashboard
#
# Tout le code (chat, futur tri mails, futures analyses) doit appeler generer_reponse()
# et ne jamais parler directement à Ollama ou à l'API Anthropic. Basculer de modèle
# devient ainsi un changement de config (config.json), pas une réécriture du code
# — même logique qu'une couche d'abstraction matérielle (HAL) en embarqué.

import json
import os
from pathlib import Path

import requests
from anthropic import Anthropic
from dotenv import load_dotenv

from costs import SEUIL_ANOMALIE, calculer_cout, get_total_spent, log_cost

load_dotenv()

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"

MODELE_OLLAMA = "llama3.2:3b"
MODELE_ANTHROPIC = "claude-haiku-4-5-20251001"  # modèle le moins cher, cohérent avec le budget serré


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


def generer_reponse(message):
    provider = lire_provider()
    if provider == "anthropic":
        return _appel_anthropic(message)
    return _appel_ollama(message)


def _appel_ollama(message):
    reponse = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODELE_OLLAMA, "prompt": message, "stream": False},
        timeout=60,
    )
    reponse.raise_for_status()
    return reponse.json()["response"]


def _appel_anthropic(message):
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
        messages=[{"role": "user", "content": message}],
    )
    log_cost(calculer_cout(reponse.usage))
    return reponse.content[0].text
