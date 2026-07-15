// Dashboard — script.js
// Étape 2 : chat Claude (via serveur local), bascule Ollama/Anthropic, suivi des coûts.
// Gmail/Calendar (étape 3), suggestions/notes (étapes 4-5) pas encore branchés.

const SVG_TOGGLE_LEFT = `<path d="M6 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M2 12a6 6 0 0 1 6 -6h8a6 6 0 0 1 6 6a6 6 0 0 1 -6 6h-8a6 6 0 0 1 -6 -6" />`;
const SVG_TOGGLE_RIGHT = `<path d="M14 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M2 12a6 6 0 0 1 6 -6h8a6 6 0 0 1 6 6a6 6 0 0 1 -6 6h-8a6 6 0 0 1 -6 -6" />`;

// --- Chat ---
const zoneChat = document.getElementById("zone-chat");
const panneauChat = document.getElementById("panneau-chat");
const iconeChat = document.getElementById("icone-chat");
const messagesChat = document.getElementById("messages-chat");
const formChat = document.getElementById("form-chat");
const saisieChat = document.getElementById("saisie-chat");

// Historique de la conversation en cours (remis à zéro si la page est rechargée).
// Envoyé en entier à chaque message pour que Claude garde le contexte
// (sinon chaque message est traité isolément, voir bug "d'autres" incohérent).
let historique = [];

zoneChat.addEventListener("click", () => {
  const estOuvert = zoneChat.classList.toggle("ouvert");
  panneauChat.hidden = !estOuvert;
  iconeChat.hidden = estOuvert;
  if (estOuvert) saisieChat.focus();
});

formChat.addEventListener("submit", async (evenement) => {
  evenement.preventDefault();
  evenement.stopPropagation();
  const message = saisieChat.value.trim();
  if (!message) return;

  ajouterMessage(message, "utilisateur");
  historique.push({ role: "user", content: message });
  saisieChat.value = "";

  try {
    const reponse = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ historique }),
    });
    const donnees = await reponse.json();
    if (!reponse.ok) {
      ajouterMessage(donnees.erreur || "Erreur inconnue", "erreur");
      return;
    }
    ajouterMessage(donnees.reponse, "assistant");
    historique.push({ role: "assistant", content: donnees.reponse });
  } catch {
    ajouterMessage("Impossible de joindre le serveur local.", "erreur");
  }
});

// Empêche le clic dans le panneau de refermer le chat (event bubbling vers zoneChat)
panneauChat.addEventListener("click", (evenement) => evenement.stopPropagation());

function ajouterMessage(texte, type) {
  const bulle = document.createElement("div");
  bulle.className = `message ${type}`;
  if (type === "assistant") {
    // Réponse de Claude : contient du Markdown (#, **, listes...) -> on le
    // transforme en HTML, puis DOMPurify retire tout ce qui pourrait exécuter
    // du code (balises <script>, attributs onclick...).
    bulle.innerHTML = DOMPurify.sanitize(marked.parse(texte));
  } else {
    bulle.textContent = texte;
  }
  messagesChat.appendChild(bulle);
  messagesChat.scrollTop = messagesChat.scrollHeight;
}

// --- Bascule Ollama / Anthropic ---
const btnProvider = document.getElementById("btn-provider");
const iconeProvider = document.getElementById("icone-provider");

function appliquerEtatProvider(provider) {
  const surAnthropic = provider === "anthropic";
  btnProvider.classList.toggle("provider-anthropic", surAnthropic);
  iconeProvider.innerHTML = surAnthropic ? SVG_TOGGLE_RIGHT : SVG_TOGGLE_LEFT;
  btnProvider.title = surAnthropic
    ? "API Anthropic active (payant) — clic pour repasser sur Ollama"
    : "Ollama actif (local, gratuit) — clic pour basculer sur l'API Anthropic";
}

btnProvider.addEventListener("click", async () => {
  const reponse = await fetch("/api/provider/toggle", { method: "POST" });
  const donnees = await reponse.json();
  appliquerEtatProvider(donnees.provider);
  rafraichirCouts();
});

async function chargerProviderInitial() {
  const reponse = await fetch("/api/provider");
  const donnees = await reponse.json();
  appliquerEtatProvider(donnees.provider);
}

// --- Suivi des coûts (icône seule par défaut, détail au clic) ---
const zoneCouts = document.getElementById("zone-couts");
const detailCouts = document.getElementById("detail-couts");

zoneCouts.addEventListener("click", async () => {
  const estVisible = !detailCouts.hidden;
  if (estVisible) {
    detailCouts.hidden = true;
    return;
  }
  await rafraichirCouts();
  detailCouts.hidden = false;
});

async function rafraichirCouts() {
  const reponse = await fetch("/api/costs");
  const donnees = await reponse.json();
  if (donnees.anomalie) {
    detailCouts.textContent = `⚠ Anomalie : ${donnees.depense}$ (seuil de secours ${donnees.seuil_anomalie}$ atteint)`;
    detailCouts.classList.add("anomalie");
  } else {
    detailCouts.textContent = `${donnees.depense}$ / ${donnees.seuil_principal}$`;
    detailCouts.classList.remove("anomalie");
  }
}

// --- Calendrier (icône seule par défaut, bande de 7 jours au clic) ---
const zoneCalendrier = document.getElementById("zone-calendrier");
const panneauCalendrier = document.getElementById("panneau-calendrier");
const iconeCalendrier = document.getElementById("icone-calendrier");
const joursSemaine = document.getElementById("jours-semaine");
const detailJour = document.getElementById("detail-jour");

