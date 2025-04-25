let turn = null;
let selectedSquare = null;
let gameOver = false;
let pendingPromotion = null;
const params = new URLSearchParams(window.location.search);
const gameMode = params.get("mode");
const playerColor = params.get("color") || null; // 'white', 'black', or null
let hasHumanMoved = false;
const INITIAL_POSITION = {
    a1: "w_r", b1: "w_n", c1: "w_b", d1: "w_q", e1: "w_k", f1: "w_b", g1: "w_n", h1: "w_r",
    a2: "w_p", b2: "w_p", c2: "w_p", d2: "w_p", e2: "w_p", f2: "w_p", g2: "w_p", h2: "w_p",
    a7: "b_p", b7: "b_p", c7: "b_p", d7: "b_p", e7: "b_p", f7: "b_p", g7: "b_p", h7: "b_p",
    a8: "b_r", b8: "b_n", c8: "b_b", d8: "b_q", e8: "b_k", f8: "b_b", g8: "b_n", h8: "b_r"
};

document.addEventListener("DOMContentLoaded", () => {
    const boardContainer = document.querySelector(".chessboard-container");
    const board = document.getElementById("chessboard");
    window.undoButton = document.getElementById("undo-btn");
    const isAiGame = gameMode === "ai";

    if (board) {
        // Render initial board position
        if (isAiGame && playerColor === "b") {
            boardContainer.classList.add("rotated");

            setTimeout(() => {
                renderInitialPosition().then(updateStats);
            }, 1000);
        } else {
            renderInitialPosition().then(updateStats);
        }

        // Initialize turn
        fetch("/get/turn")
            .then(res => res.json())
            .then(data => {
                if (data.turn) {
                    turn = data.turn;
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

function resetBoard() {
    fetch("/reset", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                selectedSquare?.classList.remove("selected");
                selectedSquare = null;
                clearBoard();
                renderInitialPosition();
                updateStats();

                // Close promotion selection if open
                const promotionContainer = document.querySelector('.promotion-container');
                promotionContainer.classList.add('hidden');
                pendingPromotion = null;

                // Reinitialize turn after reset
                fetch("/get/turn")
                    .then(res => res.json())
                    .then(data => {
                        if (data.turn) {
                            turn = data.turn;

                            // If AI plays white and it's white's turn after reset, move
                            if (gameMode === "ai" && playerColor === "b" && turn === "w") {
                                setTimeout(() => {
                                    aiMove();
                                }, 1000);
                            }
                        }
                    });
            } else {
                console.error("Reset failed:", data.error);
            }
        })
        .catch(err => console.error("Reset request failed:", err));
}

function clearBoard() {
    document.querySelectorAll(".square").forEach(square => {
        const piece = square.querySelector(".piece");
        if (piece) {
            piece.remove();
        }
        square.dataset.pieceColor = "";
        square.dataset.pieceType = "";
    });
}

function updateStats() {
    fetch("/get/stats")
        .then(res => res.json())
        .then(data => {
            const activeColor = data.active_color;
            const castlingRights = data.castling;
            const enPassant = data.en_passant;
            const halfmove = data.halfmove_clock;
            const fullmove = data.fullmove_count;
            const ply = data.ply;

            // Turn
            document.getElementById("stat-turn").textContent = activeColor === "w" ? "White" : "Black";

            // Castling
            const wk = castlingRights.includes("K");
            const wq = castlingRights.includes("Q");
            const bk = castlingRights.includes("k");
            const bq = castlingRights.includes("q");

            document.getElementById("stat-wk").textContent = "K" + (wk ? "✓" : "✗");
            document.getElementById("stat-wq").textContent = "Q" + (wq ? "✓" : "✗");
            document.getElementById("stat-bk").textContent = "K" + (bk ? "✓" : "✗");
            document.getElementById("stat-bq").textContent = "Q" + (bq ? "✓" : "✗");

            // En Passant
            document.getElementById("stat-ep").textContent = enPassant;

            // Halfmove & Fullmove
            document.getElementById("stat-halfmove").textContent = halfmove;
            document.getElementById("stat-fullmove").textContent = fullmove;

            // Ply
            document.getElementById("stat-ply").textContent = ply;

            // Show end game status
            gameOver = data.checkmate || data.draw
            showGameEnd(data.checkmate, data.draw, data.winner);

            // Clear any old "checked" highlight
            document.querySelectorAll(".square.checked").forEach(sq => sq.classList.remove("checked"));

            // Highlight king's square if side to move is in check
            if (data.in_check) {
                const selector = `.square[data-piece-color="${activeColor}"][data-piece-type="k"]`;
                const kingSquare = document.querySelector(selector);
                if (kingSquare) kingSquare.classList.add("checked");
            }

            // Recompute whether the player has moved already
            if (gameMode === "ai") {
                if (playerColor === "w") {
                    hasHumanMoved = data.ply >= 1;
                } else {
                    hasHumanMoved = data.ply >= 2;
                }
                window.undoButton.disabled = !hasHumanMoved;

                if (hasHumanMoved) {
                    window.undoButton.classList.remove("disabled");
                } else {
                    window.undoButton.classList.add("disabled");
                }
            } else if (gameMode === "pvp") {
                hasHumanMoved = data.ply >= 1;
                window.undoButton.disabled = !hasHumanMoved;

                if (hasHumanMoved) {
                    window.undoButton.classList.remove("disabled");
                } else {
                    window.undoButton.classList.add("disabled");
                }
            }
        })
        .catch(err => console.error("Failed to load FEN stats:", err));
}

function showGameEnd(checkmate, draw, winner) {
    const banner = document.getElementById("game-end-banner");
    if (!banner) return;

    if (checkmate) {
        banner.textContent = `Checkmate: ${winner === "w" ? "White" : "Black"} won`;
    } else if (draw) {
        banner.textContent = "Draw";
    }

    if (checkmate || draw) {
        banner.classList.remove("hidden");
    } else {
        banner.classList.add("hidden");
    }
}

function toggleStatsSidebar() {
    const sidebar = document.getElementById("stats-sidebar");
    sidebar.classList.toggle("hidden");
}


function renderInitialPosition() {
    return fetch("/get/board")
        .then(res => res.json())
        .then(data => {
            const board = data.board;

            // Clear existing pieces first
            document.querySelectorAll(".square").forEach(square => {
                const piece = square.querySelector(".piece");
                if (piece) piece.remove();
                square.dataset.pieceColor = "";
                square.dataset.pieceType = "";
            });

            const entries = [];

            for (let row = 0; row < 8; row++) {
                for (let col = 0; col < 8; col++) {
                    const symbol = board[row][col];
                    if (symbol) {
                        const uci = String.fromCharCode(97 + col) + (8 - row);
                        entries.push([uci, symbol]);
                    }
                }
            }

            const whiteEntries = entries
                .filter(([_, sym]) => sym === sym.toUpperCase())
                .sort(([a], [b]) => a[1] - b[1]);

            const blackEntries = entries
                .filter(([_, sym]) => sym === sym.toLowerCase())
                .sort(([a], [b]) => b[1] - a[1]);

            whiteEntries.forEach(([squareId, symbol], index) => {
                const square = document.getElementById(squareId);
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

            blackEntries.forEach(([squareId, symbol], index) => {
                const square = document.getElementById(squareId);
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
    if (gameOver) return;

    color = square.dataset.pieceColor;

    if (gameMode === "pvp" && turn !== color) {
        return false;
    } else if (gameMode === "ai" && playerColor !== color) {
        return false;
    }

    selectedSquare?.classList.remove("selected");
    selectedSquare = square;
    selectedSquare.classList.add("selected");

    return true;
}

function handleSquareClick(square) {
    if (gameOver || pendingPromotion) return;

    if (selectPiece(square)) return;
    if (!selectedSquare) return;

    const from = selectedSquare.id;
    const to = square.id;
    const uci = from + to;

    selectedSquare.classList.remove("selected");
    selectedSquare = null;

    const fromRank = parseInt(from[1]);
    const toRank = parseInt(to[1]);
    const pieceType = document.getElementById(from).dataset.pieceType;
    const pieceColor = document.getElementById(from).dataset.pieceColor;

    const isWhitePromo = pieceType === "p" && pieceColor === "w" && fromRank === 7 && toRank === 8;
    const isBlackPromo = pieceType === "p" && pieceColor === "b" && fromRank === 2 && toRank === 1;

    if (isWhitePromo || isBlackPromo) {
        fetch(`/can_move/${from}/${to}`)
            .then(res => res.json())
            .then(data => {
                if (data.can_move) {
                    pendingPromotion = { from, to };
                    showPromotionOptions();
                } else {
                    errorSquare(square);
                }
            })
            .catch(err => {
                console.error("Promotion legality check failed:", err);
            });
        return;
    }

    sendMove(uci, from, to, null);
}

function sendMove(uci, from, to, promotion) {
    const fullUci = promotion ? uci + promotion : uci;

    const url = gameMode === "pvp" ? "/move/local_player" : "/move/ai_player";

    fetch(url, {
        method: "POST",
        body: fullUci
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            movePiece(from, to, promotion);
            turn = turn === "w" ? "b" : "w";
            updateStats();

            if (gameMode === "ai" && playerColor !== turn) {
                setTimeout(aiMove, 300);
            }
        } else {
            errorSquare(document.getElementById(to));
        }
    })
    .catch(err => console.error("Move request failed:", err));
}

function showPromotionOptions() {
    if (gameOver) return;

    const container = document.querySelector('.promotion-container');
    container.classList.remove('hidden');

    const pieceMap = {
        'promotion-select-queen':  'q',
        'promotion-select-rook':   'r',
        'promotion-select-bishop': 'b',
        'promotion-select-knight': 'n'
    };

    const buttons = container.querySelectorAll('button[id^="promotion-select-"]');
    buttons.forEach(btn => {
        // Clear out any old handler
        btn.onclick = null;

        // Assign the new one
        btn.onclick = () => {
            const promotion = pieceMap[btn.id];
            const { from, to } = pendingPromotion;
            container.classList.add('hidden');
            pendingPromotion = null;
            sendMove(from + to, from, to, promotion);
        };
    });
}

function movePiece(fromId, toId, promotion = null) {
    if (gameOver) return;

    lastMoveMade = [fromId, toId];
    const fromSquare = document.getElementById(fromId);
    const toSquare = document.getElementById(toId);
    if (!fromSquare || !toSquare) {
        console.error('Invalid square IDs:', fromId, toId);
        return;
    }

    const piece = fromSquare.querySelector('.piece');
    if (!piece) {
        console.error('No piece found at square:', fromId);
        return;
    }

    // Figure out what piece to end up with
    const pieceColor = fromSquare.dataset.pieceColor;
    const originalType = fromSquare.dataset.pieceType;
    const newType = promotion || originalType;
    const fileName = `${pieceColor}_${newType}`;

    // Handle captures
    const captured = toSquare.querySelector('.piece');
    if (captured) {
        captured.style.transition = 'opacity 0.2s ease';
        captured.style.opacity = '0';
        setTimeout(() => captured.remove(), 200);
    }

    // Handle en passant capture
    if (originalType === 'p') {
        const fromFile = fromId.charCodeAt(0);
        const toFile = toId.charCodeAt(0);
        const fromRank = parseInt(fromId[1], 10);
        const toRank = parseInt(toId[1], 10);
        if (Math.abs(fromFile - toFile) === 1 &&
            Math.abs(fromRank - toRank) === 1 &&
            !captured) {
            const epId = String.fromCharCode(toFile) + fromRank;
            const epSq = document.getElementById(epId);
            if (epSq) {
                const epCap = epSq.querySelector('.piece');
                if (epCap) {
                    epCap.style.transition = 'opacity 0.2s ease';
                    epCap.style.opacity = '0';
                    setTimeout(() => {
                        epCap.remove();
                        epSq.dataset.pieceColor = '';
                        epSq.dataset.pieceType = '';
                    }, 200);
                }
            }
        }
    }

    // Prepare for castling rook moves
    const rookMoves = [];
    if (originalType === 'k') {
        const fromFile = fromId.charCodeAt(0);
        const toFile = toId.charCodeAt(0);
        // kingside
        if (toFile - fromFile === 2) {
            const rookFrom = fromId[1] === '1' ? 'h1' : 'h8';
            const rookTo   = fromId[1] === '1' ? 'f1' : 'f8';
            rookMoves.push([rookFrom, rookTo]);
        }
        // queenside
        if (toFile - fromFile === -2) {
            const rookFrom = fromId[1] === '1' ? 'a1' : 'a8';
            const rookTo   = fromId[1] === '1' ? 'd1' : 'd8';
            rookMoves.push([rookFrom, rookTo]);
        }
    }

    // Animate the move
    const fromRect = fromSquare.getBoundingClientRect();
    const toRect   = toSquare.getBoundingClientRect();
    const clone    = piece.cloneNode(true);
    document.body.appendChild(clone);
    clone.style.position = 'fixed';
    clone.style.zIndex   = '1000';
    clone.style.width    = `${fromRect.width * 0.8}px`;
    clone.style.height   = `${fromRect.height * 0.8}px`;
    clone.style.top      = `${fromRect.top + (fromRect.height - fromRect.height * 0.8) / 2}px`;
    clone.style.left     = `${fromRect.left + (fromRect.width  - fromRect.width  * 0.8) / 2}px`;
    clone.style.transition = 'top 0.3s ease, left 0.3s ease';
    clone.style.pointerEvents = 'none';

    piece.style.opacity = '0';

    // Kick off the CSS transition
    setTimeout(() => {
        clone.style.top  = `${toRect.top  + (toRect.height  - toRect.height  * 0.8) / 2}px`;
        clone.style.left = `${toRect.left + (toRect.width   - toRect.width   * 0.8) / 2}px`;
    }, 10);

    // Once animation is done, swap in the new piece
    setTimeout(() => {
        piece.remove();

        const newPiece = document.createElement('img');
        newPiece.src         = `/static/images/pieces_svg/${fileName}.svg`;
        newPiece.classList.add('piece');
        newPiece.style.opacity = '1';
        toSquare.appendChild(newPiece);

        // Update data attributes
        toSquare.dataset.pieceColor = pieceColor;
        toSquare.dataset.pieceType  = newType;
        fromSquare.dataset.pieceColor = '';
        fromSquare.dataset.pieceType  = '';

        clone.remove();

        // Handle rook in castling
        rookMoves.forEach(([rFrom, rTo]) => {
            const rf = document.getElementById(rFrom);
            const rt = document.getElementById(rTo);
            if (!rf || !rt) return;

            const rook = rf.querySelector('.piece');
            if (!rook) return;

            const rfRect = rf.getBoundingClientRect();
            const rtRect = rt.getBoundingClientRect();
            const rClone = rook.cloneNode(true);
            document.body.appendChild(rClone);
            rClone.style.position = 'fixed';
            rClone.style.zIndex   = '1000';
            rClone.style.width    = `${rfRect.width * 0.8}px`;
            rClone.style.height   = `${rfRect.height * 0.8}px`;
            rClone.style.top      = `${rfRect.top + (rfRect.height - rfRect.height * 0.8) / 2}px`;
            rClone.style.left     = `${rfRect.left + (rfRect.width - rfRect.width * 0.8) / 2}px`;
            rClone.style.transition = 'top 0.3s ease, left 0.3s ease';
            rClone.style.pointerEvents = 'none';

            rook.style.opacity = '0';

            setTimeout(() => {
                rClone.style.top  = `${rtRect.top  + (rtRect.height  - rtRect.height  * 0.8) / 2}px`;
                rClone.style.left = `${rtRect.left + (rtRect.width   - rtRect.width   * 0.8) / 2}px`;
            }, 10);

            setTimeout(() => {
                rook.remove();
                const newRook = document.createElement('img');
                newRook.src         = rook.src;
                newRook.classList.add('piece');
                newRook.style.opacity = '1';
                rt.appendChild(newRook);

                rt.dataset.pieceColor = pieceColor;
                rt.dataset.pieceType  = 'r';
                rf.dataset.pieceColor = '';
                rf.dataset.pieceType  = '';
                rClone.remove();
            }, 300);
        });

    }, 300);
}

function aiMove() {
    if (gameOver) return;

    fetch("/move/ai_bot")
    .then(res => res.json())
    .then(data => {
        if (!data.success) return console.error("AI move failed");

        const uci = data.uci;           // e.g. "e7e8q"  
        const aiFrom = uci.slice(0, 2); // "e7"  
        const aiTo   = uci.slice(2, 4); // "e8"  
        // if there's a 5th character, it's the promotion piece:
        const aiPromo = uci.length === 5 ? uci[4] : null;  

        // directly movePiece; no prompts ever for the AI
        movePiece(aiFrom, aiTo, aiPromo);

        // flip turn & stats
        turn = turn === "w" ? "b" : "w";
        updateStats();
    })
    .catch(err => console.error("AI move request failed:", err));
}


function undoMove() {
    // Ensure promotion container is closed
    const promotionContainer = document.querySelector('.promotion-container');
    promotionContainer.classList.add('hidden');
    pendingPromotion = null;

    // If player is black vs AI and hasn't moved, do nothing
    if (gameMode === "ai" && playerColor === "b" && !hasHumanMoved) return;

    const undoOnce = () => fetch("/undo", { method: "POST" }).then(res => res.json());

    if (gameMode === "ai") {
        // Undo twice: player move + AI move
        undoOnce()
            .then(data1 => {
                if (!data1.success) throw new Error(data1.error || "Undo 1 failed");
                return undoOnce();
            })
            .then(data2 => {
                if (!data2.success) throw new Error(data2.error || "Undo 2 failed");
                afterUndoRefresh();
            })
            .catch(err => console.error("AI Undo error:", err));
    } else {
        // PvP: just undo once
        undoOnce()
            .then(data => {
                if (!data.success) {
                    console.error("Undo failed:", data.error || data);
                    return;
                }
                afterUndoRefresh();
            })
            .catch(err => console.error("Undo request failed:", err));
    }
}

function afterUndoRefresh() {
    clearBoard();
    renderInitialPosition();
    updateStats();
    gameOver = false;

    fetch("/get/turn")
        .then(res => res.json())
        .then(data => {
            if (!data.turn) {
                console.error("Turn fetch error:", data.error);
                return;
            }
            turn = data.turn;

            // Let AI move only if it's its turn now
            if (gameMode === "ai" && playerColor !== turn) {
                setTimeout(() => aiMove(), 1000);
            }
        });
}
