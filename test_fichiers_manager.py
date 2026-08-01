# test_fichiers_manager.py — Tests de confinement pour fichiers_manager.py (Projet 2)
#
# Origine : revue de sécurité adversariale (01/08/2026) où un agent a tenté de casser
# resoudre_chemin()/renommer()/deplacer_fichier() avec 4 scénarios précis (traversée
# de chemin, lien symbolique, changement de dossier déguisé en renommage, valeur d'outil
# forgée façon injection de prompt) plutôt que de faire une relecture passive. Deux vrais
# bugs trouvés (caractère nul non rattrapé, renommage vers le même nom toujours refusé),
# corrigés, épinglés ici en tests de non-régression. Complète le grep/l'audit manuel, ne
# les remplace pas — un agent qui approuve n'est pas une preuve, un test qui passe l'est.
#
# Ajout du même jour : le déplacement gère trois catégories (Cours/Perso/Pro), chacune
# avec sous-dossiers dynamiques — `categorie` et `sous_dossier` sont deux valeurs
# proposées par le modèle, toutes deux revalidées avec les mêmes garde-fous que
# nouveau_nom (testés ici : traversée, catégorie invalide, création vs réutilisation).
#
# Isole systématiquement DOSSIER_SURVEILLE/DOSSIERS_CIBLES sur des dossiers jetables sous
# /tmp (jamais le vrai ~/Downloads ni ~/projets/Cours|Perso|Pro).
#
# Lancer : venv/bin/python -m pytest test_fichiers_manager.py -v

import pytest

import activity_log
import fichiers_manager as fm


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    watched = tmp_path / "downloads"
    cours = tmp_path / "cours"
    perso = tmp_path / "perso"
    pro = tmp_path / "pro"
    outside = tmp_path / "outside"
    watched.mkdir()
    cours.mkdir()
    perso.mkdir()
    pro.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("vrai contenu secret")

    monkeypatch.setattr(fm, "DOSSIER_SURVEILLE", watched.resolve())
    monkeypatch.setattr(
        fm,
        "DOSSIERS_CIBLES",
        {"Cours": cours.resolve(), "Perso": perso.resolve(), "Pro": pro.resolve()},
    )
    monkeypatch.setattr(fm, "FICHIER_TRAITES", tmp_path / "fichiers_traites.json")
    monkeypatch.setattr(activity_log, "LOG_PATH", tmp_path / "activity_log.json")
    return {"watched": watched, "cours": cours, "perso": perso, "pro": pro, "outside": outside}


# --- Scénario 1 : traversée de chemin ---------------------------------------
TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "../outside/secret.txt",
    "/etc/passwd",
    "normal.txt/../../outside/secret.txt",
    "....//....//outside/secret.txt",
    "",
    ".",
    "..",
]


@pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
def test_resoudre_chemin_rejette_traversee(isolated_dirs, payload):
    with pytest.raises((fm.ActionRefuseeError, fm.FichierIntrouvableError)):
        fm.resoudre_chemin(payload)


@pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
def test_lire_extrait_rejette_traversee(isolated_dirs, payload):
    with pytest.raises((fm.ActionRefuseeError, fm.FichierIntrouvableError)):
        fm.lire_extrait(payload)


@pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
def test_deplacer_fichier_rejette_traversee_dans_nom_fichier(isolated_dirs, payload):
    with pytest.raises((fm.ActionRefuseeError, fm.FichierIntrouvableError)):
        fm.deplacer_fichier(payload, "Cours", "Gestion-de-projet")


@pytest.mark.parametrize("payload", [p for p in TRAVERSAL_PAYLOADS if p != ""])
def test_deplacer_fichier_rejette_traversee_dans_sous_dossier(isolated_dirs, payload):
    """`sous_dossier` est aussi une valeur proposée par le modèle — mêmes garde-fous
    requis que pour nouveau_nom, car elle finit aussi dans un chemin de fichier.
    ("" est exclu : traité comme "pas de sous-dossier", même comportement que None,
    ce n'est pas une tentative d'évasion — voir test_deplacer_sans_sous_dossier_va_a_la_racine_de_la_categorie.)"""
    (isolated_dirs["watched"] / "source.txt").write_text("data")
    with pytest.raises(fm.ActionRefuseeError):
        fm.deplacer_fichier("source.txt", "Cours", payload)
    assert (isolated_dirs["watched"] / "source.txt").exists()


@pytest.mark.parametrize("payload", [
    "../outside",
    "/etc",
    "Downloads",
    "assistant-ia",
    "",
    "cours",  # sensible à la casse, pas une clé valide de DOSSIERS_CIBLES
])
def test_deplacer_fichier_rejette_categorie_invalide(isolated_dirs, payload):
    """`categorie` doit être une clé exacte de DOSSIERS_CIBLES — jamais un chemin ou une
    valeur approchante, même si elle a l'air plausible."""
    (isolated_dirs["watched"] / "source.txt").write_text("data")
    with pytest.raises(fm.ActionRefuseeError):
        fm.deplacer_fichier("source.txt", payload, None)
    assert (isolated_dirs["watched"] / "source.txt").exists()