let evenementsParJour = new Map(); // clé "AAAA-MM-JJ" -> tableau d'événements ce jour-là
let jourSelectionne = null; // clé "AAAA-MM-JJ" du jour actuellement déroulé, ou null

zoneCalendrier.addEventListener("click", async () => {
  const estOuvert = zoneCalendrier.classList.toggle("ouvert");
  panneauCalendrier.hidden = !estOuvert;
  iconeCalendrier.hidden = estOuvert;
  if (estOuvert) await rafraichirCalendrier();
});

// Empêche le clic dans le panneau de refermer le calendrier (comme pour le chat)
panneauCalendrier.addEventListener("click", (evenement) => evenement.stopPropagation());

function cleJour(date) {
  // "AAAA-MM-JJ" en heure locale (pas toISOString, qui repasse en UTC et peut changer de jour)
  const annee = date.getFullYear();
  const mois = String(date.getMonth() + 1).padStart(2, "0");
  const jour = String(date.getDate()).padStart(2, "0");
  return `${annee}-${mois}-${jour}`;
}

function joursDeLaSemaineCourante() {
  const aujourdhui = new Date();
  // getDay() : dimanche=0 ... samedi=6 -> on veut commencer le lundi
  const decalageLundi = (aujourdhui.getDay() + 6) % 7;
  const lundi = new Date(aujourdhui);
  lundi.setDate(aujourdhui.getDate() - decalageLundi);
  lundi.setHours(0, 0, 0, 0);

  const jours = [];
  for (let i = 0; i < 7; i++) {
    const jour = new Date(lundi);
    jour.setDate(lundi.getDate() + i);
    jours.push(jour);
  }
  return jours;
}

function formaterHeure(evenement) {
  if (!evenement.start.dateTime) return "Journée entière";
  return new Date(evenement.start.dateTime).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function afficherDetailJour(cle, dateJour) {
  detailJour.textContent = "";
  const evenements = evenementsParJour.get(cle) || [];

  if (evenements.length === 0) {
    const vide = document.createElement("div");
    vide.className = "vide";
    vide.textContent = "Aucun événement ce jour.";
    detailJour.appendChild(vide);
  } else {
    for (const evenement of evenements) {
      const bloc = document.createElement("div");
      bloc.className = "evenement";
      const heure = document.createElement("div");
      heure.className = "heure";
      heure.textContent = formaterHeure(evenement);
      const titre = document.createElement("div");
      titre.textContent = evenement.summary || "(Sans titre)";
      bloc.appendChild(heure);
      bloc.appendChild(titre);
      detailJour.appendChild(bloc);
    }
  }
  detailJour.hidden = false;
}

function construireBandeJours() {
  joursSemaine.textContent = "";
  const aujourdhuiCle = cleJour(new Date());

  for (const date of joursDeLaSemaineCourante()) {
    const cle = cleJour(date);
    const aDesEvenements = evenementsParJour.has(cle);

    const cellule = document.createElement("div");
    cellule.className = "jour";
    if (cle === aujourdhuiCle) cellule.classList.add("aujourdhui");
    if (aDesEvenements) cellule.classList.add("a-des-evenements");
    if (cle === jourSelectionne) cellule.classList.add("selectionne");

    const nomJour = document.createElement("div");
    nomJour.className = "nom-jour";
    nomJour.textContent = date.toLocaleDateString("fr-FR", { weekday: "short" });

    const numeroJour = document.createElement("div");
    numeroJour.className = "numero-jour";
    numeroJour.textContent = date.getDate();

    const point = document.createElement("div");
    point.className = "point-evenement";

    cellule.appendChild(nomJour);
    cellule.appendChild(numeroJour);
    cellule.appendChild(point);

    cellule.addEventListener("click", () => {
      if (jourSelectionne === cle) {
        // Reclic sur le même jour -> referme le détail
        jourSelectionne = null;
        detailJour.hidden = true;
      } else {
        jourSelectionne = cle;
        afficherDetailJour(cle, date);
      }
      construireBandeJours(); // remet à jour la mise en surbrillance du jour sélectionné
    });

    joursSemaine.appendChild(cellule);
  }
}

async function rafraichirCalendrier() {
  evenementsParJour = new Map();
  jourSelectionne = null;
  detailJour.hidden = true;
  detailJour.textContent = "";

  try {
    const reponse = await fetch("/api/calendar");
    const donnees = await reponse.json();
    if (!reponse.ok) {
      construireBandeJours();
      detailJour.textContent = "";
      const erreur = document.createElement("div");
      erreur.className = "erreur";
      erreur.textContent = donnees.erreur || "Calendrier indisponible.";
      detailJour.appendChild(erreur);
      detailJour.hidden = false;
      return;
    }
    for (const evenement of donnees.events || []) {
      const debut = evenement.start.dateTime || evenement.start.date;
      const cle = cleJour(new Date(debut));
      if (!evenementsParJour.has(cle)) evenementsParJour.set(cle, []);
      evenementsParJour.get(cle).push(evenement);
    }
    construireBandeJours();
  } catch {
    construireBandeJours();
    const erreur = document.createElement("div");
    erreur.className = "erreur";
    erreur.textContent = "Impossible de joindre le serveur local.";
    detailJour.appendChild(erreur);
    detailJour.hidden = false;
  }
}

chargerProviderInitial();
