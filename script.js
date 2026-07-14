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
  saisieChat.value = "";

  try {
    const reponse = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const donnees = await reponse.json();
    if (!reponse.ok) {
      ajouterMessage(donnees.erreur || "Erreur inconnue", "erreur");
      return;
    }
    ajouterMessage(donnees.reponse, "assistant");
  } catch {
    ajouterMessage("Impossible de joindre le serveur local.", "erreur");
  }
});

// Empêche le clic dans le panneau de refermer le chat (event bubbling vers zoneChat)
panneauChat.addEventListener("click", (evenement) => evenement.stopPropagation());

function ajouterMessage(texte, type) {
  const bulle = document.createElement("div");
  bulle.className = `message ${type}`;
  bulle.textContent = texte;
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
    detailCouts.textContent = `⚠ Anomalie : ${donnees.depense}€ (seuil de secours ${donnees.seuil_anomalie}€ atteint)`;
    detailCouts.classList.add("anomalie");
  } else {
    detailCouts.textContent = `${donnees.depense}€ / ${donnees.seuil_principal}€`;
    detailCouts.classList.remove("anomalie");
  }
}

chargerProviderInitial();
