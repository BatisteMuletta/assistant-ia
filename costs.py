# costs.py — Suivi des dépenses API Anthropic (double seuil, voir cahier des charges)
#
# Seuil principal (7,5€) : informationnel côté serveur, la vraie barrière est le
# plafond configuré dans la Console Anthropic (crédits prépayés + auto-reload désactivé).
# Seuil de secours (10€) : blocage réel ici, ne devrait jamais être atteint en
# fonctionnement normal — s'il l'est, c'est une anomalie (le plafond Console a échoué).
#
# Prix approximatifs (à vérifier sur console.anthropic.com/settings/billing avant
# de s'y fier pour un vrai suivi précis — le seuil de secours sert de filet, pas
# de compteur exact).

import json
from datetime import datetime
from pathlib import Path

COSTS_PATH = Path(__file__).parent / "costs.json"

SEUIL_PRINCIPAL = 7.5
SEUIL_ANOMALIE = 10.0

PRIX_INPUT_PAR_TOKEN = 3.0 / 1_000_000
PRIX_OUTPUT_PAR_TOKEN = 15.0 / 1_000_000


def _mois_courant():
    return datetime.now().strftime("%Y-%m")


def _lire_donnees():
    if not COSTS_PATH.exists():
        return {}
    return json.loads(COSTS_PATH.read_text())


def get_total_spent(mois=None):
    donnees = _lire_donnees()
    mois = mois or _mois_courant()
    return donnees.get(mois, 0.0)


def log_cost(montant_euros):
    donnees = _lire_donnees()
    mois = _mois_courant()
    donnees[mois] = donnees.get(mois, 0.0) + montant_euros
    COSTS_PATH.write_text(json.dumps(donnees, indent=2))


def calculer_cout(usage):
    """usage = objet Anthropic avec .input_tokens / .output_tokens"""
    return (usage.input_tokens * PRIX_INPUT_PAR_TOKEN) + (
        usage.output_tokens * PRIX_OUTPUT_PAR_TOKEN
    )


def etat_couts():
    depense = get_total_spent()
    return {
        "depense": round(depense, 4),
        "seuil_principal": SEUIL_PRINCIPAL,
        "reste_avant_seuil_principal": round(max(0, SEUIL_PRINCIPAL - depense), 4),
        "seuil_anomalie": SEUIL_ANOMALIE,
        "anomalie": depense >= SEUIL_ANOMALIE,
    }
