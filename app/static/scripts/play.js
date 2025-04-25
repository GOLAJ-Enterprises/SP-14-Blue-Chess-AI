document.addEventListener("DOMContentLoaded", () => {
    menuToggle = document.getElementById("menu-toggle");
    board = document.getElementById("chessboard");

    if (board && menuToggle) {
        menuToggle.classList.remove("hidden");
    }
});

function selectColor(color) {
    const url = new URL(window.location.href);
    url.searchParams.set("color", color);
    window.location.href = url.toString();
}