import requests
import json
import time
import socket
import subprocess
import qrcode

URL="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

STATE_FILE="pro_state.json"

MAX_SERVERS=80


def get_configs():
    r=requests.get(URL,timeout=20)
    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")][:MAX_SERVERS]


def parse_vless(link):

    link=link.replace("vless://","")

    uuid,rest=link.split("@")

    host_port=rest.split("?")[0]

    host=host_port.split(":")[0]

    port=int(host_port.split(":")[1])

    return uuid,host,port


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


def create_config(uuid,host,port):

    config={
        "log":{"loglevel":"error"},
        "inbounds":[
            {
                "port":1080,
                "protocol":"socks",
                "settings":{"auth":"noauth"}
            }
        ],
        "outbounds":[
            {
                "protocol":"vless",
                "settings":{
                    "vnext":[
                        {
                            "address":host,
                            "port":port,
                            "users":[
                                {
                                    "id":uuid,
                                    "encryption":"none"
                                }
                            ]
                        }
                    ]
                },
                "streamSettings":{"network":"tcp"}
            }
        ]
    }

    with open("config.json","w") as f:
        json.dump(config,f)


def test_xray():

    try:

        r=requests.get(
            "https://1.1.1.1",
            proxies={
                "http":"socks5h://127.0.0.1:1080",
                "https":"socks5h://127.0.0.1:1080"
            },
            timeout=6
        )

        return r.status_code==200

    except:

        return False


def make_qr(cfg,i):

    img=qrcode.make(cfg)

    img.save(f"qr{i}.png")


configs=get_configs()

servers=[]
xray_server=None


for cfg in configs:

    if len(servers)>=3 and xray_server:
        break

    try:

        uuid,host,port=parse_vless(cfg)

        ping=tcp_ping(host,port)

        if not ping:
            continue

        if len(servers)<3:

            country,code=get_country(host)

            servers.append({

                "config":cfg,
                "ping":ping,
                "country":country,
                "flag":code.lower(),
                "ip":host,
                "start":int(time.time()),
                "type":"tcp"

            })

        if not xray_server:

            create_config(uuid,host,port)

            proc=subprocess.Popen(["./xray","run","-c","config.json"])

            time.sleep(2)

            ok=test_xray()

            proc.kill()

            if ok:

                country,code=get_country(host)

                xray_server={

                    "config":cfg,
                    "ping":ping,
                    "country":country,
                    "flag":code.lower(),
                    "ip":host,
                    "start":int(time.time()),
                    "type":"xray"

                }

    except:

        pass


if xray_server:

    servers.append(xray_server)


for i,s in enumerate(servers,1):

    make_qr(s["config"],i)


with open(STATE_FILE,"w") as f:

    json.dump({"servers":servers},f)
