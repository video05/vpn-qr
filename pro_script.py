import requests
import json
import time
import socket
import qrcode
import re

URL1="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
URL2="https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt"
TG_URL="https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/tg-proxy/all.txt"

STATE_FILE="pro_state.json"


def get_configs(url):

    r=requests.get(url,timeout=20)

    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]


def parse_vless(link):

    link=link.replace("vless://","")

    uuid,rest=link.split("@")

    host_port=rest.split("?")[0]

    host=host_port.split(":")[0]

    port=int(host_port.split(":")[1])

    return host,port


def tcp_ping(host,port):

    try:

        start=time.time()

        sock=socket.create_connection((host,port),3)

        sock.close()

        return time.time()-start

    except:

        return None


def get_country(ip):

    try:

        r=requests.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode",timeout=5)

        data=r.json()

        return data.get("country","Unknown"),data.get("countryCode","")

    except:

        return "Unknown",""


def make_qr(cfg,i):

    img=qrcode.make(cfg)

    img.save(f"qr{i}.png")


configs1=get_configs(URL1)
configs2=get_configs(URL2)

servers=[]


# VPN 1-3
for cfg in configs1:

    if len(servers)>=3:
        break

    try:

        host,port=parse_vless(cfg)

        ping=tcp_ping(host,port)

        if not ping:
            continue

        country,code=get_country(host)

        servers.append({
            "config":cfg,
            "ping":ping,
            "country":country,
            "flag":code.lower(),
            "ip":host,
            "start":int(time.time())
        })

    except:
        pass


# VPN 4-6
for cfg in configs2:

    if len(servers)>=6:
        break

    try:

        host,port=parse_vless(cfg)

        ping=tcp_ping(host,port)

        if not ping:
            continue

        country,code=get_country(host)

        servers.append({
            "config":cfg,
            "ping":ping,
            "country":country,
            "flag":code.lower(),
            "ip":host,
            "start":int(time.time())
        })

    except:
        pass


for i,s in enumerate(servers,1):
    make_qr(s["config"],i)


# Telegram proxy parsing

tg=[]

try:

    r=requests.get(TG_URL,timeout=20)

    for line in r.text.splitlines():

        line=line.strip()

        if not line:
            continue

        # если уже готовая tg ссылка
        if line.startswith("tg://") or "t.me/proxy" in line:

            tg.append(line)

        # если формат server=IP&port=PORT&secret=SECRET
        elif "server=" in line and "port=" in line and "secret=" in line:

            tg.append("https://t.me/proxy?"+line)

        # если формат IP:PORT:SECRET
        else:

            parts=line.split(":")

            if len(parts)>=3:

                ip=parts[0]
                port=parts[1]
                secret=parts[2]

                tg.append(f"https://t.me/proxy?server={ip}&port={port}&secret={secret}")

        if len(tg)>=3:
            break

except:
    pass


with open(STATE_FILE,"w") as f:

    json.dump({
        "servers":servers,
        "tg":tg
    },f)
