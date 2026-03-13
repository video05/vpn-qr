import requests
import socket
import qrcode
import json
import time
from urllib.parse import urlparse

URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

STATE_FILE = "pro_state.json"


def check(cfg):
    try:
        p = urlparse(cfg)
        sock = socket.create_connection((p.hostname, p.port or 443), 3)
        sock.close()
        return True
    except:
        return False


def get_configs():
    r = requests.get(URL, timeout=10)
    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"servers": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def make_qr(cfg, index):
    img = qrcode.make(cfg)
    img.save(f"qr{index}.png")


configs = get_configs()
state = load_state()

now = int(time.time())

# проверяем старые сервера
alive_servers = []

for s in state["servers"]:
    if check(s["config"]):
        alive_servers.append(s)

# если меньше 3 — ищем новые
for cfg in configs:
    if len(alive_servers) >= 3:
        break

    if any(cfg == s["config"] for s in alive_servers):
        continue

    if check(cfg):
        alive_servers.append({
            "config": cfg,
            "start": now
        })

# оставляем только 3
alive_servers = alive_servers[:3]

# сохраняем QR
for i, s in enumerate(alive_servers, start=1):
    make_qr(s["config"], i)

state["servers"] = alive_servers
save_state(state)