@pytest.mark.parametrize("categorie", ["Cours", "Perso", "Pro"])
def test_deplacer_fichier_accepte_les_trois_categories_valides(isolated_dirs, categorie):
    (isolated_dirs["watched"] / f"fichier_{categorie}.txt").write_text("data")
    fm.deplacer_fichier(f"fichier_{categorie}.txt", categorie, None)
    assert (isolated_dirs[categorie.lower()] / f"fichier_{categorie}.txt").exists()


@pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
def test_renommer_rejette_traversee_dans_nouveau_nom(isolated_dirs, payload):
    (isolated_dirs["watched"] / "normal.txt").write_text("hello")
    with pytest.raises(fm.ActionRefuseeError):
        fm.renommer("normal.txt", payload)


def test_octet_nul_dans_nouveau_nom_est_refuse_proprement(isolated_dirs):
    """Bug trouvé le 01/08/2026 : un \\x00 passait la regex et atteignait rename() côté OS,
    provoquant un ValueError non rattrapé par server.py (qui ne capte qu'ActionRefuseeError).
    Doit maintenant être rejeté explicitement, avant tout appel système."""
    (isolated_dirs["watched"] / "invoice.txt").write_text("x")
    with pytest.raises(fm.ActionRefuseeError):
        fm.renommer("invoice.txt", "\x00.txt")


# --- Scénario 2 : lien symbolique --------------------------------------------
def test_resoudre_chemin_bloque_symlink_vers_exterieur(isolated_dirs):
    lien = isolated_dirs["watched"] / "lien_pirate.txt"
    lien.symlink_to(isolated_dirs["outside"] / "secret.txt")
    with pytest.raises(fm.ActionRefuseeError):
        fm.resoudre_chemin("lien_pirate.txt")


def test_lire_extrait_bloque_symlink_vers_exterieur(isolated_dirs):
    lien = isolated_dirs["watched"] / "lien_pirate.txt"
    lien.symlink_to(isolated_dirs["outside"] / "secret.txt")
    with pytest.raises(fm.ActionRefuseeError):
        fm.lire_extrait("lien_pirate.txt")


def test_renommer_bloque_a_travers_symlink(isolated_dirs):
    lien = isolated_dirs["watched"] / "lien_pirate.txt"
    lien.symlink_to(isolated_dirs["outside"] / "secret.txt")
    with pytest.raises(fm.ActionRefuseeError):
        fm.renommer("lien_pirate.txt", "renomme.txt")
    assert (isolated_dirs["outside"] / "secret.txt").read_text() == "vrai contenu secret"


def test_deplacer_bloque_a_travers_symlink(isolated_dirs):
    lien = isolated_dirs["watched"] / "lien_pirate.txt"
    lien.symlink_to(isolated_dirs["outside"] / "secret.txt")
    with pytest.raises(fm.ActionRefuseeError):
        fm.deplacer_fichier("lien_pirate.txt", "Cours", "Gestion-de-projet")
    assert (isolated_dirs["outside"] / "secret.txt").exists()


def test_symlink_de_dossier_bloque(isolated_dirs):
    lien_dossier = isolated_dirs["watched"] / "lien_dossier"
    lien_dossier.symlink_to(isolated_dirs["outside"])
    with pytest.raises(fm.ActionRefuseeError):
        fm.resoudre_chemin("lien_dossier/secret.txt")


def test_renommage_sur_symlink_casse_remplace_le_lien_pas_la_cible(isolated_dirs):
    """Un lien symbolique cassé posé sous le nom de destination ne doit pas devenir une
    écriture à travers le lien — os.rename() remplace l'entrée du lien elle-même."""
    watched = isolated_dirs["watched"]
    source = watched / "source.txt"
    source.write_text("données source")
    casse = watched / "destination_cassee.txt"
    casse.symlink_to(isolated_dirs["outside"] / "inexistant.txt")

    resultat = fm.renommer("source.txt", "destination_cassee.txt")

    assert resultat == "destination_cassee.txt"
    assert not (watched / "destination_cassee.txt").is_symlink()
    assert (watched / "destination_cassee.txt").read_text() == "données source"
    assert not (isolated_dirs["outside"] / "inexistant.txt").exists()


# --- Scénario 3 : changement de dossier déguisé en renommage ----------------
CHANGEMENT_DOSSIER_PAYLOADS = [
    "../outside/pwned.txt",
    "subdir/pwned.txt",
    "/tmp/pwned_abs.txt",
    "a/b/../../pwned.txt",
]


