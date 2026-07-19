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

// --- Gmail (icône seule par défaut, liste au clic) ---
const zoneGmail = document.getElementById("zone-gmail");
const panneauGmail = document.getElementById("panneau-gmail");
const iconeGmail = document.getElementById("icone-gmail");
const listeEmails = document.getElementById("liste-emails");

zoneGmail.addEventListener("click", async () => {
  const estOuvert = zoneGmail.classList.toggle("ouvert");
  panneauGmail.hidden = !estOuvert;
  iconeGmail.hidden = estOuvert;
  if (estOuvert) await rafraichirGmail();
});

// Empêche le clic dans le panneau de refermer Gmail (comme pour le chat et le calendrier)
panneauGmail.addEventListener("click", (evenement) => evenement.stopPropagation());

function afficherMessageListeEmails(texte, classe) {
  listeEmails.textContent = "";
  const bloc = document.createElement("div");
  bloc.className = classe;
  bloc.textContent = texte;
  listeEmails.appendChild(bloc);
}

async function rafraichirGmail() {
  afficherMessageListeEmails("Chargement…", "vide");

  try {
    const reponse = await fetch("/api/gmail");
    const donnees = await reponse.json();
    if (!reponse.ok) {
      afficherMessageListeEmails(donnees.erreur || "Gmail indisponible.", "erreur");
      return;
    }
    if (donnees.length === 0) {
      afficherMessageListeEmails("Aucun mail récent.", "vide");
      return;
    }

    listeEmails.textContent = "";
    // Tri stable : les urgents remontent en premier, sans mélanger l'ordre entre eux
    const emailsTries = [...donnees].sort((a, b) => (b.urgent === true) - (a.urgent === true));
    for (const email of emailsTries) {
      const bloc = document.createElement("div");
      bloc.className = "email" + (email.urgent ? " urgent" : "");

      const sujet = document.createElement("div");
      sujet.className = "sujet";
      sujet.textContent = email.sujet || "(Sans sujet)";

      const expediteur = document.createElement("div");
      expediteur.className = "expediteur";
      expediteur.textContent = email.expediteur;

      const corps = document.createElement("div");
      corps.className = "corps-email";
      corps.hidden = true;

      const zoneReponse = creerZoneReponse(email);

      bloc.appendChild(sujet);
      bloc.appendChild(expediteur);
      bloc.appendChild(corps);
      bloc.appendChild(zoneReponse);

      bloc.addEventListener("click", () => ouvrirFermerEmail(email, corps, zoneReponse));

      listeEmails.appendChild(bloc);
    }
  } catch {
    afficherMessageListeEmails("Impossible de joindre le serveur local.", "erreur");
  }
}

async function ouvrirFermerEmail(email, conteneurCorps, zoneReponse) {
  const doitFermer = !conteneurCorps.hidden;
  conteneurCorps.hidden = doitFermer;
  zoneReponse.hidden = doitFermer;
  if (doitFermer) return;

  // Chargé une seule fois par mail, mis en cache dans le DOM (dataset.charge)
  if (conteneurCorps.dataset.charge) return;
  conteneurCorps.textContent = "Chargement…";

  try {
    const reponse = await fetch(`/api/gmail/${encodeURIComponent(email.id)}`);
    const donnees = await reponse.json();
    if (!reponse.ok) {
      conteneurCorps.textContent = donnees.erreur || "Impossible de charger ce mail.";
      return;
    }
    conteneurCorps.textContent = donnees.corps || "(Corps vide)";
    conteneurCorps.dataset.charge = "1";
  } catch {
    conteneurCorps.textContent = "Impossible de joindre le serveur local.";
  }
}

