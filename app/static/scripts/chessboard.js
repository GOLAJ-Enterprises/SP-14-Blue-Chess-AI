let turn = null;
let selectedSquare = null;
const params = new URLSearchParams(window.location.search);
const gameMode = params.get("pvp") === "true" ? "pvp"
            : params.get("ai") === "true" ? "ai"
            : params.get("lan") === "true" ? "lan"
            : "unknown";
const playerColor = params.get("color") || null; // 'white', 'black', or null
const INITIAL_POSITION = {
    a1: "w_r", b1: "w_n", c1: "w_b", d1: "w_q", e1: "w_k", f1: "w_b", g1: "w_n", h1: "w_r",
    a2: "w_p", b2: "w_p", c2: "w_p", d2: "w_p", e2: "w_p", f2: "w_p", g2: "w_p", h2: "w_p",
    a7: "b_p", b7: "b_p", c7: "b_p", d7: "b_p", e7: "b_p", f7: "b_p", g7: "b_p", h7: "b_p",
    a8: "b_r", b8: "b_n", c8: "b_b", d8: "b_q", e8: "b_k", f8: "b_b", g8: "b_n", h8: "b_r"
};

document.addEventListener("DOMContentLoaded", () => {
    const boardContainer = document.querySelector(".chessboard-container");
    const board = document.getElementById("chessboard");
    const isAiGame = new URLSearchParams(window.location.search).get("ai") === "true";
    
    // Rotate board if necessary, and fill board.
    if (board) {
        if (isAiGame && playerColor === "b") {
            boardContainer.classList.add("rotated");
    
            // Wait for rotation to visually finish (1s)
            setTimeout(() => {
                renderInitialPosition();
            }, 1000); // match the CSS transition duration
        } else {
            renderInitialPosition();
        }
    }
    
    // Initialize turn
    if (board) {
        fetch(api("/get/turn"))
        .then(res => res.json())
        .then(data => {
            if (data.turn) {
                turn = data.turn;
                // Auto-trigger AI move after load if player is black
                if (isAiGame && playerColor === "b" && turn === "w") {
                    setTimeout(() => {
                        aiMove();
                    }, 2010);
                }
            } else {
                console.error("Turn initialization error:", data.error)
            }
        });
    }
});

function api(path) {
    const ip = HOST_IP || localStorage.getItem("LAN_HOST_IP");
    if (ip) {
        return `http://${ip}:5000${path}`;
    }
    return path;  // default to current origin if no host set
}

function renderInitialPosition() {
    fetch(api("/get/board"))
        .then(res => res.json())
        .then(data => {
            const board = data.board; // 8x8 array of symbols

            // Flatten to entries like [["e2", "P"], ["a7", "p"], ...]
            const entries = [];

            for (let row = 0; row < 8; row++) {
                for (let col = 0; col < 8; col++) {
                    const symbol = board[row][col];
                    if (symbol) {
                        const uci = String.fromCharCode(97 + col) + (8 - row); // 'a'-'h' and 8-1
                        entries.push([uci, symbol]);
                    }
                }
            }

            // Separate and sort white and black
            const whiteEntries = entries
                .filter(([_, sym]) => sym === sym.toUpperCase())
                .sort(([a], [b]) => a[1] - b[1]); // pawns last

            const blackEntries = entries
                .filter(([_, sym]) => sym === sym.toLowerCase())
                .sort(([a], [b]) => b[1] - a[1]);

            // White pieces
            whiteEntries.forEach(([squareId, symbol], index) => {
                const square = document.getElementById(squareId);
                if (!square) return;

                const pieceName = "w_" + symbol.toLowerCase();
                const img = document.createElement("img");
                img.src = `/static/images/pieces_svg/${pieceName}.svg`;
                img.classList.add("piece", "piece-entry-white");
                img.style.animationDelay = `${index * 50}ms`;

                square.appendChild(img);

                img.addEventListener("animationend", () => {
                    img.style.opacity = "1";
                    img.classList.remove("piece-entry-white");
                });

                square.dataset.pieceColor = "w";
                square.dataset.pieceType = symbol.toLowerCase();
            });

            // Black pieces
            blackEntries.forEach(([squareId, symbol], index) => {
                const square = document.getElementById(squareId);
                if (!square) return;

                const pieceName = "b_" + symbol;
                const img = document.createElement("img");
                img.src = `/static/images/pieces_svg/${pieceName}.svg`;
                img.classList.add("piece", "piece-entry-black");
                img.style.animationDelay = `${index * 50}ms`;

                square.appendChild(img);

                img.addEventListener("animationend", () => {
                    img.style.opacity = "1";
                    img.classList.remove("piece-entry-black");
                });

                square.dataset.pieceColor = "b";
                square.dataset.pieceType = symbol;
            });
        })
        .catch(err => console.error("Failed to load board:", err));
}

