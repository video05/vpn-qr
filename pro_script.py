import requests
import json
import time
import socket
import qrcode
import os

URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

STATE_FILE = "pro_state.json"


def get_configs():
    r = requests.get(URL, timeout=20)
    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]


def parse_vless(link):

    link = link.replace("vless://","")

    uuid, rest = link.split("@")

    host_port = rest.split("?")[0]

    host = host_port.split(":")[0]

    port = int(host_port.split(":")[1])

    return host, port


def tcp_ping(host,port):

    try:

        start=time.time()

        sock=socket.create_connection((host,port),3)

        sock.close()

        latency=time.time()-start

        return latency

    except:

        return None


def get_country(ip):

    try:

        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=5)

        data = r.json()

        if "country" in data:
            return data["country"]

    except:
        pass

    return "Unknown"

    try:

        r=requests.get(f"https://ipapi.co/{ip}/country_name/",timeout=5)

        return r.text.strip()

    except:

        return "Unknown"


def make_qr(cfg,i):

    img=qrcode.make(cfg)

    img.save(f"qr{i}.png")


configs=get_configs()

servers=[]

for cfg in configs:

    if len(servers)>=3:

        break

    try:

        host,port=parse_vless(cfg)

        latency=tcp_ping(host,port)

        if latency:

            servers.append({

                "config":cfg,

                "ping":latency,

                "country":get_country(host),

                "ip":host,

                "start":int(time.time())

            })

    except:

        pass


for i,s in enumerate(servers,1):

    make_qr(s["config"],i)


with open(STATE_FILE,"w") as f:

    json.dump({"servers":servers},f)
