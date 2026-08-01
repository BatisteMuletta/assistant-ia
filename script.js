// Dashboard — script.js
// Étape 2 : chat Claude (via serveur local), bascule Ollama/Anthropic, suivi des coûts.
// Gmail/Calendar (étape 3), suggestions/notes (étapes 4-5) pas encore branchés.

const SVG_TOGGLE_LEFT = `<path d="M6 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M2 12a6 6 0 0 1 6 -6h8a6 6 0 0 1 6 6a6 6 0 0 1 -6 6h-8a6 6 0 0 1 -6 -6" />`;
const SVG_TOGGLE_RIGHT = `<path d="M14 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M2 12a6 6 0 0 1 6 -6h8a6 6 0 0 1 6 6a6 6 0 0 1 -6 6h-8a6 6 0 0 1 -6 -6" />`;

// Compte Gmail réellement connecté à ce dashboard (voir carnet d'apprentissage,
// session 6/10) — ciblé explicitement par adresse dans le lien "Ouvrir dans Gmail" ;
// sans ça, Gmail ouvre le compte en position 0 du navigateur, pas forcément le bon
// si plusieurs comptes Google sont connectés en même temps.
const COMPTE_GMAIL_DASHBOARD = "batistemuletta7@gmail.com";

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
    // Utilisé par le lien "Ouvrir dans Gmail" du bloc réponse : le thread_id n'est
    // renvoyé que par le détail d'un mail, pas par la liste initiale.
    email.thread_id = donnees.thread_id || "";
  } catch {
    conteneurCorps.textContent = "Impossible de joindre le serveur local.";
  }
}

