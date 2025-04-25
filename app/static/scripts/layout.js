document.addEventListener("DOMContentLoaded", () => {
    const board = document.getElementById("chessboard");
    const stats = document.getElementById("game-stats");

    if (board && stats) {
        stats.classList.remove("hidden");
    }
});

function goHome() {
    window.location.href = "/";
}
