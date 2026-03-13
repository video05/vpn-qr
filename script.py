import requests
import socket
import qrcode
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

def get_configs():
    r = requests.get(URL, timeout=10)
    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]

def check(cfg):
    try:
        p = urlparse(cfg)
        sock = socket.create_connection((p.hostname, p.port or 443), 2)
        sock.close()
        return cfg
    except:
        return None

configs = get_configs()

working = None

with ThreadPoolExecutor(max_workers=50) as ex:
    results = list(ex.map(check, configs))

for r in results:
    if r:
        working = r
        break

if working:
    img = qrcode.make(working)
    img.save("qr.png")

    with open("config.txt","w") as f:
        f.write(working)
