let HOST_IP = null;

if (!HOST_IP) {
    const saved = localStorage.getItem("LAN_HOST_IP");
    if (saved) {
        HOST_IP = saved;
        console.log("Restored HOST_IP from localStorage:", HOST_IP);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Auto-refresh LAN games only if the list exists (i.e., not on create screen)
    const lanList = document.getElementById("lan-game-list");
    if (lanList && GAME_MODE === "lan") {
        refreshLANGames();
    }
});

function selectColor(color) {
    const url = new URL(window.location.href);
    url.searchParams.set("color", color);
    window.location.href = url.toString();
}

function goToCreateLANGame() {
    const url = new URL(window.location.href);
    url.searchParams.set("create", "true");
    window.location.href = url.toString();
}

function createLANGame(color) {
    fetch("/lan/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ color })
    })
    .then(res => res.json())
    .then(data => {
        // Redirect into the newly created game
        const url = new URL(window.location.href);
        url.searchParams.set("color", data.color);
        url.searchParams.set("game", data.game_id);
        url.searchParams.delete("create");
        window.location.href = url.toString();
    })
    .catch(err => console.error("Failed to create LAN game", err));
}

function refreshLANGames() {
    fetch("/lan/discovered")
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById("lan-game-list");
            list.innerHTML = "";

            let localGame = null;
            const otherGames = [];

            data.games.forEach(game => {
                if (game.local) {
                    localGame = game;
                } else {
                    otherGames.push(game);
                }
            });

            // Show your hosted game first (if exists)
            if (localGame) {
                const localDiv = document.createElement("div");
                localDiv.className = "lan-game-entry local";
                localDiv.textContent = `Your Hosted Game (ID: ${localGame.game_id})`;
                localDiv.onclick = () => joinLANGame(localGame);
                list.appendChild(localDiv);
            }

            // Show discovered games
            otherGames.forEach(game => {
                const li = document.createElement("li");
                li.textContent = `Game ${game.game_id} @ ${game.ip}:${game.port}`;
                li.className = "lan-game-entry";
                li.onclick = () => joinLANGame(game);
                list.appendChild(li);
            });
        })
        .catch(err => console.error("Failed to fetch LAN games", err));
}

function joinLANGame(game) {
    HOST_IP = game.ip;
    localStorage.setItem("LAN_HOST_IP", game.ip);

    fetch(`http://${HOST_IP}:5000/lan/join/${game.game_id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert("Could not join game: " + data.error);
                return;
            }

            // Store player color and redirect into game
            const url = new URL(window.location.href);
            url.searchParams.set("color", data.color);
            url.searchParams.set("game", game.game_id);
            window.location.href = url.toString();
        })
        .catch(err => {
            console.error("Join request failed:", err);
            alert("Failed to join game");
        });
}
