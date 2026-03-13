import requests
import json
import time
import socket
import qrcode

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


# первые 3 VPN

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


# ещё 3 VPN

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


# telegram proxy

tg_list=[]

try:

    r=requests.get(TG_URL,timeout=20)

    lines=r.text.split("\n")

    for line in lines:

        if "tg://proxy" in line:

            tg_list.append(line.strip())

        if len(tg_list)>=3:
            break

except:

    pass


with open(STATE_FILE,"w") as f:

    json.dump({

        "servers":servers,

        "tg":tg_list

    },f)
