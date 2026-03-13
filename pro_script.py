import requests
import json
import time
import subprocess
import qrcode
import os
import socket

URL="https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

STATE_FILE="pro_state.json"

MAX_SERVERS=80
XRAY_TEST_LIMIT=15


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


def tcp_test(host,port):

    try:
        sock=socket.create_connection((host,port),2)
        sock.close()
        return True
    except:
        return False


def get_country(ip):

    try:
        r=requests.get(f"https://ipapi.co/{ip}/country_name/",timeout=5)
        return r.text.strip()
    except:
        return "Unknown"


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


def test_vpn():

    try:

        start=time.time()

        r=requests.get(
            "https://1.1.1.1",
            proxies={
                "http":"socks5h://127.0.0.1:1080",
                "https":"socks5h://127.0.0.1:1080"
            },
            timeout=6
        )

        latency=time.time()-start

        if r.status_code==200:
            return latency

    except:
        pass

    return None


def save_state(state):

    with open(STATE_FILE,"w") as f:
        json.dump(state,f)


def make_qr(cfg,i):

    img=qrcode.make(cfg)
    img.save(f"qr{i}.png")


configs=get_configs()

alive=[]

candidates=[]

for cfg in configs:

    uuid,host,port=parse_vless(cfg)

    if tcp_test(host,port):
        candidates.append(cfg)

    if len(candidates)>=XRAY_TEST_LIMIT:
        break


for cfg in candidates:

    if len(alive)>=3:
        break

    uuid,host,port=parse_vless(cfg)

    create_config(uuid,host,port)

    proc=subprocess.Popen(["./xray","run","-c","config.json"])

    time.sleep(2)

    latency=test_vpn()

    proc.kill()

    if latency:

        alive.append({
            "config":cfg,
            "start":int(time.time()),
            "ping":latency,
            "country":get_country(host),
            "ip":host
        })


for i,s in enumerate(alive,1):
    make_qr(s["config"],i)

save_state({"servers":alive})