@pytest.mark.parametrize("payload", CHANGEMENT_DOSSIER_PAYLOADS)
def test_renommer_ne_peut_pas_changer_de_dossier(isolated_dirs, payload):
    (isolated_dirs["watched"] / "source.txt").write_text("data")
    with pytest.raises(fm.ActionRefuseeError):
        fm.renommer("source.txt", payload)
    assert (isolated_dirs["watched"] / "source.txt").exists()


# --- Scénario 4 : valeur d'outil forgée (façon injection de prompt) ---------
def _simuler_boucle_lire_de_server(nom_final, appels):
    """Reproduit exactement la boucle de server.fichiers_lire() sur les appels d'outils."""
    for appel in appels:
        if appel["name"] == "renommer_fichier":
            nom_final = fm.renommer(nom_final, appel["input"]["nouveau_nom"])
    return nom_final


@pytest.mark.parametrize("payload", [
    "../../../etc/passwd",
    "../outside/pwned.txt",
    "/etc/cron.d/evil",
    "....//....//outside/pwned.txt",
])
def test_valeur_outil_forgee_ne_peut_pas_s_echapper(isolated_dirs, payload):
    (isolated_dirs["watched"] / "facture.txt").write_text("contenu fabriqué par l'attaquant")
    appels = [{"name": "renommer_fichier", "input": {"nouveau_nom": payload}}]
    with pytest.raises(fm.ActionRefuseeError):
        _simuler_boucle_lire_de_server("facture.txt", appels)
    assert not (isolated_dirs["outside"] / "pwned.txt").exists()


def test_sous_dossier_forge_ne_peut_pas_rediriger_le_deplacement(isolated_dirs):
    """Même si une valeur 'sous_dossier' forgée essaie de sortir de Cours (../outside), la
    revalidation dans deplacer_fichier() (même regex + même check parent que pour
    nouveau_nom) bloque le déplacement, indépendamment de ce qu'a renvoyé le modèle."""
    (isolated_dirs["watched"] / "facture.txt").write_text("contenu fabriqué par l'attaquant")
    with pytest.raises(fm.ActionRefuseeError):
        fm.deplacer_fichier("facture.txt", "Cours", "../outside")
    assert not (isolated_dirs["outside"] / "facture.txt").exists()


# --- Sous-dossiers dynamiques (ajouté le 01/08/2026) ------------------------
def test_deplacer_cree_le_sous_dossier_si_absent(isolated_dirs):
    (isolated_dirs["watched"] / "cours.txt").write_text("contenu")
    fm.deplacer_fichier("cours.txt", "Cours", "Gestion-de-projet")
    cible = isolated_dirs["cours"] / "Gestion-de-projet" / "cours.txt"
    assert cible.exists()
    assert cible.read_text() == "contenu"


def test_deplacer_reutilise_sous_dossier_existant(isolated_dirs):
    (isolated_dirs["cours"] / "Gestion-de-projet").mkdir()
    (isolated_dirs["watched"] / "cours2.txt").write_text("contenu2")
    fm.deplacer_fichier("cours2.txt", "Cours", "Gestion-de-projet")
    assert (isolated_dirs["cours"] / "Gestion-de-projet" / "cours2.txt").exists()
    # un seul sous-dossier "Gestion-de-projet", pas de doublon créé
    assert fm.lister_sous_dossiers_existants()["Cours"] == ["Gestion-de-projet"]


def test_deplacer_sans_sous_dossier_va_a_la_racine_de_la_categorie(isolated_dirs):
    (isolated_dirs["watched"] / "divers.txt").write_text("contenu")
    fm.deplacer_fichier("divers.txt", "Perso", None)
    assert (isolated_dirs["perso"] / "divers.txt").exists()


def test_lister_sous_dossiers_existants_reflete_les_trois_categories(isolated_dirs):
    assert fm.lister_sous_dossiers_existants() == {"Cours": [], "Perso": [], "Pro": []}
    (isolated_dirs["cours"] / "Marketing").mkdir()
    (isolated_dirs["cours"] / "Finance").mkdir()
    (isolated_dirs["perso"] / "Photos").mkdir()
    resultat = fm.lister_sous_dossiers_existants()
    assert resultat["Cours"] == ["Finance", "Marketing"]
    assert resultat["Perso"] == ["Photos"]
    assert resultat["Pro"] == []


# --- Bug fonctionnel trouvé en chemin : renommer vers le même nom ----------
def test_renommer_vers_le_meme_nom_est_un_no_op(isolated_dirs):
    """ia_provider.OUTILS_FICHIERS demande explicitement au modèle de toujours appeler
    l'outil, même pour proposer le même nom si le fichier est déjà bien nommé. Bug trouvé
    le 01/08/2026 : ce cas était traité comme "nom déjà pris" et refusé à chaque fois."""
    (isolated_dirs["watched"] / "rapport_2024.txt").write_text("data")
    resultat = fm.renommer("rapport_2024.txt", "rapport_2024.txt")
    assert resultat == "rapport_2024.txt"
    assert (isolated_dirs["watched"] / "rapport_2024.txt").exists()
