import urllib.request, json, time, threading

def poll_progress():
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:5000/api/progress") as r:
                data = json.loads(r.read())
                print(f"[POLL] {data.get('pct')}% | {data.get('stage')} | {data.get('message')}")
                if data.get("pct") == 100:
                    break
        except Exception:
            pass
        time.sleep(0.35)

t = threading.Thread(target=poll_progress)
t.start()

payload = {
    "channel_id": "1516697578107043850",
    "limit": 1000,
    "confession": "You just admitted you are scared of me😅✌️. There is a reason why no one hates me and I have supporters unlike you 🤪✌️. Ts entire situation is funny ASFUCK. Someone can't be this jealous bro holy fuck."
}

req = urllib.request.Request(
    "http://127.0.0.1:5000/api/predict",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("Prediction result received! Top suspect:", res["data"]["top_rankings"][0]["display_name"])
except Exception as e:
    print("Error:", e)

t.join()

