import socket
from flask import request, jsonify
from functools import wraps
from app import state


# Get your local machine IP at startup
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to connect - just triggers IP resolution logic
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


LOCAL_IP = socket.gethostbyname(socket.gethostname())


def requires_mode(*modes):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if state.active_mode not in modes:
                return jsonify({"error": "Invalid game mode"}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def local_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        if ip != "127.0.0.1" and ip != LOCAL_IP:
            return jsonify({"error": f"Local access only (from {ip})"}), 403
        return f(*args, **kwargs)

    return wrapper


def requires_lan_player():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if state.active_mode != "lan":
                return jsonify({"error": "LAN not active"}), 403

            game = state.game_states["lan"]
            token = (
                request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            )
            ip = request.remote_addr
            current = game["current_turn"]

            expected_token = game.get(f"{current}_token")
            expected_ip = game.get(f"{current}_ip")

            if token != expected_token or ip != expected_ip:
                return jsonify({"error": "Unauthorized LAN access"}), 403

            return f(*args, **kwargs)

        return wrapper

    return decorator