// Construit le bloc "brouillon" d'un mail : le dashboard ne peut PAS envoyer de mail
// (aucune route d'envoi côté serveur, et le jeton OAuth Gmail est en lecture seule —
// voir gmail_mcp.py). Claude ne fait que proposer un texte de réponse, éditable ; c'est
// l'utilisateur qui le copie et le colle lui-même dans Gmail, après avoir cliqué sur
// "Répondre" dans le fil ouvert via le lien ci-dessous.
function creerZoneReponse(email) {
  const zone = document.createElement("div");
  zone.className = "zone-reponse";
  zone.hidden = true;
  // Empêche tout clic à l'intérieur (y compris taper dans le brouillon) de
  // remonter jusqu'au bloc email et de refermer le mail (comme pour les autres panneaux)
  zone.addEventListener("click", (evenement) => evenement.stopPropagation());

  const btnGenerer = document.createElement("button");
  btnGenerer.type = "button";
  btnGenerer.className = "btn-repondre";
  btnGenerer.textContent = "Générer un brouillon";

  const zoneBrouillon = document.createElement("div");
  zoneBrouillon.className = "zone-brouillon";
  zoneBrouillon.hidden = true;

  const texteBrouillon = document.createElement("textarea");
  texteBrouillon.className = "texte-brouillon";
  texteBrouillon.rows = 6;

  const actions = document.createElement("div");
  actions.className = "actions-brouillon";

  const btnCopier = document.createElement("button");
  btnCopier.type = "button";
  btnCopier.className = "btn-copier";
  btnCopier.textContent = "Copier";

  const lienGmail = document.createElement("button");
  lienGmail.type = "button";
  lienGmail.className = "btn-ouvrir-gmail";
  lienGmail.textContent = "Ouvrir dans Gmail ↗";
  lienGmail.title = "Ouvre ce fil dans Gmail — clique sur \"Répondre\" là-bas, puis colle le brouillon";

  const statut = document.createElement("div");
  statut.className = "statut-reponse";

  actions.appendChild(btnCopier);
  actions.appendChild(lienGmail);
  zoneBrouillon.appendChild(texteBrouillon);
  zoneBrouillon.appendChild(actions);
  zoneBrouillon.appendChild(statut);
  zone.appendChild(btnGenerer);
  zone.appendChild(zoneBrouillon);

  btnGenerer.addEventListener("click", async () => {
    btnGenerer.hidden = true;
    zoneBrouillon.hidden = false;
    texteBrouillon.disabled = true;
    texteBrouillon.value = "Génération du brouillon…";

    try {
      const reponse = await fetch(`/api/gmail/${encodeURIComponent(email.id)}/draft`, { method: "POST" });
      const donnees = await reponse.json();
      if (!reponse.ok) {
        texteBrouillon.value = "";
        statut.textContent = donnees.erreur || "Impossible de générer un brouillon.";
        statut.className = "statut-reponse erreur";
        btnGenerer.hidden = false;
        zoneBrouillon.hidden = true;
        return;
      }
      texteBrouillon.value = donnees.brouillon;
    } catch {
      texteBrouillon.value = "";
      statut.textContent = "Impossible de joindre le serveur local.";
      statut.className = "statut-reponse erreur";
      btnGenerer.hidden = false;
      zoneBrouillon.hidden = true;
      return;
    }
    texteBrouillon.disabled = false;
  });

  btnCopier.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(texteBrouillon.value);
      statut.textContent = "Brouillon copié ✓";
      statut.className = "statut-reponse succes";
    } catch {
      statut.textContent = "Impossible de copier — sélectionne le texte manuellement.";
      statut.className = "statut-reponse erreur";
    }
  });

  // Ouvre le fil directement dans Gmail (nouvel onglet) : c'est là que l'utilisateur
  // clique lui-même sur "Répondre" et colle le brouillon — le dashboard n'envoie rien.
  // authuser=<adresse> cible explicitement le bon compte, plutôt que /u/0/ qui dépend
  // de l'ordre de connexion des comptes dans le navigateur (source du bug : ouvrait
  // parfois un autre compte Google connecté en parallèle).
  lienGmail.addEventListener("click", () => {
    const cle = email.thread_id || email.id;
    const url = `https://mail.google.com/mail/?authuser=${encodeURIComponent(COMPTE_GMAIL_DASHBOARD)}#all/${encodeURIComponent(cle)}`;
    window.open(url, "_blank", "noopener");
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

// --- Fichiers détectés (~/Downloads) : scan manuel, jamais automatique ---
// Chaque étape reste un clic explicite distinct : "Scanner" ne fait que lister des noms
// (autorisé sans permission) ; "Lire et proposer un nom" EST l'autorisation de lire le
// contenu de ce fichier précis (renomme aussitôt, automatique par conception — voir
// ia_provider.OUTILS_FICHIERS) ; le déplacement vers Cours/Perso/Pro reste, lui,
// toujours confirmé, quelle que soit la catégorie choisie.
const btnScannerFichiers = document.getElementById("btn-scanner-fichiers");
const listeFichiers = document.getElementById("liste-fichiers");

btnScannerFichiers.addEventListener("click", async () => {
  btnScannerFichiers.disabled = true;
  btnScannerFichiers.textContent = "Scan…";
  try {
    const reponse = await fetch("/api/fichiers/scan", { method: "POST" });
    const donnees = await reponse.json();
    for (const fichier of donnees.nouveaux || []) {
      listeFichiers.appendChild(creerLigneFichier(fichier));
    }
    if (!listeFichiers.children.length) {
      listeFichiers.textContent = "Aucun nouveau fichier.";
    }
  } catch {
    listeFichiers.textContent = "Impossible de joindre le serveur local.";
  }
  btnScannerFichiers.disabled = false;
  btnScannerFichiers.textContent = "Scanner";
});

function creerLigneFichier(fichier) {
  const carte = document.createElement("div");
  carte.className = "fichier";

  const ligne = document.createElement("div");
  ligne.className = "fichier-ligne";
  const nom = document.createElement("span");
  nom.className = "fichier-nom";
  nom.textContent = fichier.nom;
  ligne.appendChild(nom);

  const actions = document.createElement("div");
  actions.className = "fichier-actions";
  const btnLire = document.createElement("button");
  btnLire.type = "button";
  btnLire.className = "btn-ajouter-deadline";
  btnLire.textContent = "Lire et proposer un nom";
  actions.appendChild(btnLire);
  ligne.appendChild(actions);

  const statut = document.createElement("div");
  statut.className = "fichier-statut";
  statut.hidden = true;

  let nomActuel = fichier.nom;

  btnLire.addEventListener("click", async () => {
    btnLire.disabled = true;
    btnLire.textContent = "Lecture…";
    try {
      const reponse = await fetch(`/api/fichiers/${encodeURIComponent(nomActuel)}/lire`, { method: "POST" });
      const donnees = await reponse.json();
      if (!reponse.ok) {
        statut.hidden = false;
        statut.textContent = donnees.erreur || "Impossible de traiter ce fichier.";
        btnLire.hidden = true;
        return;
      }
      nomActuel = donnees.nom;
      nom.textContent = nomActuel;
      actions.textContent = "";
      statut.hidden = false;

      const categorie = donnees.categorie_proposee;
      const sousDossier = donnees.sous_dossier_propose;
      if (categorie) {
        const cible = sousDossier ? `${categorie}/${sousDossier}` : categorie;
        statut.textContent = `Renommé — déplacement proposé vers ${cible}.`;
        const btnDeplacer = document.createElement("button");
        btnDeplacer.type = "button";
        btnDeplacer.className = "btn-ajouter-deadline";
        btnDeplacer.textContent = `Déplacer vers ${cible}`;
        btnDeplacer.addEventListener("click", async () => {
          btnDeplacer.disabled = true;
          btnDeplacer.textContent = "Déplacement…";
          try {
            const rep = await fetch(`/api/fichiers/${encodeURIComponent(nomActuel)}/confirmer`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ categorie, sous_dossier: sousDossier }),
            });
            if (!rep.ok) throw new Error();
            statut.textContent = `Déplacé vers ${cible} ✓`;
            actions.textContent = "";
          } catch {
            statut.textContent = "Impossible de déplacer ce fichier.";
            btnDeplacer.disabled = false;
            btnDeplacer.textContent = `Déplacer vers ${cible}`;
          }
        });
        const btnLaisser = document.createElement("button");
        btnLaisser.type = "button";
        btnLaisser.className = "btn-ajouter-deadline";
        btnLaisser.textContent = "Laisser dans Downloads";
        btnLaisser.addEventListener("click", () => {
          statut.textContent = "Renommé, laissé dans Downloads.";
          actions.textContent = "";
        });
        actions.appendChild(btnDeplacer);
        actions.appendChild(btnLaisser);
      } else {
        statut.textContent = "Renommé, reste dans Downloads.";
      }
    } catch {
      statut.hidden = false;
      statut.textContent = "Impossible de joindre le serveur local.";
      btnLire.disabled = false;
      btnLire.textContent = "Lire et proposer un nom";
    }
  });

  carte.appendChild(ligne);
  carte.appendChild(statut);
  return carte;
}