// Construit le bloc "Répondre" d'un mail : brouillon généré par l'IA (Ollama/Claude
// selon le provider actif), toujours éditable, jamais envoyé sans clic explicite sur
// "Envoyer" (règle du cahier des charges : validation + bouton d'envoi obligatoire).
function creerZoneReponse(email) {
  const zone = document.createElement("div");
  zone.className = "zone-reponse";
  zone.hidden = true;
  // Empêche tout clic à l'intérieur (y compris taper dans le brouillon) de
  // remonter jusqu'au bloc email et de refermer le mail (comme pour les autres panneaux)
  zone.addEventListener("click", (evenement) => evenement.stopPropagation());

  const btnRepondre = document.createElement("button");
  btnRepondre.type = "button";
  btnRepondre.className = "btn-repondre";
  btnRepondre.textContent = "Répondre";

  const zoneBrouillon = document.createElement("div");
  zoneBrouillon.className = "zone-brouillon";
  zoneBrouillon.hidden = true;

  const texteBrouillon = document.createElement("textarea");
  texteBrouillon.className = "texte-brouillon";
  texteBrouillon.rows = 6;

  const btnEnvoyer = document.createElement("button");
  btnEnvoyer.type = "button";
  btnEnvoyer.className = "btn-envoyer";
  btnEnvoyer.textContent = "Envoyer";

  const statut = document.createElement("div");
  statut.className = "statut-envoi";

  zoneBrouillon.appendChild(texteBrouillon);
  zoneBrouillon.appendChild(btnEnvoyer);
  zoneBrouillon.appendChild(statut);
  zone.appendChild(btnRepondre);
  zone.appendChild(zoneBrouillon);

  btnRepondre.addEventListener("click", async () => {
    btnRepondre.hidden = true;
    zoneBrouillon.hidden = false;
    texteBrouillon.disabled = true;
    texteBrouillon.value = "Génération du brouillon…";

    try {
      const reponse = await fetch(`/api/gmail/${encodeURIComponent(email.id)}/draft`, { method: "POST" });
      const donnees = await reponse.json();
      if (!reponse.ok) {
        texteBrouillon.value = "";
        statut.textContent = donnees.erreur || "Impossible de générer un brouillon.";
        statut.className = "statut-envoi erreur";
        btnRepondre.hidden = false;
        zoneBrouillon.hidden = true;
        return;
      }
      texteBrouillon.value = donnees.brouillon;
    } catch {
      texteBrouillon.value = "";
      statut.textContent = "Impossible de joindre le serveur local.";
      statut.className = "statut-envoi erreur";
      btnRepondre.hidden = false;
      zoneBrouillon.hidden = true;
      return;
    }
    texteBrouillon.disabled = false;
  });

  btnEnvoyer.addEventListener("click", async () => {
    const corpsReponse = texteBrouillon.value.trim();
    if (!corpsReponse) return;
    btnEnvoyer.disabled = true;
    statut.textContent = "Envoi…";
    statut.className = "statut-envoi";

    try {
      const reponse = await fetch(`/api/gmail/${encodeURIComponent(email.id)}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ corps: corpsReponse }),
      });
      const donnees = await reponse.json();
      if (!reponse.ok) {
        statut.textContent = donnees.erreur || "Échec de l'envoi.";
        statut.className = "statut-envoi erreur";
        btnEnvoyer.disabled = false;
        return;
      }
      statut.textContent = "Envoyé.";
      statut.className = "statut-envoi succes";
      texteBrouillon.disabled = true;
    } catch {
      statut.textContent = "Impossible de joindre le serveur local.";
      statut.className = "statut-envoi erreur";
      btnEnvoyer.disabled = false;
    }
  });

  return zone;
}

// --- Suggestions / briefing du matin (icône seule par défaut, généré au clic) ---
const zoneSuggestion = document.getElementById("zone-suggestion");
const panneauSuggestion = document.getElementById("panneau-suggestion");
const iconeSuggestion = document.getElementById("icone-suggestion");
const texteBriefing = document.getElementById("texte-briefing");
const listeDeadlines = document.getElementById("liste-deadlines");

zoneSuggestion.addEventListener("click", async () => {
  const estOuvert = zoneSuggestion.classList.toggle("ouvert");
  panneauSuggestion.hidden = !estOuvert;
  iconeSuggestion.hidden = estOuvert;
  if (estOuvert) await rafraichirBriefing();
});

// Empêche le clic dans le panneau de refermer la zone (comme pour les autres panneaux)
panneauSuggestion.addEventListener("click", (evenement) => evenement.stopPropagation());

async function rafraichirBriefing() {
  texteBriefing.textContent = "Génération du briefing…";
  listeDeadlines.textContent = "";

  try {
    const reponse = await fetch("/api/briefing", { method: "POST" });
    const donnees = await reponse.json();
    if (!reponse.ok) {
      texteBriefing.textContent = donnees.erreur || "Briefing indisponible.";
      return;
    }

    // Le texte du briefing contient du Markdown, comme les réponses du chat : même
    // traitement (marked -> HTML, puis DOMPurify pour retirer tout code exécutable).
    texteBriefing.innerHTML = DOMPurify.sanitize(marked.parse(donnees.texte || ""));

    listeDeadlines.textContent = "";
    for (const deadline of donnees.deadlines || []) {
      listeDeadlines.appendChild(creerLigneDeadline(deadline));
    }
  } catch {
    texteBriefing.textContent = "Impossible de joindre le serveur local.";
  }
}

function creerLigneDeadline(deadline) {
  const ligne = document.createElement("div");
  ligne.className = "deadline";

  const info = document.createElement("div");
  info.className = "deadline-info";
  const quand = deadline.heure ? `${deadline.date} à ${deadline.heure}` : deadline.date;
  info.textContent = `${deadline.titre} — ${quand}`;

  const bouton = document.createElement("button");
  bouton.type = "button";
  bouton.className = "btn-ajouter-deadline";
  bouton.textContent = "Ajouter au calendrier";

  bouton.addEventListener("click", async () => {
    bouton.disabled = true;
    bouton.textContent = "Ajout…";
    try {
      const reponse = await fetch("/api/briefing/deadline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titre: deadline.titre, date: deadline.date, heure: deadline.heure }),
      });
      const donnees = await reponse.json();
      if (!reponse.ok) {
        bouton.textContent = donnees.erreur || "Échec de l'ajout";
        bouton.disabled = false;
        return;
      }
      bouton.textContent = "Ajouté ✓";
    } catch {
      bouton.textContent = "Serveur local injoignable";
      bouton.disabled = false;
    }
  });

  ligne.appendChild(info);
  ligne.appendChild(bouton);
  return ligne;
}

chargerProviderInitial();
