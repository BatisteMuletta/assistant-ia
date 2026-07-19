# gmail_mcp.py — Client MCP pour le serveur Gmail (~/mcp-servers/Gmail-MCP-Server)
#
# Contrairement à Calendar (serveur HTTP déjà lancé sur un port fixe), le serveur
# Gmail ne parle qu'en stdio (entrée/sortie standard) : notre client Python lance
# lui-même le processus Node à chaque appel et communique avec lui via stdin/stdout
# (StdioServerParameters + stdio_client, au lieu de streamablehttp_client).

import asyncio
import re
from html.parser import HTMLParser
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CHEMIN_SERVEUR_MCP = Path.home() / "mcp-servers" / "Gmail-MCP-Server" / "dist" / "index.js"


class ServeurGmailIndisponibleError(Exception):
    """Le serveur MCP Gmail (processus Node) n'a pas pu être lancé ou a échoué."""


async def _appeler_outil(nom_outil: str, arguments: dict) -> dict:
    parametres = StdioServerParameters(command="node", args=[str(CHEMIN_SERVEUR_MCP)])
    async with stdio_client(parametres) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resultat = await session.call_tool(nom_outil, arguments)
            return resultat.content[0].text


def _parser_emails(texte: str) -> list[dict]:
    """Transforme le texte brut du serveur MCP (blocs 'ID:/Subject:/From:/Date:' séparés
    par une ligne vide) en liste de dicts structurés."""
    emails = []
    for bloc in texte.strip().split("\n\n"):
        champs = {}
        for ligne in bloc.splitlines():
            if ": " not in ligne:
                continue
            cle, valeur = ligne.split(": ", 1)
            champs[cle.strip().lower()] = valeur.strip()
        if champs:
            emails.append(
                {
                    "id": champs.get("id", ""),
                    "sujet": champs.get("subject", ""),
                    "expediteur": champs.get("from", ""),
                    "date": champs.get("date", ""),
                }
            )
    return emails


class _ExtracteurTexteHTML(HTMLParser):
    """Réduit un corps de mail HTML à du texte lisible : ignore <script>/<style>,
    insère un saut de ligne aux séparateurs de bloc usuels (<p>, <br>, <div>...)."""

    BALISES_BLOC = {"p", "div", "tr", "li", "br", "h1", "h2", "h3", "h4"}
    BALISES_IGNOREES = {"script", "style"}

    def __init__(self):
        super().__init__()
        self._ignorer = False
        self._morceaux = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BALISES_IGNOREES:
            self._ignorer = True
        elif tag in self.BALISES_BLOC:
            self._morceaux.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BALISES_IGNOREES:
            self._ignorer = False

    def handle_data(self, data):
        if not self._ignorer:
            self._morceaux.append(data)

    def texte(self) -> str:
        lignes = [ligne.strip() for ligne in "".join(self._morceaux).splitlines()]
        return "\n".join(ligne for ligne in lignes if ligne)


# Espaces de largeur nulle (zero-width space/non-joiner/joiner, BOM) : utilisés par
# certains emails marketing comme espaceurs de mise en page HTML, invisibles mais
# gênants une fois convertis en texte brut.
_CARACTERES_INVISIBLES = re.compile("[\u200b\u200c\u200d\ufeff]")


def _nettoyer_corps(corps: str) -> str:
    """Convertit un corps HTML en texte lisible ; laisse le texte brut tel quel sinon."""
    corps = re.sub(r"^\[Note:.*?\]\s*", "", corps.strip())
    if re.search(r"<[a-zA-Z][^>]*>", corps):
        extracteur = _ExtracteurTexteHTML()
        extracteur.feed(corps)
        corps = extracteur.texte()
    corps = _CARACTERES_INVISIBLES.sub("", corps)
    # Une ligne devenue vide après suppression des espaceurs ne doit pas laisser
    # de blancs multiples ; on retire aussi les lignes qui ne contenaient qu'eux.
    lignes = [ligne.strip() for ligne in corps.splitlines()]
    return "\n".join(ligne for ligne in lignes if ligne)


def _parser_email_complet(texte: str) -> dict:
    """Parse le texte détaillé renvoyé par l'outil MCP read_email (en-têtes suivis
    d'une ligne vide puis du corps) en dict structuré, corps nettoyé en texte lisible."""
    entetes, _, corps = texte.partition("\n\n")
    champs = {}
    for ligne in entetes.splitlines():
        if ": " not in ligne:
            continue
        cle, valeur = ligne.split(": ", 1)
        champs[cle.strip().lower()] = valeur.strip()

    return {
        "sujet": champs.get("subject", ""),
        "expediteur": champs.get("from", ""),
        "destinataire": champs.get("to", ""),
        "date": champs.get("date", ""),
        "corps": _nettoyer_corps(corps),
        "thread_id": champs.get("thread id", ""),
    }


def lire_email(message_id: str) -> dict:
    """Retourne le contenu complet d'un email (sujet, expéditeur, destinataire, date, corps nettoyé)."""
    try:
        texte_brut = asyncio.run(_appeler_outil("read_email", {"messageId": message_id}))
    except Exception as erreur:
        raise ServeurGmailIndisponibleError(
            f"Serveur MCP Gmail injoignable ({CHEMIN_SERVEUR_MCP}) : {erreur}"
        ) from erreur
    return _parser_email_complet(texte_brut)


def lister_emails_recents(nombre: int = 10) -> list[dict]:
    """Retourne les derniers emails de la boîte de réception, structurés (id/sujet/expediteur/date)."""
    try:
        texte_brut = asyncio.run(
            _appeler_outil(
                "search_emails",
                {"query": "in:inbox", "maxResults": nombre},
            )
        )
    except Exception as erreur:
        raise ServeurGmailIndisponibleError(
            f"Serveur MCP Gmail injoignable ({CHEMIN_SERVEUR_MCP}) : {erreur}"
        ) from erreur
    return _parser_emails(texte_brut)