// --- Notes (icône seule par défaut, zone de texte unique au clic) ---
// Une seule zone de texte libre, toujours entièrement visible et éditable comme un
// fichier texte (une ligne = une note). Sauvegarde automatique en tâche de fond ;
// aucun appel IA tant que l'utilisateur n'a pas cliqué explicitement sur "Analyser".
const zoneNotes = document.getElementById("zone-notes");
const panneauNotes = document.getElementById("panneau-notes");
const iconeNotes = document.getElementById("icone-notes");
const saisieNote = document.getElementById("saisie-note");
const suggestionsTaches = document.getElementById("suggestions-taches");
const statutNote = document.getElementById("statut-note");
const btnAnalyserNotes = document.getElementById("btn-analyser-notes");

let notesChargees = false;
let minuteurSauvegardeNote = null;

zoneNotes.addEventListener("click", async () => {
  const estOuvert = zoneNotes.classList.toggle("ouvert");
  panneauNotes.hidden = !estOuvert;
  iconeNotes.hidden = estOuvert;
  if (estOuvert) {
    if (!notesChargees) await chargerNotes();
    saisieNote.focus();
  }
});

panneauNotes.addEventListener("click", (evenement) => evenement.stopPropagation());

async function chargerNotes() {
  try {
    const reponse = await fetch("/api/notes");
    const donnees = await reponse.json();
    saisieNote.value = donnees.texte || "";
    notesChargees = true;
  } catch {
    statutNote.textContent = "Impossible de joindre le serveur local.";
    statutNote.className = "statut-note erreur";
  }
}

// Auto-save : un peu après la dernière frappe, pas à chaque caractère.
saisieNote.addEventListener("input", () => {
  clearTimeout(minuteurSauvegardeNote);
  minuteurSauvegardeNote = setTimeout(sauvegarderNotes, 800);
});

async function sauvegarderNotes() {
  clearTimeout(minuteurSauvegardeNote);
  try {
    await fetch("/api/notes", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texte: saisieNote.value }),
    });
  } catch {
    statutNote.textContent = "Impossible de joindre le serveur local.";
    statutNote.className = "statut-note erreur";
  }
}

