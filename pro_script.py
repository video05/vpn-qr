import requests
import json
import time
import socket
import ssl
import qrcode
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def tcp_check(host,port):

    try:
        sock=socket.create_connection((host,port),2)
        sock.close()
        return True
    except:
        return False


def tls_check(host,port):

    try:
        ctx=ssl.create_default_context()
        sock=socket.create_connection((host,port),2)
        ssock=ctx.wrap_socket(sock,server_hostname=host)
        ssock.close()
        return True
    except:
        return False


def v2_check(host,port):

    try:

        ctx=ssl.create_default_context()

        sock=socket.create_connection((host,port),3)

        ssock=ctx.wrap_socket(sock,server_hostname=host)

        ssock.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

        data=ssock.recv(100)

        ssock.close()

        if data:
            return True

    except:
        pass

    return False


def measure_ping(host,port):

    try:
        start=time.time()
        sock=socket.create_connection((host,port),2)
        sock.close()
        return time.time()-start
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


def check_server(cfg):

    try:

        host,port=parse_vless(cfg)

        if not tcp_check(host,port):
            return None

        if not tls_check(host,port):
            return None

        if not v2_check(host,port):
            return None

        ping=measure_ping(host,port)

        if ping is None:
            return None

        country,code=get_country(host)

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


configs1=get_configs(URL1)[:25]
configs2=get_configs(URL2)[:25]

configs=configs1+configs2


servers=[]


with ThreadPoolExecutor(max_workers=25) as executor:

    futures=[executor.submit(check_server,cfg) for cfg in configs]

    for future in as_completed(futures):

        result=future.result()

        if result:
            servers.append(result)


if len(servers)<6:

    extra=configs1[25:50]+configs2[25:50]

    with ThreadPoolExecutor(max_workers=25) as executor:

        futures=[executor.submit(check_server,cfg) for cfg in extra]

        for future in as_completed(futures):

            result=future.result()

            if result:
                servers.append(result)


servers=sorted(servers,key=lambda x:x["ping"])


servers=servers[:6]


for i,s in enumerate(servers,1):

    make_qr(s["config"],i)


with open(STATE_FILE,"w") as f:

    json.dump({"servers":servers},f)
