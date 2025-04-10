let selectedSquare = {};
const boardSizeInput = document.getElementById("board-size");
const chessboard = document.getElementById("chessboard");
let boardAnimateTimeout;

document.addEventListener("DOMContentLoaded", () => {
    updateBoardScale(boardSizeInput.value, false);
    updateBoard(true);
    
    setTimeout(() => {
        chessboard.classList.add("loaded");
    }, 0);
});

boardSizeInput.addEventListener("input", (e) => {
    updateBoardScale(e.target.value, true);
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

function updateBoardScale(sliderValue, animate) {
    let squareSize = 70 + 20 * parseInt(sliderValue, 10);

    if (animate) {
        chessboard.classList.add("animate");

        clearTimeout(boardAnimateTimeout);

        boardAnimateTimeout = setTimeout(() => {
            chessboard.classList.remove("animate");
        }, 200);
    }

    chessboard.style.setProperty("--square-size", `${squareSize}px`)
}

function updateBoard(fadeIn) {
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
                        }, 300);
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

        colorSpan.innerHTML = data.color.toLowerCase() === "w" ? "White" : "Black";
        castlingSpan.innerHTML = data.castling_rights;
        enPassantSpan.innerHTML = data.en_passant;
        halfmoveSpan.innerHTML = data.halfmove;
        fullmoveSpan.innerHTML = data.fullmove;
    });

    fetch("/get/state", {
        method: "GET",
        headers: {"Content-Type": "application/json"},
    })
    .then(res => res.json())
    .then(data => {
        const stateSpan = document.querySelector(".game-state");

        stateSpan.innerHTML = data.state;
    });
}

async function movePiece(fromSquare, toSquare) {
    return fetch("/move", {
        method: "POST",
        headers: {"Content-Type": "text/plain"},
        body: fromSquare + toSquare
    })
    .then(res => res.json())
    .then(data => {
        return data.success === true;
    });
}

function resetBoard() {
    fetch("/reset", {method: "POST"})
    .then(() => {
        if (!selectedSquareEmpty()) {
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {};
        }
        updateBoard(true);
    });
}

function undoMove() {
    fetch("/undo", {method: "POST"})
    .then(() => {
        if (!selectedSquareEmpty()) {
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {};
        }
        updateBoard(true);
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
        const canMoveSquare = (img && img.dataset.color !== selectedSquare.img.dataset.color) || !img;

        if (canMoveSquare) {
            const fromSquare = selectedSquare.square.id;
            let toSquare = square.id;

            if (selectedSquare.img.src.endsWith("p.svg") && 
            (toSquare.endsWith("1") || toSquare.endsWith("8"))) {
                toSquare += "q";
            }

            success = await movePiece(fromSquare, toSquare);
        }

        if (img) {
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {"squareName": squareName, "square": square, "img": img};
            selectedSquare.square.classList.add("highlight");
        }

        if (success) {
            updateBoard(false);
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {};
        } else if (canMoveSquare) {
            selectedSquare.square.classList.remove("highlight");
            selectedSquare = {};
            square.classList.add("error");

            setTimeout(() => {
                square.classList.remove("error");
            }, 500);
        }
    }
}

function addDragToPiece(piece) {
    let isDragging = false;
    let startX, startY;

    piece.addEventListener("mousedown", (e) => {
        e.preventDefault();

        const sourceSquare = piece.parentElement;
        const chessboard = document.getElementById("chessboard");
        const boardRect = chessboard.getBoundingClientRect();

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
                const img = dropSquare?.querySelector("img");

                const canMoveSquare = dropSquare && ((img && img.dataset.color !== piece.dataset.color) || !img);

                let destinationSquare = sourceSquare;
                let success = false;

                const fromSquare = sourceSquare.id;
                let toSquare = dropSquare?.id;

                if (canMoveSquare && dropSquare) {
                    if (piece.src.endsWith("p.svg") && (toSquare.endsWith("1") || toSquare.endsWith("8"))) {
                        toSquare += "q";
                    }

                    success = await movePiece(fromSquare, toSquare);

                    if (success) {
                        destinationSquare = dropSquare;
                        destinationSquare.appendChild(piece);
                        updateBoard(false);
                    }
                }

                if (!success) {
                    destinationSquare.appendChild(piece);

                    if (canMoveSquare && dropSquare && fromSquare !== toSquare) {
                        dropSquare.classList.add("error");

                        setTimeout(() => {
                            dropSquare.classList.remove("error");
                        }, 500);
                    }
                }

                piece.style.position = "";
                piece.style.zIndex = "";
                piece.style.pointerEvents = "";
                piece.style.width = "";
                piece.style.height = "";
                piece.style.margin = "";
                piece.style.top = "";
                piece.style.left = "";
            }

            isDragging = false;
        }, { once: true });

        function moveAt(x, y) {
            const halfWidth = piece.offsetWidth / 2;
            const halfHeight = piece.offsetHeight / 2;

            // Clamp x/y to chessboard bounds
            const clampedX = Math.max(boardRect.left + halfWidth, Math.min(x, boardRect.right - halfWidth));
            const clampedY = Math.max(boardRect.top + halfHeight, Math.min(y, boardRect.bottom - halfHeight));

            piece.style.left = clampedX - halfWidth + "px";
            piece.style.top = clampedY - halfHeight + "px";
        }
    });
}