btnAnalyserNotes.addEventListener("click", async () => {
  btnAnalyserNotes.disabled = true;
  statutNote.textContent = "Analyse…";
  statutNote.className = "statut-note";

  try {
    await sauvegarderNotes(); // s'assure d'analyser le texte le plus récent
    const reponse = await fetch("/api/notes/analyser", { method: "POST" });
    const donnees = await reponse.json();
    if (!reponse.ok) {
      statutNote.textContent = donnees.erreur || "Impossible d'analyser les notes.";
      statutNote.className = "statut-note erreur";
    } else if (donnees.suggestions.length === 0) {
      statutNote.textContent = "Rien de nouveau à proposer.";
    } else {
      statutNote.textContent = "";
      for (const suggestion of donnees.suggestions) {
        afficherSuggestionTache(suggestion);
      }
    }
  } catch {
    statutNote.textContent = "Impossible de joindre le serveur local.";
    statutNote.className = "statut-note erreur";
  }
  btnAnalyserNotes.disabled = false;
});

function afficherSuggestionTache(suggestion) {
  suggestionsTaches.hidden = false;

  const ligne = document.createElement("div");
  ligne.className = "suggestion-tache";

  const texte = document.createElement("span");
  texte.textContent = `Ajouter comme tâche : "${suggestion.tache_suggeree}" ?`;

  const btnConfirmer = document.createElement("button");
  btnConfirmer.type = "button";
  btnConfirmer.textContent = "Confirmer";

  const btnIgnorer = document.createElement("button");
  btnIgnorer.type = "button";
  btnIgnorer.textContent = "Ignorer";

  btnConfirmer.addEventListener("click", async () => {
    btnConfirmer.disabled = true;
    btnIgnorer.disabled = true;
    try {
      const reponse = await fetch("/api/taches/confirmer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texte: suggestion.tache_suggeree,
          urgent: suggestion.urgent,
          note_id: suggestion.note_id,
        }),
      });
      if (!reponse.ok) throw new Error();
      ligne.remove();
      if (!suggestionsTaches.children.length) suggestionsTaches.hidden = true;
    } catch {
      statutNote.textContent = "Impossible d'ajouter la tâche.";
      statutNote.className = "statut-note erreur";
      btnConfirmer.disabled = false;
      btnIgnorer.disabled = false;
    }
  });

  btnIgnorer.addEventListener("click", async () => {
    btnConfirmer.disabled = true;
    btnIgnorer.disabled = true;
    try {
      const reponse = await fetch(`/api/notes/${encodeURIComponent(suggestion.note_id)}/ignorer`, {
        method: "POST",
      });
      if (!reponse.ok) throw new Error();
      ligne.remove();
      if (!suggestionsTaches.children.length) suggestionsTaches.hidden = true;
    } catch {
      statutNote.textContent = "Impossible d'ignorer cette suggestion.";
      statutNote.className = "statut-note erreur";
      btnConfirmer.disabled = false;
      btnIgnorer.disabled = false;
    }
  });

  ligne.appendChild(texte);
  ligne.appendChild(btnConfirmer);
  ligne.appendChild(btnIgnorer);
  suggestionsTaches.appendChild(ligne);
}

// --- Tâches (icône seule par défaut, liste au clic) ---
const zoneTaches = document.getElementById("zone-taches");
const panneauTaches = document.getElementById("panneau-taches");
const iconeTaches = document.getElementById("icone-taches");
const listeTaches = document.getElementById("liste-taches");
const formAjoutTache = document.getElementById("form-ajout-tache");
const btnAjouterTache = document.getElementById("btn-ajouter-tache");
const saisieTache = document.getElementById("saisie-tache");

zoneTaches.addEventListener("click", async () => {
  const estOuvert = zoneTaches.classList.toggle("ouvert");
  panneauTaches.hidden = !estOuvert;
  iconeTaches.hidden = estOuvert;
  if (estOuvert) await rafraichirTaches();
});

panneauTaches.addEventListener("click", (evenement) => evenement.stopPropagation());

// Bouton "+" : ajout manuel d'une tâche, indépendant des suggestions venues des notes.
btnAjouterTache.addEventListener("click", () => {
  btnAjouterTache.hidden = true;
  saisieTache.hidden = false;
  saisieTache.focus();
});

function refermerAjoutTache() {
  saisieTache.value = "";
  saisieTache.hidden = true;
  btnAjouterTache.hidden = false;
}

