# calendar_mcp.py — Client MCP pour le serveur Calendar (~/mcp-servers/google-calendar-mcp)
#
# Notre serveur Flask joue ici le rôle de "client MCP" : il se connecte en HTTP
# au serveur MCP Calendar (processus Node séparé, lancé manuellement sur
# localhost:3000) et lui demande d'exécuter des outils (list-events...).
# Le protocole MCP est basé sur asyncio (Python asynchrone) ; comme le reste du
# serveur est synchrone, chaque appel est exécuté via asyncio.run().

import asyncio
from datetime import datetime, timedelta, timezone

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL_SERVEUR_MCP = "http://127.0.0.1:3000/"


class ServeurCalendarIndisponibleError(Exception):
    """Le serveur MCP Calendar (processus Node) ne répond pas."""


async def _appeler_outil(nom_outil: str, arguments: dict) -> dict:
    async with streamablehttp_client(URL_SERVEUR_MCP) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resultat = await session.call_tool(nom_outil, arguments)
            return resultat.content[0].text


def _bornes_semaine_courante() -> tuple[str, str]:
    """Lundi 00h00 -> lundi suivant 00h00, au format attendu par l'API Google Calendar."""
    maintenant = datetime.now(timezone.utc)
    lundi = maintenant - timedelta(days=maintenant.weekday())
    lundi = lundi.replace(hour=0, minute=0, second=0, microsecond=0)
    lundi_suivant = lundi + timedelta(days=7)
    return lundi.isoformat(), lundi_suivant.isoformat()


def lister_evenements_semaine() -> str:
    """Retourne le JSON brut renvoyé par le serveur MCP (liste des événements de la semaine)."""
    debut, fin = _bornes_semaine_courante()
    try:
        return asyncio.run(
            _appeler_outil(
                "list-events",
                {"calendarId": "primary", "timeMin": debut, "timeMax": fin},
            )
        )
    except Exception as erreur:
        raise ServeurCalendarIndisponibleError(
            f"Serveur MCP Calendar injoignable sur {URL_SERVEUR_MCP} : {erreur}"
        ) from erreur
