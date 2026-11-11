import urllib.request, json

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
        print("HTTP Status:", resp.status)
        print("Success:", res.get("success"))
        top = res["data"]["top_rankings"]
        print(f"Top suspect: {top[0]['display_name']} (@{top[0]['username']}) with {top[0]['posterior_probability_pct']}%")
        for t in top[:3]:
            print(f" - {t['display_name']}: {t['posterior_probability_pct']}%, matches: {t.get('breakdown')}")
except Exception as e:
    print("Error:", e)