saisieTache.addEventListener("keydown", (evenement) => {
  if (evenement.key === "Escape") refermerAjoutTache();
});

// Un clic hors du champ (sans avoir rien tapé) revient simplement au bouton "+"
saisieTache.addEventListener("blur", () => {
  if (!saisieTache.value.trim()) refermerAjoutTache();
});

formAjoutTache.addEventListener("submit", async (evenement) => {
  evenement.preventDefault();
  const texte = saisieTache.value.trim();
  if (!texte) {
    refermerAjoutTache();
    return;
  }
  saisieTache.disabled = true;
  try {
    const reponse = await fetch("/api/taches/confirmer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texte, urgent: false }),
    });
    if (!reponse.ok) throw new Error();
    saisieTache.disabled = false;
    refermerAjoutTache();
    await rafraichirTaches();
  } catch {
    // On laisse le texte saisi pour réessayer, plutôt que de le perdre.
    saisieTache.disabled = false;
    saisieTache.focus();
  }
});

async function rafraichirTaches() {
  listeTaches.textContent = "Chargement…";
  try {
    const reponse = await fetch("/api/taches");
    const taches = await reponse.json();
    listeTaches.textContent = "";

    if (taches.length === 0) {
      const vide = document.createElement("div");
      vide.className = "vide";
      vide.textContent = "Aucune tâche.";
      listeTaches.appendChild(vide);
      return;
    }

    // Urgentes d'abord, tri stable (ne mélange pas l'ordre au sein d'un même groupe)
    const triees = [...taches].sort((a, b) => (b.urgent === true) - (a.urgent === true));
    for (const tache of triees) {
      listeTaches.appendChild(creerLigneTache(tache));
    }
  } catch {
    listeTaches.textContent = "";
    const erreur = document.createElement("div");
    erreur.className = "erreur";
    erreur.textContent = "Impossible de joindre le serveur local.";
    listeTaches.appendChild(erreur);
  }
}

function creerLigneTache(tache) {
  const ligne = document.createElement("label");
  ligne.className = "tache" + (tache.urgent ? " urgent" : "") + (tache.fait ? " fait" : "");

  const case_ = document.createElement("input");
  case_.type = "checkbox";
  case_.checked = tache.fait;

  const texte = document.createElement("span");
  texte.textContent = tache.texte;

  case_.addEventListener("change", async () => {
    case_.disabled = true;
    try {
      const reponse = await fetch(`/api/taches/${encodeURIComponent(tache.id)}/toggle`, { method: "POST" });
      if (!reponse.ok) throw new Error();
      const misAJour = await reponse.json();
      ligne.classList.toggle("fait", misAJour.fait);
    } catch {
      case_.checked = !case_.checked; // annule le changement visuel si l'appel a échoué
    }
    case_.disabled = false;
  });

  ligne.appendChild(case_);
  ligne.appendChild(texte);
  return ligne;
}

// --- Fermeture des panneaux en cliquant en dehors ---
// Chat/calendrier/gmail/suggestion/notes/tâches partagent le même défaut : leur panneau
// recouvre entièrement la zone une fois ouvert (pas de zone-couts, plus simple, pas concernée).
// Or chacun stoppe la propagation du clic pour ne pas se refermer tout seul en cliquant
// dedans (voir plus haut) — du coup il ne restait plus aucun pixel cliquable de la zone
// elle-même pour la refermer. Un seul clic n'importe où ailleurs sur la page referme donc
// maintenant le panneau ouvert, comme n'importe quelle appli.
const ZONES_BASCULABLES = [
  { zone: zoneChat, panneau: panneauChat, icone: iconeChat },
  { zone: zoneCalendrier, panneau: panneauCalendrier, icone: iconeCalendrier },
  { zone: zoneGmail, panneau: panneauGmail, icone: iconeGmail },
  { zone: zoneSuggestion, panneau: panneauSuggestion, icone: iconeSuggestion },
  { zone: zoneNotes, panneau: panneauNotes, icone: iconeNotes },
  { zone: zoneTaches, panneau: panneauTaches, icone: iconeTaches },
];

document.addEventListener("click", (evenement) => {
  for (const { zone, panneau, icone } of ZONES_BASCULABLES) {
    if (zone.classList.contains("ouvert") && !zone.contains(evenement.target)) {
      zone.classList.remove("ouvert");
      panneau.hidden = true;
      icone.hidden = false;
    }
  }
});

chargerProviderInitial();
