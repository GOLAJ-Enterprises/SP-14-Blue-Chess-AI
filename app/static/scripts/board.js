let selectedSquare = {};

document.addEventListener("DOMContentLoaded", function () {
    updateBoard(true);
});

function isLowerCase(str) {
    return str === str.toLowerCase() && str !== str.toUpperCase();
}

function selectedSquareEmpty() {
    return Object.keys(selectedSquare).length === 0;
}

function toAlgebraic(row, col) {
    const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
    return files[col] + (8 - row);
}

function updateBoard(fadeIn = false) {
    fetch("/get/board", {
        method: "GET",
        headers: {"Content-Type": "application/json"},
    })
    .then(res => res.json())
    .then(data => {
        board = data.board;
        const squares = document.querySelectorAll(".square");

        for (let i = 0; i < board.length; i++) {
            board[i].forEach((piece, v) => {
                const squareIndex = i * 8 + v;
                const squareDiv = squares[squareIndex];
                
                squareDiv.querySelectorAll("img").forEach(img => img.remove());

                if (piece !== "") {
                    const img = document.createElement("img");
                    const color = isLowerCase(piece) ? "b" : "w";
                    img.src = `/static/images/pieces_svg/${color}_${piece.toLowerCase()}.svg`;
                    img.classList.add("piece");
                    img.draggable = false;
                    img.setAttribute("data-color", color);

                    if (fadeIn) {
                        img.classList.add("fade-in");

                        setTimeout(() => {
                            img.classList.remove("fade-in");
                        }, 400);
                    }

                    addDragToPiece(img);
                    squareDiv.appendChild(img);
                }
            })
        }
    });

    fetch("/get/stats", {
        method: "GET",
        headers: {"Content-Type": "application/json"},
    })
    .then(res => res.json())
    .then(data => {
        const colorSpan = document.querySelector(".active-color");
        const castlingSpan = document.querySelector(".castling-availability");
        const enPassantSpan = document.querySelector(".en-passant-target");
        const halfmoveSpan = document.querySelector(".halfmove-clock");
        const fullmoveSpan = document.querySelector(".fullmove-num");

        colorSpan.innerHTML = data.color.toUpperCase();
        castlingSpan.innerHTML = data.castling_rights;
        enPassantSpan.innerHTML = data.en_passant;
        halfmoveSpan.innerHTML = data.halfmove;
        fullmoveSpan.innerHTML = data.fullmove;
    });
}

async function movePiece(fromSquare, toSquare) {
    return fetch("/move", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            from: fromSquare,
            to: toSquare,
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            return true;
        }
        return false;
    })
}

function resetBoard() {
    fetch("/reset", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (!selectedSquareEmpty()) {
                selectedSquare.square.classList.remove("highlight");
                selectedSquare = {};
            }
            updateBoard(true);
        }
    });
}

async function handleSquareClick(row, col) {
    const squareName = toAlgebraic(row, col);
    const square = document.querySelectorAll(".square")[row * 8 + col];
    const img = square.querySelector("img");

    if (selectedSquareEmpty() && img) {
        selectedSquare = {"squareName": squareName, "square": square, "img": img};
        selectedSquare.square.classList.add("highlight");
    } else if (!selectedSquareEmpty()) {
        let success = false;

        if ((img && img.dataset.color !== selectedSquare.img.dataset.color) || !img) {
            let fromSquare = toAlgebraic(selectedSquare.square.dataset.row, selectedSquare.square.dataset.col);
            let toSquare = toAlgebraic(square.dataset.row, square.dataset.col);
            success = await movePiece(fromSquare, toSquare);
        }

        if (img) {
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {"squareName": squareName, "square": square, "img": img};
            selectedSquare.square.classList.add("highlight");
        }

        if (success) {
            updateBoard();
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {};
        }
    }
}

function addDragToPiece(piece) {
    let isDragging = false;
    let startX, startY;

    piece.addEventListener("mousedown", (e) => {
        e.preventDefault();
        
        const sourceSquare = piece.parentElement;
        draggedPiece = piece;

        startX = e.clientX;
        startY = e.clientY;

        function onMouseMove(e) {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (!isDragging && distance > 10) {
                isDragging = true;

                document.body.appendChild(piece);

                piece.style.position = "fixed";
                piece.style.zIndex = "1000";
                piece.style.pointerEvents = "none";
                piece.style.width = sourceSquare.offsetWidth + "px";
                piece.style.height = sourceSquare.offsetHeight + "px";
                piece.style.margin = "0";
            }

            if (isDragging) {
                if (!selectedSquareEmpty()) {
                    selectedSquare.square.classList.remove("highlight");
                    selectedSquare = {};
                }

                moveAt(e.clientX, e.clientY);
            }
        }

        document.addEventListener("mousemove", onMouseMove);

        document.addEventListener("mouseup", async (e) => {
            document.removeEventListener("mousemove", onMouseMove);

            if (isDragging) {
                const target = document.elementFromPoint(e.clientX, e.clientY);
                const dropSquare = target?.closest(".square");
                const img = dropSquare?.querySelector("img")

                let destinationSquare = sourceSquare;
                let success = false;

                if (dropSquare && 
                    ((img && img.dataset.color !== piece.dataset.color) || !img)
                ) {
                    const fromSquare = toAlgebraic(sourceSquare.dataset.row, sourceSquare.dataset.col);
                    const toSquare = toAlgebraic(dropSquare.dataset.row, dropSquare.dataset.col);
                    
                    success = await movePiece(fromSquare, toSquare);

                    if (success) {
                        destinationSquare = dropSquare;
                        destinationSquare.appendChild(piece);
                        updateBoard();
                    }
                }

                if (!success) {
                    destinationSquare.appendChild(piece);
                }

                piece.style.position = "";
                piece.style.zIndex = "";
                piece.style.pointerEvents = "";
                piece.style.width = "";
                piece.style.height = "";
                piece.style.margin = "";

            }

            isDragging = false;
            draggedPiece = null;
        }, {once: true});
    });

    function moveAt(x, y) {
        piece.style.left = x - piece.offsetWidth / 2 + "px";
        piece.style.top = y - piece.offsetHeight / 2 + "px";
    }
}