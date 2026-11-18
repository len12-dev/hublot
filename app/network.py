"""Gestion réseau via NetworkManager (nmcli)."""
import subprocess

AP_CONNECTION = "hublot-ap"
AP_SSID = "Hublot-Setup"


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(["nmcli", *args], capture_output=True, text=True, timeout=30)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def connection_status() -> dict:
    """Retourne le mode actuel, le SSID et l'adresse IP."""
    _, out = _run(["-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"])
    active = [line.split(":") for line in out.splitlines() if line]
    mode = "none"
    ssid = None
    for name, ctype, _device in (a[:3] for a in active if len(a) >= 3):
        if name == AP_CONNECTION:
            mode = "ap"
        elif ctype == "802-11-wireless":
            mode, ssid = "wifi", name
        elif ctype == "802-3-ethernet":
            mode = "ethernet" if mode == "none" else mode
    _, ip_out = _run(["-t", "-f", "IP4.ADDRESS", "device", "show"])
    ip = next((l.split(":", 1)[1].split("/")[0] for l in ip_out.splitlines()
               if l.startswith("IP4.ADDRESS") and not l.endswith("127.0.0.1/8")), None)
    return {"mode": mode, "ssid": ssid, "ip": ip}


def scan_wifi() -> list[dict]:
    _run(["device", "wifi", "rescan"])
    _, out = _run(["-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
    seen, networks = set(), []
    for line in out.splitlines():
        parts = line.rsplit(":", 2)
        if len(parts) != 3 or not parts[0] or parts[0] in seen:
            continue
        seen.add(parts[0])
        networks.append({"ssid": parts[0], "signal": int(parts[1] or 0), "security": parts[2]})
    return sorted(networks, key=lambda n: n["signal"], reverse=True)


def connect_wifi(ssid: str, password: str) -> tuple[bool, str]:
    args = ["device", "wifi", "connect", ssid]
    if password:
        args += ["password", password]
    code, out = _run(args)
    return code == 0, out


def start_access_point(password: str) -> tuple[bool, str]:
    """Crée le point d'accès de secours (utilisé quand aucun réseau n'est joignable)."""
    _run(["connection", "delete", AP_CONNECTION])
    code, out = _run([
        "device", "wifi", "hotspot", "ifname", "wlan0",
        "con-name", AP_CONNECTION, "ssid", AP_SSID, "password", password,
    ])
    return code == 0, out
