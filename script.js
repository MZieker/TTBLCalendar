const GAMES_DATA_URL = "games.json";
const TABLE_DATA_URL = "table.json";
const OWN_TEAM_NAME = "Borussia Düsseldorf";

const MONTH_NAMES = [
  "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
  "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
];

const WEEKDAY_NAMES = [
  "Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"
];

function parseGameDate(datum, uhrzeit) {
  const [day, month, year] = datum.split(".").map(Number);
  const [hour, minute] = uhrzeit.split(":").map(Number);
  return new Date(year, month - 1, day, hour, minute);
}

async function loadGames() {
  const response = await fetch(GAMES_DATA_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`games.json konnte nicht geladen werden (Status ${response.status})`);
  }
  const rawGames = await response.json();
  return rawGames
    .map((game) => ({ ...game, dateObj: parseGameDate(game.datum, game.uhrzeit) }))
    .sort((a, b) => a.dateObj - b.dateObj);
}

async function loadTable() {
  const response = await fetch(TABLE_DATA_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`table.json konnte nicht geladen werden (Status ${response.status})`);
  }
  const rawTable = await response.json();
  return rawTable.slice().sort((a, b) => a.platz - b.platz);
}

function renderTable(table) {
  const body = document.getElementById("standings-body");
  body.innerHTML = "";

  table.forEach((team) => {
    const row = document.createElement("tr");
    if (team.name === OWN_TEAM_NAME) row.classList.add("is-own-team");

    row.innerHTML = `
      <td>${team.platz}</td>
      <td>${team.name}</td>
      <td>${team.spiele}</td>
      <td>${team.punkte}</td>
    `;

    body.appendChild(row);
  });
}

function renderGames(games) {
  const container = document.getElementById("games-list");
  const now = new Date();
  const nextGame = games.find((g) => g.dateObj >= now);

  container.innerHTML = "";

  games.forEach((game) => {
    const card = document.createElement("div");
    card.className = `game-card ${game.heimspiel ? "is-home" : "is-away"}`;
    if (nextGame && game === nextGame) card.classList.add("is-next");
    if (game.dateObj < now) card.classList.add("is-past");

    const day = String(game.dateObj.getDate()).padStart(2, "0");
    const month = MONTH_NAMES[game.dateObj.getMonth()];
    const weekday = WEEKDAY_NAMES[game.dateObj.getDay()];
    const matchup = game.heimspiel
      ? `Borussia Düsseldorf – ${game.gegner}`
      : `${game.gegner} – Borussia Düsseldorf`;
    const typeLabel = game.heimspiel ? "Heim" : "Auswärts";

    card.innerHTML = `
      <div class="game-date">
        <span class="day">${day}</span>
        <span class="month">${month}</span>
      </div>
      <div class="game-details">
        <p class="game-opponent">${matchup}</p>
        <p class="game-meta">
          <span class="type-badge">${typeLabel}</span>
          <span>${weekday}, ${game.datum}</span>
          <span>${game.uhrzeit} Uhr</span>
          <span>${game.ort}</span>
        </p>
      </div>
      ${nextGame && game === nextGame ? '<span class="game-badge">Nächstes Spiel</span>' : ""}
    `;

    container.appendChild(card);
  });
}

function updateCountdown(games) {
  const now = new Date();
  const nextGame = games.find((g) => g.dateObj >= now);

  const daysEl = document.getElementById("cd-days");
  const hoursEl = document.getElementById("cd-hours");
  const minutesEl = document.getElementById("cd-minutes");
  const secondsEl = document.getElementById("cd-seconds");
  const infoEl = document.getElementById("next-game-info");
  const titleEl = document.getElementById("countdown-title");

  if (!nextGame) {
    titleEl.textContent = "Saison beendet";
    daysEl.textContent = "--";
    hoursEl.textContent = "--";
    minutesEl.textContent = "--";
    secondsEl.textContent = "--";
    infoEl.textContent = "Aktuell sind keine weiteren Spiele geplant.";
    return;
  }

  const diff = nextGame.dateObj - now;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
  const minutes = Math.floor((diff / (1000 * 60)) % 60);
  const seconds = Math.floor((diff / 1000) % 60);

  daysEl.textContent = String(days);
  hoursEl.textContent = String(hours).padStart(2, "0");
  minutesEl.textContent = String(minutes).padStart(2, "0");
  secondsEl.textContent = String(seconds).padStart(2, "0");

  infoEl.textContent = `gegen ${nextGame.gegner} am ${nextGame.datum} um ${nextGame.uhrzeit} Uhr · ${nextGame.ort}`;
}

async function initGames() {
  try {
    const games = await loadGames();
    renderGames(games);
    updateCountdown(games);
    setInterval(() => updateCountdown(games), 1000);
  } catch (error) {
    console.error(error);
    document.getElementById("games-list").innerHTML =
      "<p class=\"load-error\">Die Spieldaten konnten nicht geladen werden.</p>";
    document.getElementById("countdown-title").textContent = "Fehler beim Laden";
  }
}

async function initTable() {
  try {
    const table = await loadTable();
    renderTable(table);
  } catch (error) {
    console.error(error);
    document.getElementById("standings-body").innerHTML = "";
    document.querySelector(".table-scroll").innerHTML =
      "<p class=\"load-error\">Die Tabelle konnte nicht geladen werden.</p>";
  }
}

initGames();
initTable();