function errorSquare(square) {
    selectedSquare?.classList.remove("selected");
    square.classList.add("error");

    setTimeout(() => {
        square.classList.remove("error");
    }, 500);
    selectedSquare = null;
}

function selectPiece(square) {
    color = square.dataset.pieceColor;

    if (gameMode === "pvp" && turn !== color) {
        return false;
    } else if ((gameMode.includes("ai") || gameMode === "lan") && playerColor !== color) {
        return false;
    }

    selectedSquare?.classList.remove("selected");
    selectedSquare = square;
    selectedSquare.classList.add("selected");

    return true;
}

function handleSquareClick(square) {
    if (selectPiece(square)) return;
    if (!selectedSquare) return;

    const from = selectedSquare.id;
    const to = square.id;
    const uci = from + to;

    selectedSquare.classList.remove("selected");
    selectedSquare = null;

    // Local PvP move
    if (gameMode === "pvp") {
        fetch("/move/local_player", {
            method: "POST",
            body: uci
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                movePiece(from, to);
                turn = turn === "w" ? "b" : "w";
            } else {
                errorSquare(square);
            }
        })
        .catch(err => console.error("Move request failed:", err));
    }

    // Player vs AI
    else if (gameMode.includes("ai") && playerColor === turn) {
        fetch("/move/ai_player", {
            method: "POST",
            body: uci
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                movePiece(from, to);
                turn = turn === "w" ? "b" : "w";

                // Wait until move animation finishes (300ms) before AI moves
                setTimeout(() => {
                    aiMove();
                }, 300);
            } else {
                errorSquare(square);
            }
        })
        .catch(err => console.error("Move request failed:", err));
    }

    // LAN mode (remote host)
    else if (gameMode == "lan" && playerColor === turn) {
        fetch(api("/move/lan_player"), {
            method: "POST",
            body: uci,
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                movePiece(from, to)
                turn = turn === "w" ? "b" : "w";
            } else {
                errorSquare(square);
            }
        })
        .catch(err => console.error("LAN move request failed", err));
    }
}

