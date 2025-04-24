from __future__ import annotations
from bitboarder import Board
from app.ai import ChessCNN
import socket
import threading
import time

BROADCAST_PORT = 54545
BROADCAST_INTERVAL = 2  # seconds

active_mode = None
active_lan_game: LANGame = None
_broadcast_thread = None
discovered_lan_games = {}  # game_id -> {"ip": ..., "port": ..., "game_id": ...}


def broadcast_game(game_id, server_ip, port=5000):
    global _broadcast_thread

    msg = f"chess_game:{server_ip}:{port}:{game_id}".encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def loop():
        while active_lan_game and active_lan_game.game_id == game_id:
            try:
                s.sendto(msg, ("<broadcast>", BROADCAST_PORT))
                time.sleep(BROADCAST_INTERVAL)
            except Exception as e:
                print("Broadcast error:", e)
                break

    _broadcast_thread = threading.Thread(target=loop, daemon=True)
    _broadcast_thread.start()


def listen_for_games():
    def loop():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", BROADCAST_PORT))

        while True:
            try:
                data, _ = s.recvfrom(1024)
                msg = data.decode()

                if msg.startswith("chess_game"):
                    parts = msg.strip().split(":")
                    if len(parts) == 4:
                        _, ip, port, game_id = parts

                        # Remove all previous games from this IP
                        to_delete = [
                            gid
                            for gid, g in discovered_lan_games.items()
                            if g["ip"] == ip
                        ]
                        for gid in to_delete:
                            del discovered_lan_games[gid]

                        # Register the new game
                        discovered_lan_games[game_id] = {
                            "ip": ip,
                            "port": int(port),
                            "game_id": game_id,
                        }

            except Exception as e:
                print("Listener error:", e)

    threading.Thread(target=loop, daemon=True).start()


class PvPGame:
    def __init__(self):
        self.board = Board()


class AIGame:
    def __init__(self):
        self.board = Board()
        self.ai = ChessCNN(self.board, "cpu")


class LANGame:
    def __init__(self, game_id):
        self.board = Board()
        self.game_id = game_id
        self.white_token = None
        self.black_token = None
        self.white_ip = None
        self.black_ip = None
        self.joined_clients = {}


game_states = {
    "pvp": PvPGame(),
    "ai_w": AIGame(),
    "ai_b": AIGame(),
}
