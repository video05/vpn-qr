import requests
import json
import time
import socket
import ssl
import qrcode

URL1="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
URL2="https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt"

STATE_FILE="pro_state.json"


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


def check_server(cfg):

    try:

        host,port=parse_vless(cfg)

        start=time.time()

        ctx=ssl.create_default_context()

        sock=socket.create_connection((host,port),3)

        ssock=ctx.wrap_socket(sock,server_hostname=host)

        ssock.close()

        ping=time.time()-start

        if ping>3:
            return None

        country="Unknown"
        code=""

        try:
            r=requests.get(
                f"http://ip-api.com/json/{host}?fields=country,countryCode",
                timeout=5
            )

            d=r.json()

            country=d.get("country","Unknown")
            code=d.get("countryCode","")

        except:
            pass

        return {

            "config":cfg,
            "ping":ping,
            "country":country,
            "flag":code.lower(),
            "ip":host,
            "start":int(time.time())

        }

    except:

        return None


def make_qr(cfg,i):

    img=qrcode.make(cfg)
    img.save(f"qr{i}.png")


configs1=get_configs(URL1)[:25]
configs2=get_configs(URL2)[:25]

configs=configs1+configs2


servers=[]


for cfg in configs:

    result=check_server(cfg)

    if result:

        servers.append(result)

        # сортируем каждый раз чтобы быстрые были сверху
        servers=sorted(servers,key=lambda x:x["ping"])

        # держим только 6 лучших
        servers=servers[:6]


# если серверов меньше 6 — проверяем ещё
if len(servers)<6:

    extra=configs1[25:80]+configs2[25:80]

    for cfg in extra:

        result=check_server(cfg)

        if result:

            servers.append(result)

            servers=sorted(servers,key=lambda x:x["ping"])

            servers=servers[:6]


# генерация QR

for i,s in enumerate(servers,1):

    make_qr(s["config"],i)


with open(STATE_FILE,"w") as f:

    json.dump({"servers":servers},f)