function movePiece(fromId, toId) {
    const fromSquare = document.getElementById(fromId);
    const toSquare = document.getElementById(toId);

    if (!fromSquare || !toSquare) {
        console.error("Invalid square IDs:", fromId, toId);
        return;
    }

    const piece = fromSquare.querySelector(".piece");

    if (!piece) {
        console.error("No piece found at square:", fromId);
        return;
    }

    const pieceColor = fromSquare.dataset.pieceColor;
    const pieceType = fromSquare.dataset.pieceType;

    // Handle captures
    const capturedPiece = toSquare.querySelector(".piece");
    if (capturedPiece) {
        capturedPiece.style.transition = "opacity 0.2s ease";
        capturedPiece.style.opacity = "0";
        setTimeout(() => {
            capturedPiece.remove();
        }, 200);
    }

    // Check for en passant capture
    if (pieceType === "p") {
        const fromFile = fromId.charCodeAt(0); // 'a' = 97
        const toFile = toId.charCodeAt(0);
        const fromRank = parseInt(fromId[1]);
        const toRank = parseInt(toId[1]);

        // If pawn moves diagonally but destination square is empty, it's en passant
        if (Math.abs(fromFile - toFile) === 1 && Math.abs(fromRank - toRank) === 1 && !capturedPiece) {
            // The captured pawn will be on the same file as the destination but on the same rank as the origin
            const enPassantSquareId = String.fromCharCode(toFile) + fromRank;
            const enPassantSquare = document.getElementById(enPassantSquareId);
            
            if (enPassantSquare) {
                const capturedEnPassantPiece = enPassantSquare.querySelector(".piece");
                if (capturedEnPassantPiece) {
                    capturedEnPassantPiece.style.transition = "opacity 0.2s ease";
                    capturedEnPassantPiece.style.opacity = "0";
                    setTimeout(() => {
                        capturedEnPassantPiece.remove();
                        enPassantSquare.dataset.pieceColor = "";
                        enPassantSquare.dataset.pieceType = "";
                    }, 200);
                }
            }
        }
    }

    // Animate the piece move
    const fromRect = fromSquare.getBoundingClientRect();
    const toRect = toSquare.getBoundingClientRect();

    const clone = piece.cloneNode(true);
    document.body.appendChild(clone);

    clone.style.position = "fixed";
    clone.style.zIndex = "1000";
    clone.style.width = `${fromRect.width * 0.8}px`;
    clone.style.height = `${fromRect.height * 0.8}px`;
    clone.style.top = `${fromRect.top + (fromRect.height - fromRect.height * 0.8) / 2}px`;
    clone.style.left = `${fromRect.left + (fromRect.width - fromRect.width * 0.8) / 2}px`;
    clone.style.transition = "top 0.3s ease, left 0.3s ease";
    clone.style.pointerEvents = "none";

    piece.style.opacity = "0";

    setTimeout(() => {
        clone.style.top = `${toRect.top + (toRect.height - toRect.height * 0.8) / 2}px`;
        clone.style.left = `${toRect.left + (toRect.width - toRect.width * 0.8) / 2}px`;
    }, 10);

    // Castling check
    const rookMoves = [];

    if (pieceType === "k") {
        const fromFile = fromId[0].charCodeAt(0); // 'e' = 101
        const toFile = toId[0].charCodeAt(0);

        // Kingside castling
        if (toFile - fromFile === 2) {
            const rookFrom = fromId[1] === "1" ? "h1" : "h8";
            const rookTo = fromId[1] === "1" ? "f1" : "f8";
            rookMoves.push([rookFrom, rookTo]);
        }
        // Queenside castling
        else if (toFile - fromFile === -2) {
            const rookFrom = fromId[1] === "1" ? "a1" : "a8";
            const rookTo = fromId[1] === "1" ? "d1" : "d8";
            rookMoves.push([rookFrom, rookTo]);
        }
    }

    setTimeout(() => {
        piece.remove();

        const newPiece = document.createElement("img");
        newPiece.src = piece.src;
        newPiece.classList.add("piece");
        newPiece.style.opacity = "1";

        toSquare.appendChild(newPiece);

        toSquare.dataset.pieceColor = pieceColor;
        toSquare.dataset.pieceType = pieceType;
        fromSquare.dataset.pieceColor = "";
        fromSquare.dataset.pieceType = "";

        clone.remove();

        // Now animate the rook if needed
        rookMoves.forEach(([rookFromId, rookToId]) => {
            const rookFrom = document.getElementById(rookFromId);
            const rookTo = document.getElementById(rookToId);

            if (!rookFrom || !rookTo) return;

            const rook = rookFrom.querySelector(".piece");
            if (!rook) return;

            const rookRectFrom = rookFrom.getBoundingClientRect();
            const rookRectTo = rookTo.getBoundingClientRect();

            const rookClone = rook.cloneNode(true);
            document.body.appendChild(rookClone);

            rookClone.style.position = "fixed";
            rookClone.style.zIndex = "1000";
            rookClone.style.width = `${rookRectFrom.width * 0.8}px`;
            rookClone.style.height = `${rookRectFrom.height * 0.8}px`;
            rookClone.style.top = `${rookRectFrom.top + (rookRectFrom.height - rookRectFrom.height * 0.8) / 2}px`;
            rookClone.style.left = `${rookRectFrom.left + (rookRectFrom.width - rookRectFrom.width * 0.8) / 2}px`;
            rookClone.style.transition = "top 0.3s ease, left 0.3s ease";
            rookClone.style.pointerEvents = "none";

            rook.style.opacity = "0";

            setTimeout(() => {
                rookClone.style.top = `${rookRectTo.top + (rookRectTo.height - rookRectTo.height * 0.8) / 2}px`;
                rookClone.style.left = `${rookRectTo.left + (rookRectTo.width - rookRectTo.width * 0.8) / 2}px`;
            }, 10);

            setTimeout(() => {
                rook.remove();

                const newRook = document.createElement("img");
                newRook.src = rook.src;
                newRook.classList.add("piece");
                newRook.style.opacity = "1";

                rookTo.appendChild(newRook);

                rookTo.dataset.pieceColor = pieceColor;
                rookTo.dataset.pieceType = "r";
                rookFrom.dataset.pieceColor = "";
                rookFrom.dataset.pieceType = "";

                rookClone.remove();
            }, 300);
        });

    }, 300);
}

function aiMove() {
    fetch("/move/ai_bot")
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const uci = data.uci;
            const aiFrom = uci.slice(0, 2);
            const aiTo = uci.slice(2, 4);
            movePiece(aiFrom, aiTo);
            turn = turn === "w" ? "b" : "w";
        }
    })
    .catch(err => console.error("AI move request failed:", err));
}