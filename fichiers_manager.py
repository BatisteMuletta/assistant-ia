# fichiers_manager.py — Détection, lecture d'extrait et actions sur ~/Downloads (Projet 2)
#
# Permissions appliquées ici : voir ~/.claude/skills/rangement-fichiers/SKILL.md.
# Rappel important (pas une sandbox OS, une convention de code — voir le Skill) : toute
# action passe par resoudre_chemin(), qui canonicalise et vérifie le périmètre avant
# d'agir, jamais de confiance dans un nom de fichier tel quel.

import json
import re
import shutil
from pathlib import Path

from activity_log import journaliser

BASE_DIR = Path(__file__).parent
DOSSIER_SURVEILLE = (Path.home() / "Downloads").resolve()
# Catégories cibles pour le rangement — voir SKILL.md pour le régime de permissions de
# chacune (Cours : lecture/renommage libres ; Perso/Pro : mêmes garde-fous que Downloads
# pour tout ce qui n'est pas cette route de déplacement elle-même, toujours confirmée).
DOSSIERS_CIBLES = {
    "Cours": (Path.home() / "projets" / "Cours").resolve(),
    "Perso": (Path.home() / "projets" / "Perso").resolve(),
    "Pro": (Path.home() / "projets" / "Pro").resolve(),
}
FICHIER_TRAITES = BASE_DIR / "fichiers_traites.json"

EXTENSIONS_TEXTE = {".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css"}
# Exclut séparateurs de chemin, caractères de contrôle (dont l'octet nul — provoque un
# ValueError non rattrapé côté OS sinon, trouvé par une revue adversariale du 01/08/2026)
# et les caractères interdits sous Windows (`<>:"|?*`), cohérent avec le projet cross-platform.
NOM_FICHIER_VALIDE = re.compile(r'^[^/\\\x00-\x1f<>:"|?*]+$')


class FichierIntrouvableError(Exception):
    """Le fichier demandé n'existe pas (ou plus) dans le dossier attendu."""


class ActionRefuseeError(Exception):
    """Chemin hors périmètre, nom invalide, ou destination déjà occupée."""


def _charger_traites() -> set:
    if not FICHIER_TRAITES.exists():
        return set()
    return set(json.loads(FICHIER_TRAITES.read_text()))


def _sauvegarder_traites(noms: set) -> None:
    FICHIER_TRAITES.write_text(json.dumps(sorted(noms), indent=2, ensure_ascii=False))


def scanner_nouveaux_fichiers() -> list[dict]:
    """Compare l'état actuel de ~/Downloads à fichiers_traites.json (même principe que
    mails_notifies.json) et renvoie uniquement les fichiers jamais vus lors d'un scan
    précédent. Noms/tailles uniquement — jamais de lecture de contenu ici. Les fichiers
    renvoyés sont immédiatement marqués comme vus, pour ne pas être re-proposés au
    prochain scan même si l'utilisateur ne les traite pas tout de suite."""
    deja_vus = _charger_traites()

    actuels = {
        f.name: f
        for f in DOSSIER_SURVEILLE.iterdir()
        if f.is_file() and not f.name.startswith(".")
    }

    nouveaux_noms = sorted(set(actuels) - deja_vus)
    nouveaux = [
        {"nom": nom, "taille_octets": actuels[nom].stat().st_size}
        for nom in nouveaux_noms
    ]

    _sauvegarder_traites(deja_vus | set(actuels))
    return nouveaux


def resoudre_chemin(nom: str) -> Path:
    """Canonicalise `nom` et vérifie qu'il tombe bien, réellement, dans ~/Downloads —
    rejette tout ce qui sortirait via un lien symbolique ou un séparateur de chemin,
    quelle que soit l'apparence du nom fourni. Toute action de ce module doit passer
    par cette fonction avant de toucher au disque (fonction centralisée, voir SKILL.md)."""
    chemin = (DOSSIER_SURVEILLE / nom).resolve()
    if chemin.parent != DOSSIER_SURVEILLE:
        raise ActionRefuseeError(f"Chemin hors périmètre : {nom!r}")
    if not chemin.is_file():
        raise FichierIntrouvableError(nom)
    return chemin


def lire_extrait(nom: str) -> str:
    """Lit un extrait texte du fichier si le format le permet — texte brut uniquement
    pour l'instant (l'extraction PDF/docx/pptx est un chantier séparé, prévu pour le
    Projet 3). Renvoie une chaîne vide sinon : le nom de fichier et sa taille restent
    une base suffisante pour proposer un renommage."""
    chemin = resoudre_chemin(nom)
    if chemin.suffix.lower() not in EXTENSIONS_TEXTE:
        return ""
    try:
        return chemin.read_text(errors="ignore")[:3000]
    except OSError:
        return ""


