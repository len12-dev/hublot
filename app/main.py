"""Serveur web de l'Hublot (Flask)."""
import functools
import hashlib
import hmac
import json
import os
import secrets
import subprocess
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

from network import connection_status, scan_wifi, connect_wifi

CONFIG_PATH = Path(os.environ.get("HUBLOT_CONFIG", "/etc/hublot/config.json"))
SOLOIST_ENV = Path(os.environ.get("HUBLOT_SOLOIST_ENV", "/etc/hublot/soloist.env"))

app = Flask(__name__)
app.secret_key = os.environ.get("HUBLOT_SECRET", secrets.token_hex(32))


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"friendly_name": "Mon enceinte", "pin_hash": None, "pin_salt": None}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 200_000).hex()


def check_pin(pin: str) -> bool:
    cfg = load_config()
    if not cfg.get("pin_hash"):
        return False
    return hmac.compare_digest(hash_pin(pin, cfg["pin_salt"]), cfg["pin_hash"])


# --- Soloist -----------------------------------------------------------------

def read_soloist_env() -> dict:
    if not SOLOIST_ENV.exists():
        return {}
    values = {}
    for line in SOLOIST_ENV.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            values[k] = v.strip().strip('"')
    return values


def write_soloist_env(name: str, key: str) -> None:
    # Pas de guillemets ni d'antislashs dans le nom : évite les erreurs de parsing systemd
    safe_name = name.replace('"', "").replace("\\", "")
    SOLOIST_ENV.parent.mkdir(parents=True, exist_ok=True)
    SOLOIST_ENV.write_text(f'SOLOIST_NAME="{safe_name}"\nSOLOIST_KEY={key}\n')
    os.chmod(SOLOIST_ENV, 0o600)


def soloist_restart() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "enable", "soloist"], check=False)
    subprocess.run(["systemctl", "restart", "soloist"], check=False)


def soloist_state() -> str:
    proc = subprocess.run(["systemctl", "is-active", "soloist"], capture_output=True, text=True)
    return proc.stdout.strip() or "inconnu"


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("auth"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if check_pin(request.form.get("pin", "")):
            session["auth"] = True
            return redirect(url_for("index"))
        error = "PIN incorrect"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html", config=load_config())


@app.route("/api/status")
@login_required
def api_status():
    return jsonify({
        "config": load_config(),
        "network": connection_status(),
        "soloist": soloist_state(),
        "soloist_key_set": bool(read_soloist_env().get("SOLOIST_KEY")),
    })


@app.route("/api/wifi/scan")
@login_required
def api_scan():
    return jsonify({"networks": scan_wifi()})


@app.route("/api/wifi/connect", methods=["POST"])
@login_required
def api_connect():
    data = request.get_json(force=True)
    ssid = data.get("ssid", "")
    password = data.get("password", "")
    if not ssid:
        abort(400)
    ok, message = connect_wifi(ssid, password)
    return jsonify({"ok": ok, "message": message}), (200 if ok else 500)


@app.route("/api/system", methods=["POST"])
@login_required
def api_system():
    data = request.get_json(force=True)
    cfg = load_config()
    name_changed = False
    if "friendly_name" in data:
        new_name = str(data["friendly_name"])[:64]
        name_changed = new_name != cfg.get("friendly_name")
        cfg["friendly_name"] = new_name
    if "new_pin" in data and data["new_pin"]:
        pin = str(data["new_pin"])
        if not (4 <= len(pin) <= 8 and pin.isdigit()):
            abort(400)
        salt = secrets.token_hex(16)
        cfg["pin_salt"] = salt
        cfg["pin_hash"] = hash_pin(pin, salt)
    save_config(cfg)

    # Clé API Soloist : stockée uniquement dans /etc/hublot/soloist.env
    key = str(data.get("soloist_api_key", "")).strip()
    current = read_soloist_env()
    if key or (name_changed and current.get("SOLOIST_KEY")):
        final_key = key or current.get("SOLOIST_KEY", "")
        if key and (len(key) < 10 or any(c.isspace() for c in key)):
            abort(400)
        write_soloist_env(cfg["friendly_name"], final_key)
        soloist_restart()
    return jsonify({"ok": True, "soloist": soloist_state()})


if __name__ == "__main__":
    # Développement uniquement ; en production, lancé par systemd via gunicorn.
    app.run(host="0.0.0.0", port=80)
