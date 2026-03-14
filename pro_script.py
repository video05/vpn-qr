import requests
import json
import time
import socket
import qrcode

URL1="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
URL2="https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt"

STATE_FILE="pro_state.json"

MAX_CHECK=200
MAX_SERVERS=20


def get_configs(url):

    try:
        r=requests.get(url,timeout=20)
        return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]
    except:
        return []


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

        ping=time.time()-start

        if ping>5:
            return None

        return ping

    except:

        return None


def get_country(ip):

    try:

        r=requests.get(
            f"http://ip-api.com/json/{ip}?fields=country,countryCode",
            timeout=4
        )

        data=r.json()

        return data.get("country","Unknown"),data.get("countryCode","")

    except:

        return "Unknown",""


def make_qr(cfg,i):

    img=qrcode.make(cfg)

    img.save(f"qr{i}.png")


configs1=get_configs(URL1)
configs2=get_configs(URL2)

configs=configs1+configs2

configs=configs[:MAX_CHECK]


servers=[]


for cfg in configs:

    try:

        host,port=parse_vless(cfg)

        ping=tcp_ping(host,port)

        if ping is None:
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


servers=sorted(servers,key=lambda x:x["ping"])


servers=servers[:MAX_SERVERS]


for i,s in enumerate(servers,1):

    make_qr(s["config"],i)


update_time=int(time.time())


with open(STATE_FILE,"w") as f:

    json.dump({
        "servers":servers,
        "updated":update_time
    },f)
