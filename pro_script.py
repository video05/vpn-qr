import requests
import json
import time
import subprocess
import qrcode
import os

URL = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

STATE_FILE = "pro_state.json"


def get_configs():
    r = requests.get(URL, timeout=20)
    return [x.strip() for x in r.text.split("\n") if x.startswith("vless://")]


def parse_vless(link):

    link = link.replace("vless://", "")

    uuid, rest = link.split("@")

    host_port = rest.split("?")[0]

    host = host_port.split(":")[0]

    port = int(host_port.split(":")[1])

    return uuid, host, port


def get_country(ip):

    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        j = r.json()
        return j.get("country", "Unknown")
    except:
        return "Unknown"


def create_config(uuid, host, port):

    config = {
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
                "streamSettings":{
                    "network":"tcp"
                }
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
            timeout=8
        )

        latency=time.time()-start

        if r.status_code==200:
            return latency

    except:
        pass

    return None


def load_state():

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE) as f:
            return json.load(f)

    return {"servers":[]}


def save_state(state):

    with open(STATE_FILE,"w") as f:
        json.dump(state,f)


def make_qr(cfg,i):

    img=qrcode.make(cfg)
    img.save(f"qr{i}.png")


configs=get_configs()

state=load_state()

now=int(time.time())

alive=[]

# проверяем старые серверы

for s in state["servers"]:

    try:

        uuid,host,port=parse_vless(s["config"])

        create_config(uuid,host,port)

        proc=subprocess.Popen(["./xray","run","-c","config.json"])

        time.sleep(3)

        latency=test_vpn()

        proc.kill()

        if latency:

            s["ping"]=latency
            alive.append(s)

    except:
        pass


# ищем новые

for cfg in configs:

    if len(alive)>=3:
        break

    if any(cfg==s["config"] for s in alive):
        continue

    try:

        uuid,host,port=parse_vless(cfg)

        create_config(uuid,host,port)

        proc=subprocess.Popen(["./xray","run","-c","config.json"])

        time.sleep(3)

        latency=test_vpn()

        proc.kill()

        if latency:

            alive.append({
                "config":cfg,
                "start":now,
                "ping":latency,
                "country":get_country(host),
                "ip":host
            })

    except:
        pass


alive=alive[:3]

for i,s in enumerate(alive,1):
    make_qr(s["config"],i)

state["servers"]=alive

save_state(state)