def renommer(nom_actuel: str, nouveau_nom: str) -> str:
    """Exécute un renommage dans le même dossier — jamais un déplacement (contrainte non
    négociable, voir brief_projet2_gestionnaire_fichiers.md section 10) : nouveau_nom doit
    être un simple nom de fichier, sans séparateur de chemin. Journalisé sans exception,
    seul filet de contrôle a posteriori vu que cette action s'exécute sans confirmation
    humaine (tool-calling, voir ia_provider.proposer_organisation_fichier)."""
    if not nouveau_nom or not NOM_FICHIER_VALIDE.match(nouveau_nom) or nouveau_nom in (".", ".."):
        raise ActionRefuseeError(f"Nom de fichier invalide : {nouveau_nom!r}")

    source = resoudre_chemin(nom_actuel)
    destination = source.parent / nouveau_nom

    if destination == source:
        # Le modèle propose de garder le nom actuel (explicitement demandé dans le prompt,
        # voir ia_provider.OUTILS_FICHIERS) — pas une collision, un no-op légitime.
        return nouveau_nom

    if destination.exists():
        journaliser(f"Renommage refusé (nom déjà pris) : {nom_actuel} → {nouveau_nom}")
        raise ActionRefuseeError(f"Un fichier nommé {nouveau_nom!r} existe déjà.")

    try:
        source.rename(destination)
    except OSError as erreur:
        # Filet de sécurité : toute erreur OS sur le renommage (nom invalide au sens du
        # système de fichiers, etc.) devient une erreur gérée plutôt qu'un 500 non rattrapé
        # côté serveur (trouvé par une revue adversariale du 01/08/2026).
        raise ActionRefuseeError(f"Renommage impossible : {erreur}") from erreur

    journaliser(f"Fichier renommé automatiquement : {nom_actuel} → {nouveau_nom}")
    return nouveau_nom


def lister_sous_dossiers_existants() -> dict[str, list[str]]:
    """Sous-dossiers déjà présents dans chaque catégorie cible — pas de liste figée (voir
    SKILL.md) : le modèle s'appuie sur ceux-ci pour proposer un classement cohérent
    (même sous-dossier réutilisé pour un même sujet) plutôt que d'en inventer un nouveau
    à chaque fois. Noms de dossiers uniquement, jamais de contenu lu ici."""
    resultat = {}
    for categorie, dossier in DOSSIERS_CIBLES.items():
        if dossier.is_dir():
            resultat[categorie] = sorted(
                d.name for d in dossier.iterdir() if d.is_dir() and not d.name.startswith(".")
            )
        else:
            resultat[categorie] = []
    return resultat


def deplacer_fichier(nom_fichier: str, categorie: str, sous_dossier: str | None = None) -> None:
    """Exécuté uniquement sur confirmation explicite côté dashboard (jamais automatique,
    à la différence de renommer()). `categorie` et `sous_dossier` sont des valeurs
    proposées par le modèle (tool-calling) — `categorie` doit être une clé exacte de
    DOSSIERS_CIBLES (pas un chemin arbitraire), `sous_dossier` revalidé avec les mêmes
    garde-fous que nouveau_nom. Crée le sous-dossier s'il n'existe pas encore (la
    confirmation de l'utilisateur couvre cette création)."""
    if categorie not in DOSSIERS_CIBLES:
        raise ActionRefuseeError(f"Catégorie invalide : {categorie!r}")
    dossier_categorie = DOSSIERS_CIBLES[categorie]

    source = resoudre_chemin(nom_fichier)

    dossier_cible = dossier_categorie
    sous_dossier_nouveau = False
    if sous_dossier:
        if not NOM_FICHIER_VALIDE.match(sous_dossier) or sous_dossier in (".", ".."):
            raise ActionRefuseeError(f"Nom de sous-dossier invalide : {sous_dossier!r}")
        dossier_cible = (dossier_categorie / sous_dossier).resolve()
        if dossier_cible.parent != dossier_categorie:
            raise ActionRefuseeError("Sous-dossier hors périmètre.")
        sous_dossier_nouveau = not dossier_cible.exists()
        dossier_cible.mkdir(parents=False, exist_ok=True)

    destination = (dossier_cible / nom_fichier).resolve()
    if destination.parent != dossier_cible:
        raise ActionRefuseeError("Destination hors périmètre.")
    if destination.exists():
        raise ActionRefuseeError(f"{nom_fichier!r} existe déjà à cet endroit.")

    try:
        shutil.move(str(source), str(destination))
    except OSError as erreur:
        raise ActionRefuseeError(f"Déplacement impossible : {erreur}") from erreur

    cible_lisible = f"{categorie}/{sous_dossier}" if sous_dossier else categorie
    if sous_dossier_nouveau:
        journaliser(f"Nouveau sous-dossier créé : {cible_lisible}")
    journaliser(f"Fichier déplacé vers {cible_lisible} (confirmé) : {nom_fichier}")
